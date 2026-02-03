"""
Clinical Report Generator Module
Generates clinical genomics reports from annotated variants.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PatientInfo:
    """Patient demographic information for the report."""
    
    patient_id: str
    first_name: str = ""
    last_name: str = ""
    date_of_birth: str = ""
    sex: str = ""
    mrn: str = ""  # Medical Record Number
    ordering_physician: str = ""
    indication: str = ""  # Reason for testing
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


@dataclass
class TestInfo:
    """Information about the genomic test performed."""
    
    test_name: str = "Whole Exome Sequencing"
    test_code: str = ""
    accession_number: str = ""
    sample_type: str = "Blood"
    collection_date: str = ""
    received_date: str = ""
    report_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    lab_name: str = "Clinical Genomics Laboratory"
    lab_director: str = ""
    clia_number: str = ""


@dataclass
class ReportedVariant:
    """A variant to be included in the clinical report."""
    
    gene: str
    variant: str  # HGVS notation
    protein_change: str
    zygosity: str  # Heterozygous, Homozygous
    classification: str  # Pathogenic, Likely Pathogenic, VUS, etc.
    condition: str  # Associated disease/phenotype
    inheritance: str  # AD, AR, XL, etc.
    evidence: List[str] = field(default_factory=list)
    acmg_criteria: List[str] = field(default_factory=list)
    
    @property
    def is_reportable(self) -> bool:
        """Check if variant should be reported based on classification."""
        reportable = ["pathogenic", "likely pathogenic", "uncertain significance"]
        return any(r in self.classification.lower() for r in reportable)


class ClinicalReportGenerator:
    """
    Generates clinical genomics reports.
    
    This class creates professional clinical reports from annotated
    variant data, following clinical laboratory reporting standards.
    
    Example:
        generator = ClinicalReportGenerator()
        report = generator.generate_report(
            variants=annotated_variants,
            patient=patient_info,
            test=test_info
        )
        report.save_html("report.html")
    """
    
    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize report generator.
        
        Args:
            template_dir: Directory containing report templates
        """
        self.template_dir = template_dir or Path(__file__).parent.parent.parent / "templates"
    
    def generate_report(
        self,
        variants: List[ReportedVariant],
        patient: PatientInfo,
        test: TestInfo,
        include_vus: bool = True
    ) -> 'ClinicalReport':
        """
        Generate a clinical report from annotated variants.
        
        Args:
            variants: List of annotated variants
            patient: Patient information
            test: Test information
            include_vus: Whether to include VUS in the report
            
        Returns:
            ClinicalReport object
        """
        # Filter variants for reporting
        reportable_variants = [v for v in variants if v.is_reportable]
        
        if not include_vus:
            reportable_variants = [
                v for v in reportable_variants 
                if "uncertain" not in v.classification.lower()
            ]
        
        # Categorize variants
        pathogenic = [
            v for v in reportable_variants 
            if "pathogenic" in v.classification.lower() 
            and "likely" not in v.classification.lower()
        ]
        likely_pathogenic = [
            v for v in reportable_variants 
            if "likely pathogenic" in v.classification.lower()
        ]
        vus = [
            v for v in reportable_variants 
            if "uncertain" in v.classification.lower()
        ]
        
        # Generate interpretation
        interpretation = self._generate_interpretation(
            pathogenic, likely_pathogenic, vus, patient.indication
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            pathogenic, likely_pathogenic, vus
        )
        
        return ClinicalReport(
            patient=patient,
            test=test,
            pathogenic_variants=pathogenic,
            likely_pathogenic_variants=likely_pathogenic,
            vus_variants=vus,
            interpretation=interpretation,
            recommendations=recommendations,
            generated_at=datetime.now()
        )
    
    def _generate_interpretation(
        self,
        pathogenic: List[ReportedVariant],
        likely_pathogenic: List[ReportedVariant],
        vus: List[ReportedVariant],
        indication: str
    ) -> str:
        """Generate clinical interpretation text."""
        
        if pathogenic or likely_pathogenic:
            significant = pathogenic + likely_pathogenic
            genes = ", ".join(set(v.gene for v in significant))
            conditions = ", ".join(set(v.condition for v in significant if v.condition))
            
            interpretation = (
                f"This analysis identified {len(significant)} clinically significant "
                f"variant(s) in the following gene(s): {genes}. "
            )
            
            if conditions:
                interpretation += f"These variants are associated with: {conditions}. "
            
            interpretation += (
                "Clinical correlation is recommended. Genetic counseling is advised "
                "to discuss the implications of these findings."
            )
        else:
            interpretation = (
                "No pathogenic or likely pathogenic variants were identified in the "
                "genes analyzed. "
            )
            
            if vus:
                interpretation += (
                    f"However, {len(vus)} variant(s) of uncertain significance (VUS) "
                    "were identified. VUS should not be used for clinical decision-making "
                    "but may be reclassified as more information becomes available."
                )
            else:
                interpretation += (
                    "This negative result does not exclude a genetic etiology for the "
                    "patient's condition, as this test has limitations."
                )
        
        return interpretation
    
    def _generate_recommendations(
        self,
        pathogenic: List[ReportedVariant],
        likely_pathogenic: List[ReportedVariant],
        vus: List[ReportedVariant]
    ) -> List[str]:
        """Generate clinical recommendations."""
        
        recommendations = []
        
        if pathogenic or likely_pathogenic:
            recommendations.append(
                "Genetic counseling is recommended to discuss the clinical "
                "implications of these findings."
            )
            recommendations.append(
                "Consider cascade testing of at-risk family members."
            )
            
            # Add gene-specific recommendations
            for v in pathogenic + likely_pathogenic:
                if "BRCA" in v.gene:
                    recommendations.append(
                        f"For {v.gene}: Consider referral to oncology for cancer "
                        "risk assessment and management."
                    )
        
        if vus:
            recommendations.append(
                "Variants of uncertain significance should be periodically "
                "re-evaluated as new evidence becomes available."
            )
        
        recommendations.append(
            "This report should be interpreted in the context of the patient's "
            "clinical presentation and family history."
        )
        
        return recommendations


@dataclass
class ClinicalReport:
    """Represents a complete clinical genomics report."""
    
    patient: PatientInfo
    test: TestInfo
    pathogenic_variants: List[ReportedVariant]
    likely_pathogenic_variants: List[ReportedVariant]
    vus_variants: List[ReportedVariant]
    interpretation: str
    recommendations: List[str]
    generated_at: datetime
    
    @property
    def has_significant_findings(self) -> bool:
        """Check if report has pathogenic or likely pathogenic findings."""
        return bool(self.pathogenic_variants or self.likely_pathogenic_variants)
    
    @property
    def total_variants(self) -> int:
        """Total number of reported variants."""
        return (
            len(self.pathogenic_variants) + 
            len(self.likely_pathogenic_variants) + 
            len(self.vus_variants)
        )
    
    def to_dict(self) -> Dict:
        """Convert report to dictionary for JSON serialization."""
        return {
            "patient": {
                "id": self.patient.patient_id,
                "name": self.patient.full_name,
                "dob": self.patient.date_of_birth,
                "sex": self.patient.sex,
                "mrn": self.patient.mrn
            },
            "test": {
                "name": self.test.test_name,
                "accession": self.test.accession_number,
                "report_date": self.test.report_date,
                "lab": self.test.lab_name
            },
            "results": {
                "pathogenic": [
                    {"gene": v.gene, "variant": v.variant, "classification": v.classification}
                    for v in self.pathogenic_variants
                ],
                "likely_pathogenic": [
                    {"gene": v.gene, "variant": v.variant, "classification": v.classification}
                    for v in self.likely_pathogenic_variants
                ],
                "vus": [
                    {"gene": v.gene, "variant": v.variant, "classification": v.classification}
                    for v in self.vus_variants
                ]
            },
            "interpretation": self.interpretation,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at.isoformat()
        }
    
    def save_json(self, path: str) -> None:
        """Save report as JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Report saved to {path}")
    
    def save_html(self, path: str) -> None:
        """Save report as HTML file."""
        html = self._render_html()
        with open(path, 'w') as f:
            f.write(html)
        logger.info(f"HTML report saved to {path}")
    
    def _render_html(self) -> str:
        """Render report as HTML."""
        # Simple HTML template (in production, use Jinja2)
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Clinical Genomics Report - {self.patient.patient_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 20px; }}
        .section {{ margin-bottom: 30px; }}
        .section-title {{ color: #333; border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
        .pathogenic {{ background-color: #ffebee; }}
        .likely-pathogenic {{ background-color: #fff3e0; }}
        .vus {{ background-color: #e3f2fd; }}
        .footer {{ margin-top: 40px; font-size: 0.9em; color: #666; }}
        .disclaimer {{ background-color: #f5f5f5; padding: 15px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Clinical Genomics Report</h1>
        <p><strong>Patient:</strong> {self.patient.full_name} | 
           <strong>DOB:</strong> {self.patient.date_of_birth} |
           <strong>MRN:</strong> {self.patient.mrn}</p>
        <p><strong>Test:</strong> {self.test.test_name} |
           <strong>Accession:</strong> {self.test.accession_number} |
           <strong>Report Date:</strong> {self.test.report_date}</p>
    </div>
    
    <div class="section">
        <h2 class="section-title">Results Summary</h2>
        <p><strong>Pathogenic Variants:</strong> {len(self.pathogenic_variants)}</p>
        <p><strong>Likely Pathogenic Variants:</strong> {len(self.likely_pathogenic_variants)}</p>
        <p><strong>Variants of Uncertain Significance:</strong> {len(self.vus_variants)}</p>
    </div>
"""
        
        # Add variant tables
        if self.pathogenic_variants:
            html += self._render_variant_table(
                "Pathogenic Variants", self.pathogenic_variants, "pathogenic"
            )
        
        if self.likely_pathogenic_variants:
            html += self._render_variant_table(
                "Likely Pathogenic Variants", self.likely_pathogenic_variants, "likely-pathogenic"
            )
        
        if self.vus_variants:
            html += self._render_variant_table(
                "Variants of Uncertain Significance", self.vus_variants, "vus"
            )
        
        # Add interpretation and recommendations
        html += f"""
    <div class="section">
        <h2 class="section-title">Interpretation</h2>
        <p>{self.interpretation}</p>
    </div>
    
    <div class="section">
        <h2 class="section-title">Recommendations</h2>
        <ul>
            {"".join(f"<li>{r}</li>" for r in self.recommendations)}
        </ul>
    </div>
    
    <div class="disclaimer">
        <h3>Disclaimer</h3>
        <p>This test was developed and its performance characteristics determined by 
        {self.test.lab_name}. It has not been cleared or approved by the U.S. Food 
        and Drug Administration. This report is intended for use by qualified healthcare 
        professionals and should be interpreted in the context of the patient's clinical 
        presentation and family history.</p>
    </div>
    
    <div class="footer">
        <p>Report generated: {self.generated_at.strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p>{self.test.lab_name} | CLIA: {self.test.clia_number}</p>
    </div>
</body>
</html>
"""
        return html
    
    def _render_variant_table(
        self, 
        title: str, 
        variants: List[ReportedVariant],
        css_class: str
    ) -> str:
        """Render a variant table as HTML."""
        rows = ""
        for v in variants:
            rows += f"""
            <tr class="{css_class}">
                <td>{v.gene}</td>
                <td>{v.variant}</td>
                <td>{v.protein_change}</td>
                <td>{v.zygosity}</td>
                <td>{v.classification}</td>
                <td>{v.condition}</td>
            </tr>
"""
        
        return f"""
    <div class="section">
        <h2 class="section-title">{title}</h2>
        <table>
            <tr>
                <th>Gene</th>
                <th>Variant</th>
                <th>Protein Change</th>
                <th>Zygosity</th>
                <th>Classification</th>
                <th>Associated Condition</th>
            </tr>
            {rows}
        </table>
    </div>
"""


if __name__ == "__main__":
    # Example usage
    patient = PatientInfo(
        patient_id="P12345",
        first_name="Jane",
        last_name="Doe",
        date_of_birth="1985-03-15",
        sex="Female",
        mrn="MRN123456",
        ordering_physician="Dr. Smith",
        indication="Family history of breast cancer"
    )
    
    test = TestInfo(
        test_name="Hereditary Cancer Panel",
        accession_number="ACC-2024-001",
        clia_number="12D3456789"
    )
    
    variants = [
        ReportedVariant(
            gene="BRCA1",
            variant="c.5266dupC",
            protein_change="p.Gln1756ProfsTer74",
            zygosity="Heterozygous",
            classification="Pathogenic",
            condition="Hereditary Breast and Ovarian Cancer",
            inheritance="AD",
            acmg_criteria=["PVS1", "PS3", "PM2"]
        )
    ]
    
    generator = ClinicalReportGenerator()
    report = generator.generate_report(variants, patient, test)
    
    print("Generated Clinical Report")
    print("-" * 50)
    print(f"Patient: {report.patient.full_name}")
    print(f"Significant findings: {report.has_significant_findings}")
    print(f"Total variants: {report.total_variants}")
    print(f"\nInterpretation:\n{report.interpretation}")
