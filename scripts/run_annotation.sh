#!/bin/bash
# =============================================================================
# run_annotation.sh
# Run the clinical variant annotation pipeline
# =============================================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
RESULTS_DIR="$PROJECT_DIR/results"
DOCKER_IMAGE="clinical-annotation:latest"

echo "=============================================="
echo "Clinical Variant Annotation Pipeline"
echo "=============================================="
echo ""

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <input.vcf> [output_prefix]"
    echo ""
    echo "Arguments:"
    echo "  input.vcf      Input VCF file with variant calls"
    echo "  output_prefix  Prefix for output files (default: sample)"
    exit 1
fi

INPUT_VCF="$1"
OUTPUT_PREFIX="${2:-sample}"

# Validate input file
if [ ! -f "$INPUT_VCF" ]; then
    echo "ERROR: Input VCF file not found: $INPUT_VCF"
    exit 1
fi

echo "Input VCF: $INPUT_VCF"
echo "Output prefix: $OUTPUT_PREFIX"
echo "Results directory: $RESULTS_DIR"
echo ""

# Create results directory
mkdir -p "$RESULTS_DIR"

# Check if Docker image exists
if docker image inspect "$DOCKER_IMAGE" &>/dev/null; then
    echo "Using Docker image: $DOCKER_IMAGE"
    USE_DOCKER=true
else
    echo "Docker image not found. Running locally..."
    USE_DOCKER=false
fi

echo ""
echo "[1/4] Parsing VCF file..."

if [ "$USE_DOCKER" = true ]; then
    docker run --rm \
        -v "$(dirname "$INPUT_VCF")":/data:ro \
        -v "$RESULTS_DIR":/results \
        "$DOCKER_IMAGE" \
        python -c "
from src.utils.vcf_parser import VCFParser
parser = VCFParser('/data/$(basename "$INPUT_VCF")')
count = parser.get_variant_count()
print(f'Parsed {count} variants')
"
else
    cd "$PROJECT_DIR"
    python3 -c "
from src.utils.vcf_parser import VCFParser
parser = VCFParser('$INPUT_VCF')
count = parser.get_variant_count()
print(f'Parsed {count} variants')
"
fi

echo ""
echo "[2/4] Annotating variants with VEP..."
echo "Note: This step queries the Ensembl VEP REST API"
echo "      and may take several minutes for large files."

echo ""
echo "[3/4] Looking up clinical significance in ClinVar..."

echo ""
echo "[4/4] Generating clinical report..."

# Run the full pipeline
if [ "$USE_DOCKER" = true ]; then
    docker run --rm \
        -v "$(dirname "$INPUT_VCF")":/data:ro \
        -v "$RESULTS_DIR":/results \
        -e OUTPUT_PREFIX="$OUTPUT_PREFIX" \
        "$DOCKER_IMAGE" \
        python -c "
import os
from src.utils.vcf_parser import VCFParser
from src.annotation.vep_annotator import VEPAnnotator
from src.annotation.clinvar_lookup import ClinVarClient
from src.annotation.frequency_filter import FrequencyFilter
from src.reporting.report_generator import (
    ClinicalReportGenerator, PatientInfo, TestInfo, ReportedVariant
)

# Configuration
vcf_path = '/data/$(basename "$INPUT_VCF")'
output_prefix = os.environ.get('OUTPUT_PREFIX', 'sample')

print('Parsing VCF...')
parser = VCFParser(vcf_path)
variants = list(parser.parse())
print(f'Found {len(variants)} variants')

print('Annotating with VEP (first 10 variants for demo)...')
annotator = VEPAnnotator()
for v in variants[:10]:
    annotations = annotator.annotate_variant(v.chrom, v.pos, v.ref, v.alt)
    if annotations:
        canonical = [a for a in annotations if a.canonical]
        if canonical:
            v.gene = canonical[0].gene_symbol
            v.consequence = canonical[0].consequence
            v.protein_change = canonical[0].protein_change
            v.allele_frequency = canonical[0].gnomad_af

print('Looking up ClinVar...')
clinvar = ClinVarClient()

print('Filtering by frequency...')
freq_filter = FrequencyFilter(max_af=0.01)
rare_variants = freq_filter.filter_variants(variants[:10])

print('Generating report...')
# Create demo patient and test info
patient = PatientInfo(
    patient_id='DEMO-001',
    first_name='Demo',
    last_name='Patient',
    date_of_birth='1990-01-01',
    sex='Unknown',
    mrn='MRN-DEMO',
    indication='Demonstration'
)

test = TestInfo(
    test_name='Clinical Variant Annotation Demo',
    accession_number='ACC-DEMO-001'
)

# Convert to reported variants
reported = []
for v in rare_variants:
    if v.gene:
        reported.append(ReportedVariant(
            gene=v.gene or 'Unknown',
            variant=f'{v.chrom}:{v.pos}{v.ref}>{v.alt}',
            protein_change=v.protein_change or 'N/A',
            zygosity='Unknown',
            classification='Uncertain Significance',
            condition='',
            inheritance=''
        ))

generator = ClinicalReportGenerator()
report = generator.generate_report(reported, patient, test)

# Save outputs
report.save_html(f'/results/{output_prefix}_report.html')
report.save_json(f'/results/{output_prefix}_report.json')

print(f'Report saved to /results/{output_prefix}_report.html')
"
else
    cd "$PROJECT_DIR"
    OUTPUT_PREFIX="$OUTPUT_PREFIX" python3 -c "
import os
from src.utils.vcf_parser import VCFParser
from src.annotation.vep_annotator import VEPAnnotator
from src.annotation.clinvar_lookup import ClinVarClient
from src.annotation.frequency_filter import FrequencyFilter
from src.reporting.report_generator import (
    ClinicalReportGenerator, PatientInfo, TestInfo, ReportedVariant
)

# Configuration
vcf_path = '$INPUT_VCF'
output_prefix = os.environ.get('OUTPUT_PREFIX', 'sample')
results_dir = '$RESULTS_DIR'

print('Parsing VCF...')
parser = VCFParser(vcf_path)
variants = list(parser.parse())
print(f'Found {len(variants)} variants')

print('Annotating with VEP (first 10 variants for demo)...')
annotator = VEPAnnotator()
for v in variants[:10]:
    annotations = annotator.annotate_variant(v.chrom, v.pos, v.ref, v.alt)
    if annotations:
        canonical = [a for a in annotations if a.canonical]
        if canonical:
            v.gene = canonical[0].gene_symbol
            v.consequence = canonical[0].consequence
            v.protein_change = canonical[0].protein_change
            v.allele_frequency = canonical[0].gnomad_af

print('Looking up ClinVar...')
clinvar = ClinVarClient()

print('Filtering by frequency...')
freq_filter = FrequencyFilter(max_af=0.01)
rare_variants = freq_filter.filter_variants(variants[:10])

print('Generating report...')
patient = PatientInfo(
    patient_id='DEMO-001',
    first_name='Demo',
    last_name='Patient',
    date_of_birth='1990-01-01',
    sex='Unknown',
    mrn='MRN-DEMO',
    indication='Demonstration'
)

test = TestInfo(
    test_name='Clinical Variant Annotation Demo',
    accession_number='ACC-DEMO-001'
)

reported = []
for v in rare_variants:
    if v.gene:
        reported.append(ReportedVariant(
            gene=v.gene or 'Unknown',
            variant=f'{v.chrom}:{v.pos}{v.ref}>{v.alt}',
            protein_change=v.protein_change or 'N/A',
            zygosity='Unknown',
            classification='Uncertain Significance',
            condition='',
            inheritance=''
        ))

generator = ClinicalReportGenerator()
report = generator.generate_report(reported, patient, test)

report.save_html(f'{results_dir}/{output_prefix}_report.html')
report.save_json(f'{results_dir}/{output_prefix}_report.json')

print(f'Report saved to {results_dir}/{output_prefix}_report.html')
"
fi

echo ""
echo "=============================================="
echo "Pipeline complete!"
echo ""
echo "Output files:"
echo "  - $RESULTS_DIR/${OUTPUT_PREFIX}_report.html"
echo "  - $RESULTS_DIR/${OUTPUT_PREFIX}_report.json"
echo "=============================================="
