# HIPAA Compliance Documentation

This document outlines the HIPAA compliance measures implemented in the Clinical Variant Annotation Pipeline.

## Overview

The Health Insurance Portability and Accountability Act (HIPAA) establishes national standards for the protection of health information. This pipeline handles Protected Health Information (PHI) and implements the following safeguards.

## Administrative Safeguards

### Access Management

| Control | Implementation |
|---------|----------------|
| **Role-Based Access** | Users are assigned roles (admin, lab_director, genetic_counselor, clinician) with specific permissions |
| **Minimum Necessary** | Each role has only the permissions required for their job function |
| **User Authentication** | Integration with enterprise identity providers (SAML, OIDC) |

### Audit Controls

All access to PHI is logged with:
- Timestamp (UTC)
- User identifier
- Action performed
- Resource accessed
- IP address
- Success/failure status

Audit logs are:
- Immutable (append-only)
- Retained for 6 years (HIPAA requirement)
- Regularly reviewed

## Technical Safeguards

### Encryption

| Data State | Method | Standard |
|------------|--------|----------|
| **At Rest** | AES-256 | FIPS 140-2 compliant |
| **In Transit** | TLS 1.3 | Certificate-based |
| **Key Management** | AWS KMS | Hardware security modules |

### Access Controls

```python
# Example: Checking permissions before accessing PHI
from src.utils.security import AccessControl

acl = AccessControl()
acl.require_permission(user_id, "read")  # Raises PermissionError if denied
```

### De-identification

The pipeline supports Safe Harbor de-identification by removing or generalizing:

1. Names
2. Geographic data smaller than state
3. Dates (except year)
4. Phone/fax numbers
5. Email addresses
6. Social Security numbers
7. Medical record numbers
8. Health plan numbers
9. Account numbers
10. Certificate/license numbers
11. Vehicle identifiers
12. Device identifiers
13. Web URLs
14. IP addresses
15. Biometric identifiers
16. Full-face photographs
17. Any other unique identifying number

## Physical Safeguards

### AWS Infrastructure

When deployed on AWS, the pipeline uses:

| Service | Purpose | Compliance |
|---------|---------|------------|
| **AWS GovCloud** | HIPAA-eligible region | FedRAMP High |
| **Amazon S3** | Encrypted storage | SSE-KMS |
| **Amazon VPC** | Network isolation | Private subnets |
| **AWS CloudTrail** | API logging | Tamper-proof |

### Data Center Security

AWS data centers provide:
- 24/7 physical security
- Biometric access controls
- Video surveillance
- Environmental controls

## Breach Notification

In the event of a breach:

1. **Detection**: Automated monitoring for unauthorized access
2. **Assessment**: Determine scope and affected individuals
3. **Notification**: Within 60 days to affected individuals and HHS
4. **Documentation**: Record incident details and response

## Business Associate Agreements

This pipeline requires BAAs with:
- Cloud providers (AWS, GCP, Azure)
- Third-party API providers (if applicable)
- Subcontractors with PHI access

## Implementation Checklist

### Before Deployment

- [ ] Sign BAA with cloud provider
- [ ] Configure encryption at rest
- [ ] Enable TLS for all connections
- [ ] Set up audit logging
- [ ] Configure access controls
- [ ] Train workforce on HIPAA

### Ongoing Compliance

- [ ] Regular security assessments
- [ ] Annual risk analysis
- [ ] Audit log reviews
- [ ] Access reviews
- [ ] Incident response testing
- [ ] Policy updates

## Code Examples

### Audit Logging

```python
from src.utils.security import AuditLogger

audit = AuditLogger("/var/log/clinical/audit.log")

# Log PHI access
audit.log_phi_access(
    user_id="user123",
    patient_id="patient456",
    action="view_report",
    reason="Clinical review"
)
```

### Data Encryption

```python
from src.utils.security import DataEncryption

encryption = DataEncryption()

# Encrypt sensitive data before storage
encrypted = encryption.encrypt(patient_data)

# Decrypt when needed
decrypted = encryption.decrypt(encrypted)
```

### De-identification

```python
from src.utils.security import PHIDeidentifier

deidentifier = PHIDeidentifier()

# De-identify patient data for research
safe_data = deidentifier.deidentify_patient(patient_record)
```

## References

1. [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
2. [HIPAA Privacy Rule](https://www.hhs.gov/hipaa/for-professionals/privacy/index.html)
3. [AWS HIPAA Compliance](https://aws.amazon.com/compliance/hipaa-compliance/)
4. [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## Disclaimer

This documentation is for educational purposes. Consult with a HIPAA compliance officer and legal counsel before handling real PHI.
