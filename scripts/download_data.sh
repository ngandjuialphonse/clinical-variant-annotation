#!/bin/bash
# =============================================================================
# download_data.sh
# Download sample VCF data for testing the annotation pipeline
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_DIR/data"

echo "=============================================="
echo "Clinical Variant Annotation - Sample Data"
echo "=============================================="
echo ""
echo "Downloading sample VCF files for testing..."
echo "Target directory: $DATA_DIR"
echo ""

mkdir -p "$DATA_DIR"

# Download a small sample VCF from GIAB (Genome in a Bottle)
echo "[1/2] Downloading sample VCF..."

# Create a small test VCF file
cat > "$DATA_DIR/sample.vcf" << 'EOF'
##fileformat=VCFv4.2
##FILTER=<ID=PASS,Description="All filters passed">
##INFO=<ID=DP,Number=1,Type=Integer,Description="Total Depth">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Read Depth">
##FORMAT=<ID=GQ,Number=1,Type=Integer,Description="Genotype Quality">
##contig=<ID=1,length=249250621>
##contig=<ID=17,length=81195210>
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	SAMPLE
1	69511	rs75062661	A	G	100	PASS	DP=50	GT:DP:GQ	0/1:50:99
1	942451	rs6672356	T	C	100	PASS	DP=45	GT:DP:GQ	0/1:45:99
1	1158631	rs4970383	A	G	100	PASS	DP=60	GT:DP:GQ	1/1:60:99
17	43092919	rs80357906	G	A	100	PASS	DP=55	GT:DP:GQ	0/1:55:99
17	43093220	rs80357713	C	T	100	PASS	DP=48	GT:DP:GQ	0/1:48:99
17	43094464	rs80357711	G	A	100	PASS	DP=52	GT:DP:GQ	0/1:52:99
EOF

echo "  ✓ Created sample.vcf with 6 test variants"

# Create a larger test file with more variants
echo ""
echo "[2/2] Creating extended test dataset..."

cat > "$DATA_DIR/extended_sample.vcf" << 'EOF'
##fileformat=VCFv4.2
##FILTER=<ID=PASS,Description="All filters passed">
##INFO=<ID=DP,Number=1,Type=Integer,Description="Total Depth">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Read Depth">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	SAMPLE
1	69511	rs75062661	A	G	100	PASS	DP=50	GT:DP	0/1:50
1	942451	rs6672356	T	C	100	PASS	DP=45	GT:DP	0/1:45
1	1158631	rs4970383	A	G	100	PASS	DP=60	GT:DP	1/1:60
2	179427537	rs1801133	G	A	100	PASS	DP=55	GT:DP	0/1:55
7	117199646	rs113993960	ATCT	A	100	PASS	DP=40	GT:DP	0/1:40
13	32914438	rs80359550	T	C	100	PASS	DP=48	GT:DP	0/1:48
13	32936732	rs80359065	C	T	100	PASS	DP=52	GT:DP	0/1:52
17	43092919	rs80357906	G	A	100	PASS	DP=55	GT:DP	0/1:55
17	43093220	rs80357713	C	T	100	PASS	DP=48	GT:DP	0/1:48
17	43094464	rs80357711	G	A	100	PASS	DP=52	GT:DP	0/1:52
EOF

echo "  ✓ Created extended_sample.vcf with 10 test variants"

echo ""
echo "=============================================="
echo "Sample data download complete!"
echo ""
echo "Available test files:"
echo "  - $DATA_DIR/sample.vcf (6 variants)"
echo "  - $DATA_DIR/extended_sample.vcf (10 variants)"
echo ""
echo "Notable variants included:"
echo "  - BRCA1 variants (chr17)"
echo "  - BRCA2 variants (chr13)"
echo "  - CFTR variant (chr7) - cystic fibrosis"
echo "  - MTHFR variant (chr2) - folate metabolism"
echo ""
echo "Next steps:"
echo "  bash scripts/run_annotation.sh data/sample.vcf"
echo "=============================================="
