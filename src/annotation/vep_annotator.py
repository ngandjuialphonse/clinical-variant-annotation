"""
VEP Annotator Module
Annotates variants using Ensembl Variant Effect Predictor (VEP).
"""

import requests
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VEPAnnotation:
    """Represents VEP annotation results for a variant."""
    
    gene_symbol: Optional[str] = None
    gene_id: Optional[str] = None
    transcript_id: Optional[str] = None
    consequence: Optional[str] = None
    impact: Optional[str] = None  # HIGH, MODERATE, LOW, MODIFIER
    protein_change: Optional[str] = None
    codon_change: Optional[str] = None
    sift_prediction: Optional[str] = None
    sift_score: Optional[float] = None
    polyphen_prediction: Optional[str] = None
    polyphen_score: Optional[float] = None
    gnomad_af: Optional[float] = None
    canonical: bool = False


class VEPAnnotator:
    """
    Annotates variants using the Ensembl VEP REST API.
    
    This class provides methods to annotate variants with:
    - Gene and transcript information
    - Consequence types (missense, nonsense, etc.)
    - Protein changes
    - Functional predictions (SIFT, PolyPhen)
    - Population frequencies (gnomAD)
    
    Example:
        annotator = VEPAnnotator()
        annotations = annotator.annotate_variant("1", 12345, "A", "G")
    """
    
    # VEP REST API endpoint
    VEP_API_URL = "https://rest.ensembl.org/vep/human/region"
    
    # Consequence severity ranking (higher = more severe)
    CONSEQUENCE_SEVERITY = {
        "transcript_ablation": 100,
        "splice_acceptor_variant": 95,
        "splice_donor_variant": 95,
        "stop_gained": 90,
        "frameshift_variant": 85,
        "stop_lost": 80,
        "start_lost": 80,
        "transcript_amplification": 75,
        "inframe_insertion": 70,
        "inframe_deletion": 70,
        "missense_variant": 65,
        "protein_altering_variant": 60,
        "splice_region_variant": 55,
        "incomplete_terminal_codon_variant": 50,
        "start_retained_variant": 45,
        "stop_retained_variant": 45,
        "synonymous_variant": 40,
        "coding_sequence_variant": 35,
        "mature_miRNA_variant": 30,
        "5_prime_UTR_variant": 25,
        "3_prime_UTR_variant": 25,
        "non_coding_transcript_exon_variant": 20,
        "intron_variant": 15,
        "NMD_transcript_variant": 10,
        "non_coding_transcript_variant": 10,
        "upstream_gene_variant": 5,
        "downstream_gene_variant": 5,
        "TFBS_ablation": 5,
        "TFBS_amplification": 5,
        "TF_binding_site_variant": 5,
        "regulatory_region_ablation": 5,
        "regulatory_region_amplification": 5,
        "feature_elongation": 5,
        "regulatory_region_variant": 5,
        "feature_truncation": 5,
        "intergenic_variant": 1
    }
    
    def __init__(self, assembly: str = "GRCh38", cache_results: bool = True):
        """
        Initialize VEP annotator.
        
        Args:
            assembly: Genome assembly version (GRCh37 or GRCh38)
            cache_results: Whether to cache annotation results
        """
        self.assembly = assembly
        self.cache_results = cache_results
        self._cache: Dict[str, List[VEPAnnotation]] = {}
        self._request_count = 0
        self._last_request_time = 0
    
    def _rate_limit(self) -> None:
        """Implement rate limiting for API requests."""
        # Ensembl allows 15 requests per second
        min_interval = 1.0 / 15
        elapsed = time.time() - self._last_request_time
        
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        
        self._last_request_time = time.time()
        self._request_count += 1
    
    def _build_variant_string(self, chrom: str, pos: int, ref: str, alt: str) -> str:
        """Build VEP-compatible variant string."""
        # Remove 'chr' prefix if present
        chrom = chrom.replace('chr', '')
        
        # For SNPs: chrom:pos:pos:1/alt
        if len(ref) == 1 and len(alt) == 1:
            return f"{chrom}:{pos}:{pos}:1/{alt}"
        
        # For insertions: chrom:pos:pos:1/alt
        if len(ref) == 1 and len(alt) > 1:
            return f"{chrom}:{pos}:{pos}:1/{alt}"
        
        # For deletions: chrom:start:end:1/-
        if len(ref) > 1 and len(alt) == 1:
            end = pos + len(ref) - 1
            return f"{chrom}:{pos}:{end}:1/-"
        
        # Complex variants
        return f"{chrom}:{pos}:{pos + len(ref) - 1}:1/{alt}"
    
    def annotate_variant(
        self, 
        chrom: str, 
        pos: int, 
        ref: str, 
        alt: str
    ) -> List[VEPAnnotation]:
        """
        Annotate a single variant using VEP REST API.
        
        Args:
            chrom: Chromosome
            pos: Position
            ref: Reference allele
            alt: Alternate allele
            
        Returns:
            List of VEPAnnotation objects (one per transcript)
        """
        # Check cache first
        cache_key = f"{chrom}:{pos}:{ref}:{alt}"
        if self.cache_results and cache_key in self._cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self._cache[cache_key]
        
        # Build variant string
        variant_str = self._build_variant_string(chrom, pos, ref, alt)
        
        # Rate limit
        self._rate_limit()
        
        # Make API request
        url = f"{self.VEP_API_URL}/{variant_str}"
        headers = {"Content-Type": "application/json"}
        params = {
            "canonical": 1,
            "hgvs": 1,
            "protein": 1,
            "sift": "b",
            "polyphen": "b",
            "af": 1,
            "af_gnomad": 1
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"VEP API request failed: {e}")
            return []
        
        # Parse response
        annotations = self._parse_vep_response(data)
        
        # Cache results
        if self.cache_results:
            self._cache[cache_key] = annotations
        
        return annotations
    
    def _parse_vep_response(self, data: List[Dict]) -> List[VEPAnnotation]:
        """Parse VEP API response into VEPAnnotation objects."""
        annotations = []
        
        if not data:
            return annotations
        
        for variant_data in data:
            transcript_consequences = variant_data.get("transcript_consequences", [])
            
            for tc in transcript_consequences:
                annotation = VEPAnnotation(
                    gene_symbol=tc.get("gene_symbol"),
                    gene_id=tc.get("gene_id"),
                    transcript_id=tc.get("transcript_id"),
                    consequence=self._get_most_severe_consequence(
                        tc.get("consequence_terms", [])
                    ),
                    impact=tc.get("impact"),
                    protein_change=self._build_protein_change(tc),
                    codon_change=tc.get("codons"),
                    sift_prediction=tc.get("sift_prediction"),
                    sift_score=tc.get("sift_score"),
                    polyphen_prediction=tc.get("polyphen_prediction"),
                    polyphen_score=tc.get("polyphen_score"),
                    gnomad_af=tc.get("gnomad_af"),
                    canonical=tc.get("canonical", 0) == 1
                )
                annotations.append(annotation)
        
        return annotations
    
    def _get_most_severe_consequence(self, consequences: List[str]) -> Optional[str]:
        """Get the most severe consequence from a list."""
        if not consequences:
            return None
        
        return max(
            consequences,
            key=lambda c: self.CONSEQUENCE_SEVERITY.get(c, 0)
        )
    
    def _build_protein_change(self, tc: Dict) -> Optional[str]:
        """Build protein change string (e.g., p.Arg123Cys)."""
        amino_acids = tc.get("amino_acids")
        protein_start = tc.get("protein_start")
        
        if amino_acids and protein_start:
            if "/" in amino_acids:
                ref_aa, alt_aa = amino_acids.split("/")
                return f"p.{ref_aa}{protein_start}{alt_aa}"
        
        return tc.get("hgvsp")
    
    def annotate_variants_batch(
        self, 
        variants: List[Dict]
    ) -> Dict[str, List[VEPAnnotation]]:
        """
        Annotate multiple variants using VEP POST API.
        
        Args:
            variants: List of variant dictionaries with chrom, pos, ref, alt
            
        Returns:
            Dictionary mapping variant IDs to annotations
        """
        results = {}
        
        # VEP POST API accepts up to 200 variants per request
        batch_size = 200
        
        for i in range(0, len(variants), batch_size):
            batch = variants[i:i + batch_size]
            
            # Build request body
            variant_strings = []
            for v in batch:
                var_str = self._build_variant_string(
                    v["chrom"], v["pos"], v["ref"], v["alt"]
                )
                variant_strings.append(var_str)
            
            # Rate limit
            self._rate_limit()
            
            # Make POST request
            url = f"{self.VEP_API_URL}"
            headers = {"Content-Type": "application/json"}
            body = {"variants": variant_strings}
            
            try:
                response = requests.post(url, headers=headers, json=body, timeout=60)
                response.raise_for_status()
                data = response.json()
                
                # Parse and store results
                for j, variant_data in enumerate(data):
                    var_id = f"{batch[j]['chrom']}:{batch[j]['pos']}:{batch[j]['ref']}:{batch[j]['alt']}"
                    results[var_id] = self._parse_vep_response([variant_data])
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"VEP batch request failed: {e}")
        
        return results


if __name__ == "__main__":
    # Example usage
    annotator = VEPAnnotator()
    
    # Annotate a known pathogenic variant in BRCA1
    annotations = annotator.annotate_variant("17", 43092919, "G", "A")
    
    print("VEP Annotations:")
    print("-" * 50)
    
    for ann in annotations:
        if ann.canonical:
            print(f"Gene: {ann.gene_symbol}")
            print(f"Consequence: {ann.consequence}")
            print(f"Impact: {ann.impact}")
            print(f"Protein Change: {ann.protein_change}")
            print(f"SIFT: {ann.sift_prediction} ({ann.sift_score})")
            print(f"PolyPhen: {ann.polyphen_prediction} ({ann.polyphen_score})")
            print(f"gnomAD AF: {ann.gnomad_af}")
            break
