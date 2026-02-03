"""
Frequency Filter Module
Filters variants based on population allele frequencies.
"""

from typing import List, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FrequencyThresholds:
    """Configurable frequency thresholds for variant filtering."""
    
    # Maximum allele frequency for rare disease variants
    max_af_dominant: float = 0.0001  # 0.01% for dominant conditions
    max_af_recessive: float = 0.01   # 1% for recessive conditions
    max_af_general: float = 0.01     # Default 1% threshold
    
    # Population-specific thresholds
    max_af_gnomad: float = 0.01
    max_af_gnomad_popmax: float = 0.01  # Maximum across populations


class FrequencyFilter:
    """
    Filters variants based on population allele frequencies.
    
    In clinical genomics, common variants are typically filtered out
    because they are unlikely to cause rare Mendelian diseases.
    
    The rationale:
    - If a variant is common in the population, it's unlikely to cause
      a rare disease (otherwise the disease wouldn't be rare)
    - Different thresholds apply for dominant vs. recessive conditions
    
    Example:
        filter = FrequencyFilter(max_af=0.01)
        rare_variants = filter.filter_variants(variants)
    """
    
    def __init__(
        self, 
        max_af: float = 0.01,
        thresholds: Optional[FrequencyThresholds] = None
    ):
        """
        Initialize frequency filter.
        
        Args:
            max_af: Maximum allele frequency threshold (default 1%)
            thresholds: Custom threshold configuration
        """
        self.max_af = max_af
        self.thresholds = thresholds or FrequencyThresholds()
    
    def filter_variants(
        self, 
        variants: List,
        inheritance_mode: str = "general"
    ) -> List:
        """
        Filter variants by allele frequency.
        
        Args:
            variants: List of Variant objects with allele_frequency attribute
            inheritance_mode: "dominant", "recessive", or "general"
            
        Returns:
            List of variants passing the frequency filter
        """
        # Select appropriate threshold
        if inheritance_mode == "dominant":
            threshold = self.thresholds.max_af_dominant
        elif inheritance_mode == "recessive":
            threshold = self.thresholds.max_af_recessive
        else:
            threshold = self.max_af
        
        filtered = []
        
        for variant in variants:
            af = getattr(variant, 'allele_frequency', None)
            
            # Keep variant if:
            # 1. No frequency data available (novel variant)
            # 2. Frequency is below threshold
            if af is None or af <= threshold:
                filtered.append(variant)
            else:
                logger.debug(
                    f"Filtered out {variant.variant_id}: AF={af} > {threshold}"
                )
        
        logger.info(
            f"Frequency filter: {len(filtered)}/{len(variants)} variants passed "
            f"(threshold: {threshold})"
        )
        
        return filtered
    
    def apply_gnomad_filter(
        self, 
        variants: List,
        use_popmax: bool = True
    ) -> List:
        """
        Filter variants using gnomAD allele frequencies.
        
        Args:
            variants: List of Variant objects
            use_popmax: Use maximum frequency across populations
            
        Returns:
            List of variants passing the gnomAD filter
        """
        threshold = (
            self.thresholds.max_af_gnomad_popmax 
            if use_popmax 
            else self.thresholds.max_af_gnomad
        )
        
        filtered = []
        
        for variant in variants:
            # Check gnomAD frequency from VEP annotation
            gnomad_af = getattr(variant, 'gnomad_af', None)
            
            if gnomad_af is None or gnomad_af <= threshold:
                filtered.append(variant)
        
        return filtered
    
    @staticmethod
    def calculate_carrier_frequency(allele_frequency: float) -> float:
        """
        Calculate carrier frequency for recessive conditions.
        
        For a recessive condition, the carrier frequency is approximately
        2 * sqrt(disease_frequency) using Hardy-Weinberg equilibrium.
        
        Args:
            allele_frequency: Population allele frequency
            
        Returns:
            Estimated carrier frequency
        """
        # Carrier frequency ≈ 2pq where p is disease allele frequency
        # and q ≈ 1 for rare alleles
        return 2 * allele_frequency
    
    @staticmethod
    def is_too_common_for_disease(
        allele_frequency: float,
        disease_prevalence: float,
        inheritance: str = "dominant"
    ) -> bool:
        """
        Check if variant is too common to cause a disease.
        
        Uses the maximum credible allele frequency framework.
        
        Args:
            allele_frequency: Observed allele frequency
            disease_prevalence: Disease prevalence in population
            inheritance: "dominant" or "recessive"
            
        Returns:
            True if variant is too common to cause the disease
        """
        if inheritance == "dominant":
            # For dominant: AF should be ≤ prevalence / penetrance
            # Assuming 50% penetrance as conservative estimate
            max_credible_af = disease_prevalence / 0.5
        else:
            # For recessive: AF should be ≤ sqrt(prevalence)
            max_credible_af = disease_prevalence ** 0.5
        
        return allele_frequency > max_credible_af


class QualityFilter:
    """
    Filters variants based on quality metrics.
    """
    
    def __init__(
        self,
        min_qual: float = 30,
        min_depth: int = 10,
        min_gq: int = 20
    ):
        """
        Initialize quality filter.
        
        Args:
            min_qual: Minimum variant quality score
            min_depth: Minimum read depth
            min_gq: Minimum genotype quality
        """
        self.min_qual = min_qual
        self.min_depth = min_depth
        self.min_gq = min_gq
    
    def filter_variants(self, variants: List) -> List:
        """
        Filter variants by quality metrics.
        
        Args:
            variants: List of Variant objects
            
        Returns:
            List of variants passing quality filters
        """
        filtered = []
        
        for variant in variants:
            # Check variant quality
            if variant.qual is not None and variant.qual < self.min_qual:
                continue
            
            # Check depth (from INFO or sample data)
            depth = variant.info.get('DP')
            if depth and int(depth) < self.min_depth:
                continue
            
            filtered.append(variant)
        
        logger.info(
            f"Quality filter: {len(filtered)}/{len(variants)} variants passed"
        )
        
        return filtered


if __name__ == "__main__":
    # Example usage
    from dataclasses import dataclass
    
    @dataclass
    class MockVariant:
        variant_id: str
        allele_frequency: Optional[float]
    
    # Create test variants
    variants = [
        MockVariant("chr1:100:A:G", 0.001),   # Rare - should pass
        MockVariant("chr1:200:C:T", 0.05),    # Common - should fail
        MockVariant("chr1:300:G:A", None),    # Novel - should pass
        MockVariant("chr1:400:T:C", 0.0001),  # Very rare - should pass
    ]
    
    # Apply filter
    filter = FrequencyFilter(max_af=0.01)
    passed = filter.filter_variants(variants)
    
    print("Frequency Filter Results:")
    print("-" * 50)
    print(f"Input variants: {len(variants)}")
    print(f"Passed filter: {len(passed)}")
    print("\nPassed variants:")
    for v in passed:
        print(f"  {v.variant_id}: AF={v.allele_frequency}")
