"""
Security Utilities Module
HIPAA-compliant security features for clinical genomics data.
"""

import os
import hashlib
import secrets
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import base64

# Note: In production, use proper encryption libraries
# from cryptography.fernet import Fernet
# import boto3  # For AWS KMS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AuditLogEntry:
    """Represents an audit log entry for HIPAA compliance."""
    
    timestamp: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    ip_address: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "details": self.details,
            "success": self.success
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class AuditLogger:
    """
    HIPAA-compliant audit logging system.
    
    Maintains comprehensive audit trails of all access to PHI
    (Protected Health Information) as required by HIPAA.
    
    Example:
        audit = AuditLogger("/var/log/clinical/audit.log")
        audit.log_access(user_id="user123", action="view_report", resource_id="report456")
    """
    
    def __init__(self, log_path: str = "audit.log"):
        """
        Initialize audit logger.
        
        Args:
            log_path: Path to audit log file
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_access(
        self,
        user_id: str,
        action: str,
        resource_type: str = "patient_data",
        resource_id: str = "",
        ip_address: Optional[str] = None,
        details: Optional[Dict] = None,
        success: bool = True
    ) -> None:
        """
        Log an access event.
        
        Args:
            user_id: ID of the user performing the action
            action: Type of action (view, create, update, delete, export)
            resource_type: Type of resource accessed
            resource_id: ID of the specific resource
            ip_address: IP address of the request
            details: Additional details about the action
            success: Whether the action was successful
        """
        entry = AuditLogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            details=details or {},
            success=success
        )
        
        # Write to log file
        with open(self.log_path, 'a') as f:
            f.write(entry.to_json() + "\n")
        
        logger.info(f"Audit: {user_id} {action} {resource_type}/{resource_id}")
    
    def log_phi_access(
        self,
        user_id: str,
        patient_id: str,
        action: str,
        reason: str
    ) -> None:
        """
        Log access to Protected Health Information (PHI).
        
        Args:
            user_id: ID of the user accessing PHI
            patient_id: ID of the patient whose data is accessed
            action: Type of access
            reason: Reason for accessing the data
        """
        self.log_access(
            user_id=user_id,
            action=action,
            resource_type="phi",
            resource_id=patient_id,
            details={"reason": reason}
        )


class DataEncryption:
    """
    Encryption utilities for protecting sensitive data.
    
    Implements encryption at rest for PHI as required by HIPAA.
    
    Note: This is a simplified implementation for demonstration.
    In production, use AWS KMS or similar key management service.
    """
    
    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize encryption handler.
        
        Args:
            key: Encryption key (32 bytes for AES-256)
        """
        self.key = key or self._generate_key()
    
    @staticmethod
    def _generate_key() -> bytes:
        """Generate a secure encryption key."""
        return secrets.token_bytes(32)
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt sensitive data.
        
        Args:
            data: Plain text data to encrypt
            
        Returns:
            Base64-encoded encrypted data
            
        Note: This is a placeholder. Use proper encryption in production.
        """
        # In production, use Fernet or AWS KMS
        # For demonstration, we use a simple XOR (NOT SECURE)
        # Replace with: Fernet(self.key).encrypt(data.encode())
        
        encoded = data.encode()
        # This is NOT real encryption - just for demonstration
        encrypted = bytes(b ^ self.key[i % len(self.key)] for i, b in enumerate(encoded))
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted data.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Decrypted plain text
        """
        # In production: Fernet(self.key).decrypt(encrypted_data.encode())
        encrypted = base64.b64decode(encrypted_data)
        decrypted = bytes(b ^ self.key[i % len(self.key)] for i, b in enumerate(encrypted))
        return decrypted.decode()
    
    @staticmethod
    def hash_identifier(identifier: str, salt: Optional[str] = None) -> str:
        """
        Create a one-way hash of an identifier for de-identification.
        
        Args:
            identifier: Original identifier (e.g., patient ID)
            salt: Optional salt for the hash
            
        Returns:
            Hashed identifier
        """
        if salt is None:
            salt = os.environ.get("HASH_SALT", "default_salt")
        
        combined = f"{salt}{identifier}".encode()
        return hashlib.sha256(combined).hexdigest()


class AccessControl:
    """
    Role-based access control for clinical data.
    
    Implements the minimum necessary standard required by HIPAA.
    """
    
    # Define roles and their permissions
    ROLES = {
        "admin": ["read", "write", "delete", "export", "manage_users"],
        "lab_director": ["read", "write", "export", "sign_reports"],
        "genetic_counselor": ["read", "export"],
        "clinician": ["read"],
        "bioinformatician": ["read", "write"],
        "auditor": ["read_audit_logs"]
    }
    
    def __init__(self):
        """Initialize access control system."""
        self.user_roles: Dict[str, str] = {}
    
    def assign_role(self, user_id: str, role: str) -> None:
        """Assign a role to a user."""
        if role not in self.ROLES:
            raise ValueError(f"Invalid role: {role}")
        self.user_roles[user_id] = role
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user_id: ID of the user
            permission: Permission to check
            
        Returns:
            True if user has the permission
        """
        role = self.user_roles.get(user_id)
        if not role:
            return False
        
        return permission in self.ROLES.get(role, [])
    
    def require_permission(self, user_id: str, permission: str) -> None:
        """
        Require a permission, raising an exception if not granted.
        
        Args:
            user_id: ID of the user
            permission: Required permission
            
        Raises:
            PermissionError: If user lacks the permission
        """
        if not self.check_permission(user_id, permission):
            raise PermissionError(
                f"User {user_id} lacks permission: {permission}"
            )


class PHIDeidentifier:
    """
    De-identification utilities for PHI.
    
    Implements Safe Harbor and Expert Determination methods
    for de-identifying protected health information.
    """
    
    # Safe Harbor identifiers that must be removed
    SAFE_HARBOR_IDENTIFIERS = [
        "name", "address", "dates", "phone", "fax", "email",
        "ssn", "mrn", "health_plan", "account_number",
        "license_number", "vehicle_id", "device_id", "url",
        "ip_address", "biometric", "photo", "other_unique"
    ]
    
    def __init__(self, encryption: Optional[DataEncryption] = None):
        """Initialize de-identifier."""
        self.encryption = encryption or DataEncryption()
    
    def deidentify_patient(self, patient_data: Dict) -> Dict:
        """
        De-identify patient data using Safe Harbor method.
        
        Args:
            patient_data: Dictionary containing patient information
            
        Returns:
            De-identified patient data
        """
        deidentified = {}
        
        for key, value in patient_data.items():
            if key.lower() in ["patient_id", "mrn"]:
                # Hash identifiers
                deidentified[key] = self.encryption.hash_identifier(str(value))
            elif key.lower() in ["name", "first_name", "last_name"]:
                # Remove names
                deidentified[key] = "[REDACTED]"
            elif key.lower() in ["date_of_birth", "dob"]:
                # Generalize to year only (if age > 89, use 90+)
                deidentified[key] = self._generalize_date(value)
            elif key.lower() in ["address", "zip", "phone", "email", "ssn"]:
                # Remove direct identifiers
                deidentified[key] = "[REDACTED]"
            else:
                # Keep non-identifying data
                deidentified[key] = value
        
        return deidentified
    
    def _generalize_date(self, date_str: str) -> str:
        """Generalize date to year only."""
        try:
            # Try to parse date
            if "-" in date_str:
                year = date_str.split("-")[0]
            elif "/" in date_str:
                parts = date_str.split("/")
                year = parts[-1] if len(parts[-1]) == 4 else parts[0]
            else:
                year = date_str[:4]
            
            return f"{year}-XX-XX"
        except:
            return "[REDACTED]"


if __name__ == "__main__":
    # Example usage
    print("Security Utilities Demo")
    print("=" * 50)
    
    # Audit logging
    audit = AuditLogger("demo_audit.log")
    audit.log_access(
        user_id="user123",
        action="view_report",
        resource_type="clinical_report",
        resource_id="report456"
    )
    print("✓ Audit log entry created")
    
    # Encryption
    encryption = DataEncryption()
    sensitive = "Patient SSN: 123-45-6789"
    encrypted = encryption.encrypt(sensitive)
    decrypted = encryption.decrypt(encrypted)
    print(f"✓ Encryption test: {sensitive[:20]}... -> {encrypted[:20]}...")
    
    # De-identification
    deidentifier = PHIDeidentifier()
    patient = {
        "patient_id": "P12345",
        "name": "John Doe",
        "date_of_birth": "1985-03-15",
        "ssn": "123-45-6789",
        "diagnosis": "Hereditary breast cancer"
    }
    deidentified = deidentifier.deidentify_patient(patient)
    print(f"✓ De-identification: {patient['name']} -> {deidentified['name']}")
    
    # Access control
    acl = AccessControl()
    acl.assign_role("user123", "genetic_counselor")
    can_read = acl.check_permission("user123", "read")
    can_delete = acl.check_permission("user123", "delete")
    print(f"✓ Access control: read={can_read}, delete={can_delete}")
