"""
VCF Parser Module
Parses Variant Call Format (VCF) files for annotation pipeline.
"""

import gzip
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Iterator
from pathlib import Path


@dataclass
class Variant:
    """Represents a single genetic variant."""
    
    chrom: str
    pos: int
    id: str
    ref: str
    alt: str
    qual: Optional[float] = None
    filter: str = "."
    info: Dict[str, str] = field(default_factory=dict)
    format: str = ""
    samples: Dict[str, Dict[str, str]] = field(default_factory=dict)
    
    # Annotation fields (populated later)
    gene: Optional[str] = None
    consequence: Optional[str] = None
    protein_change: Optional[str] = None
    clinical_significance: Optional[str] = None
    allele_frequency: Optional[float] = None
    
    @property
    def variant_id(self) -> str:
        """Generate a unique variant identifier."""
        return f"{self.chrom}-{self.pos}-{self.ref}-{self.alt}"
    
    @property
    def is_snp(self) -> bool:
        """Check if variant is a single nucleotide polymorphism."""
        return len(self.ref) == 1 and len(self.alt) == 1
    
    @property
    def is_indel(self) -> bool:
        """Check if variant is an insertion or deletion."""
        return len(self.ref) != len(self.alt)
    
    def to_dict(self) -> Dict:
        """Convert variant to dictionary for JSON serialization."""
        return {
            "chrom": self.chrom,
            "pos": self.pos,
            "ref": self.ref,
            "alt": self.alt,
            "gene": self.gene,
            "consequence": self.consequence,
            "protein_change": self.protein_change,
            "clinical_significance": self.clinical_significance,
            "allele_frequency": self.allele_frequency
        }


class VCFParser:
    """
    Parser for VCF (Variant Call Format) files.
    
    Supports both uncompressed (.vcf) and gzip-compressed (.vcf.gz) files.
    
    Example:
        parser = VCFParser("sample.vcf.gz")
        for variant in parser.parse():
            print(f"{variant.chrom}:{variant.pos} {variant.ref}>{variant.alt}")
    """
    
    def __init__(self, vcf_path: str):
        """
        Initialize VCF parser.
        
        Args:
            vcf_path: Path to VCF file (.vcf or .vcf.gz)
        """
        self.vcf_path = Path(vcf_path)
        self.header_lines: List[str] = []
        self.sample_names: List[str] = []
        self._validate_file()
    
    def _validate_file(self) -> None:
        """Validate that the VCF file exists and is readable."""
        if not self.vcf_path.exists():
            raise FileNotFoundError(f"VCF file not found: {self.vcf_path}")
        
        if not self.vcf_path.suffix in ['.vcf', '.gz']:
            raise ValueError(f"Invalid file extension: {self.vcf_path.suffix}")
    
    def _open_file(self):
        """Open VCF file, handling gzip compression if needed."""
        if self.vcf_path.suffix == '.gz':
            return gzip.open(self.vcf_path, 'rt')
        return open(self.vcf_path, 'r')
    
    def _parse_info_field(self, info_str: str) -> Dict[str, str]:
        """Parse the INFO field into a dictionary."""
        if info_str == '.':
            return {}
        
        info_dict = {}
        for item in info_str.split(';'):
            if '=' in item:
                key, value = item.split('=', 1)
                info_dict[key] = value
            else:
                info_dict[item] = 'True'
        
        return info_dict
    
    def _parse_sample_data(self, format_str: str, sample_str: str) -> Dict[str, str]:
        """Parse sample genotype data."""
        if format_str == '.' or sample_str == '.':
            return {}
        
        keys = format_str.split(':')
        values = sample_str.split(':')
        
        return dict(zip(keys, values))
    
    def parse(self) -> Iterator[Variant]:
        """
        Parse VCF file and yield Variant objects.
        
        Yields:
            Variant objects for each record in the VCF file.
        """
        with self._open_file() as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Store header lines
                if line.startswith('##'):
                    self.header_lines.append(line)
                    continue
                
                # Parse column header line
                if line.startswith('#CHROM'):
                    columns = line[1:].split('\t')
                    if len(columns) > 9:
                        self.sample_names = columns[9:]
                    continue
                
                # Parse variant record
                fields = line.split('\t')
                
                if len(fields) < 8:
                    continue
                
                # Parse quality score
                qual = None
                if fields[5] != '.':
                    try:
                        qual = float(fields[5])
                    except ValueError:
                        pass
                
                # Handle multiple alternate alleles
                alts = fields[4].split(',')
                
                for alt in alts:
                    variant = Variant(
                        chrom=fields[0],
                        pos=int(fields[1]),
                        id=fields[2],
                        ref=fields[3],
                        alt=alt,
                        qual=qual,
                        filter=fields[6],
                        info=self._parse_info_field(fields[7])
                    )
                    
                    # Parse sample data if present
                    if len(fields) > 9:
                        variant.format = fields[8]
                        for i, sample_name in enumerate(self.sample_names):
                            if i + 9 < len(fields):
                                variant.samples[sample_name] = self._parse_sample_data(
                                    fields[8], fields[i + 9]
                                )
                    
                    yield variant
    
    def get_variant_count(self) -> int:
        """Count total number of variants in the VCF file."""
        return sum(1 for _ in self.parse())
    
    def get_variants_list(self) -> List[Variant]:
        """Parse all variants and return as a list."""
        return list(self.parse())


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python vcf_parser.py <vcf_file>")
        sys.exit(1)
    
    parser = VCFParser(sys.argv[1])
    
    print(f"Parsing: {sys.argv[1]}")
    print("-" * 50)
    
    for i, variant in enumerate(parser.parse()):
        if i >= 10:  # Print first 10 variants
            print(f"... and more variants")
            break
        print(f"{variant.chrom}:{variant.pos} {variant.ref}>{variant.alt}")
    
    print("-" * 50)
    print(f"Total variants: {parser.get_variant_count()}")
