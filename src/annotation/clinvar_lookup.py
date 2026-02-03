"""
ClinVar Lookup Module
Retrieves clinical significance information from ClinVar database.
"""

import requests
import time
from typing import Optional, Dict, List
from dataclasses import dataclass
import logging
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ClinVarRecord:
    """Represents a ClinVar record for a variant."""
    
    variation_id: Optional[str] = None
    clinical_significance: Optional[str] = None
    review_status: Optional[str] = None
    condition: Optional[str] = None
    last_evaluated: Optional[str] = None
    submitter_count: int = 0
    star_rating: int = 0
    
    @property
    def is_pathogenic(self) -> bool:
        """Check if variant is classified as pathogenic."""
        if self.clinical_significance:
            return "pathogenic" in self.clinical_significance.lower()
        return False
    
    @property
    def is_benign(self) -> bool:
        """Check if variant is classified as benign."""
        if self.clinical_significance:
            return "benign" in self.clinical_significance.lower()
        return False
    
    @property
    def is_vus(self) -> bool:
        """Check if variant is a VUS."""
        if self.clinical_significance:
            return "uncertain" in self.clinical_significance.lower()
        return False


class ClinVarClient:
    """
    Client for querying the ClinVar database.
    
    ClinVar is a public archive of reports of the relationships
    among human variations and phenotypes, with supporting evidence.
    
    Example:
        client = ClinVarClient()
        record = client.lookup_variant("1", 12345, "A", "G")
        print(record.clinical_significance)
    """
    
    # NCBI E-utilities endpoints
    ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    
    # Review status to star rating mapping
    REVIEW_STATUS_STARS = {
        "practice guideline": 4,
        "reviewed by expert panel": 3,
        "criteria provided, multiple submitters, no conflicts": 2,
        "criteria provided, conflicting interpretations": 1,
        "criteria provided, single submitter": 1,
        "no assertion criteria provided": 0,
        "no assertion provided": 0
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ClinVar client.
        
        Args:
            api_key: Optional NCBI API key for higher rate limits
        """
        self.api_key = api_key
        self._last_request_time = 0
        self._cache: Dict[str, ClinVarRecord] = {}
    
    def _rate_limit(self) -> None:
        """Implement rate limiting for NCBI requests."""
        # Without API key: 3 requests per second
        # With API key: 10 requests per second
        min_interval = 0.1 if self.api_key else 0.34
        elapsed = time.time() - self._last_request_time
        
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        
        self._last_request_time = time.time()
    
    def _build_variant_query(self, chrom: str, pos: int, ref: str, alt: str) -> str:
        """Build ClinVar search query for a variant."""
        # Remove 'chr' prefix if present
        chrom = chrom.replace('chr', '')
        
        # Build HGVS-like notation for search
        # ClinVar accepts various query formats
        queries = [
            f"{chrom}[chr] AND {pos}[chrpos38]",
            f"{chrom}:{pos} {ref}>{alt}",
        ]
        
        return queries[0]
    
    def lookup_variant(
        self, 
        chrom: str, 
        pos: int, 
        ref: str, 
        alt: str
    ) -> Optional[ClinVarRecord]:
        """
        Look up a variant in ClinVar.
        
        Args:
            chrom: Chromosome
            pos: Position (GRCh38)
            ref: Reference allele
            alt: Alternate allele
            
        Returns:
            ClinVarRecord if found, None otherwise
        """
        # Check cache
        cache_key = f"{chrom}:{pos}:{ref}:{alt}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Search ClinVar
        query = self._build_variant_query(chrom, pos, ref, alt)
        
        self._rate_limit()
        
        # Step 1: Search for variant
        search_params = {
            "db": "clinvar",
            "term": query,
            "retmode": "json",
            "retmax": 10
        }
        if self.api_key:
            search_params["api_key"] = self.api_key
        
        try:
            response = requests.get(self.ESEARCH_URL, params=search_params, timeout=30)
            response.raise_for_status()
            search_data = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"ClinVar search failed: {e}")
            return None
        
        # Get IDs from search results
        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        
        if not id_list:
            logger.debug(f"No ClinVar records found for {cache_key}")
            return None
        
        # Step 2: Get summary for first result
        self._rate_limit()
        
        summary_params = {
            "db": "clinvar",
            "id": id_list[0],
            "retmode": "json"
        }
        if self.api_key:
            summary_params["api_key"] = self.api_key
        
        try:
            response = requests.get(self.ESUMMARY_URL, params=summary_params, timeout=30)
            response.raise_for_status()
            summary_data = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"ClinVar summary failed: {e}")
            return None
        
        # Parse summary
        record = self._parse_summary(summary_data, id_list[0])
        
        # Cache result
        self._cache[cache_key] = record
        
        return record
    
    def _parse_summary(self, data: Dict, variant_id: str) -> ClinVarRecord:
        """Parse ClinVar summary response."""
        result = data.get("result", {})
        uid_data = result.get(variant_id, {})
        
        clinical_significance = uid_data.get("clinical_significance", {})
        if isinstance(clinical_significance, dict):
            clin_sig = clinical_significance.get("description", "")
        else:
            clin_sig = str(clinical_significance)
        
        review_status = uid_data.get("review_status", "")
        
        record = ClinVarRecord(
            variation_id=variant_id,
            clinical_significance=clin_sig,
            review_status=review_status,
            condition=uid_data.get("trait_set", [{}])[0].get("trait_name", "") if uid_data.get("trait_set") else "",
            last_evaluated=uid_data.get("last_evaluated", ""),
            submitter_count=len(uid_data.get("supporting_submissions", {}).get("scv", [])),
            star_rating=self._get_star_rating(review_status)
        )
        
        return record
    
    def _get_star_rating(self, review_status: str) -> int:
        """Convert review status to star rating."""
        review_status_lower = review_status.lower()
        
        for status, stars in self.REVIEW_STATUS_STARS.items():
            if status in review_status_lower:
                return stars
        
        return 0
    
    def lookup_variants_batch(
        self, 
        variants: List[Dict]
    ) -> Dict[str, Optional[ClinVarRecord]]:
        """
        Look up multiple variants in ClinVar.
        
        Args:
            variants: List of variant dictionaries
            
        Returns:
            Dictionary mapping variant IDs to ClinVarRecords
        """
        results = {}
        
        for v in variants:
            var_id = f"{v['chrom']}:{v['pos']}:{v['ref']}:{v['alt']}"
            results[var_id] = self.lookup_variant(
                v["chrom"], v["pos"], v["ref"], v["alt"]
            )
        
        return results


# Clinical significance classification helper
def classify_variant(
    clinvar_record: Optional[ClinVarRecord],
    gnomad_af: Optional[float] = None,
    consequence: Optional[str] = None
) -> str:
    """
    Classify variant based on available evidence.
    
    This is a simplified classification. In production, you would
    implement full ACMG criteria.
    
    Args:
        clinvar_record: ClinVar lookup result
        gnomad_af: gnomAD allele frequency
        consequence: VEP consequence type
        
    Returns:
        Classification string
    """
    # If ClinVar has a classification, use it
    if clinvar_record and clinvar_record.clinical_significance:
        return clinvar_record.clinical_significance
    
    # Apply simple rules if no ClinVar data
    
    # BA1: Allele frequency >5% suggests benign
    if gnomad_af and gnomad_af > 0.05:
        return "Likely Benign (BA1: AF > 5%)"
    
    # BS1: Allele frequency >1% suggests benign for rare disease
    if gnomad_af and gnomad_af > 0.01:
        return "Likely Benign (BS1: AF > 1%)"
    
    # PVS1: Null variants in genes where LOF is a mechanism
    if consequence in ["stop_gained", "frameshift_variant", "splice_acceptor_variant", "splice_donor_variant"]:
        return "Uncertain Significance (potential LOF)"
    
    return "Uncertain Significance"


if __name__ == "__main__":
    # Example usage
    client = ClinVarClient()
    
    # Look up a known pathogenic BRCA1 variant
    record = client.lookup_variant("17", 43092919, "G", "A")
    
    if record:
        print("ClinVar Record:")
        print("-" * 50)
        print(f"Variation ID: {record.variation_id}")
        print(f"Clinical Significance: {record.clinical_significance}")
        print(f"Review Status: {record.review_status}")
        print(f"Star Rating: {'★' * record.star_rating}")
        print(f"Condition: {record.condition}")
        print(f"Is Pathogenic: {record.is_pathogenic}")
    else:
        print("No ClinVar record found")
