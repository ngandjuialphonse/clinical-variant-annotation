# Clinical Variant Annotation and Reporting Pipeline

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![HIPAA](https://img.shields.io/badge/HIPAA-Compliant-green)](https://www.hhs.gov/hipaa/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-grade clinical variant annotation and reporting system that transforms raw variant calls (VCF) into clinically actionable reports. This project demonstrates the final step in a clinical genomics workflow: interpreting variants and generating reports for clinical decision-making.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Biology Concepts](#biology-concepts)
3. [Bioinformatics Concepts](#bioinformatics-concepts)
4. [Technical Stack](#technical-stack)
5. [Project Structure](#project-structure)
6. [Quick Start](#quick-start)
7. [Clinical Annotation Pipeline](#clinical-annotation-pipeline)
8. [HIPAA Compliance](#hipaa-compliance)
9. [Interview Preparation](#interview-preparation)
10. [Stretch Goals](#stretch-goals)
11. [References](#references)

---

## Project Overview

### Real-World Use Case

After identifying genetic variants in a patient's DNA, the next critical step is to **interpret** those variants. Is a variant benign or pathogenic? Does it explain the patient's symptoms? Should it change their treatment? This project builds the system that answers these questions by:

1. **Annotating** variants with functional and clinical information
2. **Filtering** to identify clinically relevant variants
3. **Generating** professional reports for clinicians
4. **Ensuring** HIPAA compliance throughout the process

### Learning Objectives

By completing this project, you will learn:

- How variant annotation works (VEP, ClinVar, gnomAD)
- Clinical variant classification (ACMG guidelines)
- How to build clinical reports from genomic data
- HIPAA compliance basics for genomic data
- Python best practices for clinical bioinformatics

---

## Biology Concepts

### From Variants to Clinical Meaning

Finding a variant is just the beginning. To understand its clinical significance, we need to answer several questions:

| Question | Information Source | Example |
|----------|-------------------|---------|
| Where is the variant? | Gene annotation | In the BRCA1 gene |
| What does it do to the protein? | Functional prediction | Causes a premature stop codon |
| How common is it? | Population databases | Found in 0.01% of people |
| Is it associated with disease? | Clinical databases | Known to cause breast cancer |

### Variant Consequence Types

When a variant occurs in a gene, it can have different effects:

| Consequence | Description | Clinical Impact |
|-------------|-------------|-----------------|
| **Synonymous** | Changes DNA but not protein | Usually benign |
| **Missense** | Changes one amino acid | Variable (benign to pathogenic) |
| **Nonsense** | Creates premature stop codon | Often pathogenic (loss of function) |
| **Frameshift** | Shifts reading frame | Often pathogenic |
| **Splice site** | Affects RNA splicing | Often pathogenic |

### ACMG Classification

The **American College of Medical Genetics (ACMG)** provides guidelines for classifying variants:

| Classification | Description | Clinical Action |
|----------------|-------------|-----------------|
| **Pathogenic** | Causes disease | Report and act on |
| **Likely Pathogenic** | Probably causes disease | Report with caution |
| **Uncertain Significance (VUS)** | Unknown impact | Report but don't act on |
| **Likely Benign** | Probably harmless | May not report |
| **Benign** | Harmless | Do not report |

---

## Bioinformatics Concepts

### Variant Effect Predictor (VEP)

**VEP** is the industry-standard tool for variant annotation. It adds:

- **Gene information**: Which gene(s) the variant affects
- **Transcript consequences**: Effect on each transcript
- **Protein changes**: Amino acid changes (e.g., p.Arg123Cys)
- **Functional predictions**: SIFT, PolyPhen scores
- **Population frequencies**: gnomAD allele frequencies

### Clinical Databases

| Database | Content | Use Case |
|----------|---------|----------|
| **ClinVar** | Clinical variant classifications | Known pathogenic/benign variants |
| **gnomAD** | Population allele frequencies | Filtering common variants |
| **OMIM** | Gene-disease relationships | Understanding affected genes |
| **PharmGKB** | Drug-gene interactions | Pharmacogenomics |

### Annotation Pipeline Flow

```
VCF Input → VEP Annotation → ClinVar Lookup → Frequency Filtering → Classification → Report
```

---

## Technical Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Annotation** | Ensembl VEP | Variant effect prediction |
| **Clinical Data** | ClinVar API | Clinical significance lookup |
| **Population Data** | gnomAD | Allele frequency filtering |
| **Programming** | Python 3.11 | Pipeline implementation |
| **Reporting** | Jinja2 + WeasyPrint | PDF report generation |
| **Containerization** | Docker | Reproducible environment |
| **Security** | AWS KMS | HIPAA-compliant encryption |

---

## Project Structure

```
clinical-variant-annotation/
├── README.md                    # This file
├── docker/
│   └── Dockerfile              # Docker image definition
├── src/
│   ├── annotation/
│   │   ├── __init__.py
│   │   ├── vep_annotator.py    # VEP annotation wrapper
│   │   ├── clinvar_lookup.py   # ClinVar API client
│   │   └── frequency_filter.py # Population frequency filtering
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── report_generator.py # Clinical report generation
│   │   └── pdf_renderer.py     # PDF rendering
│   └── utils/
│       ├── __init__.py
│       ├── vcf_parser.py       # VCF file parsing
│       └── security.py         # HIPAA compliance utilities
├── templates/
│   └── clinical_report.html    # Report template
├── scripts/
│   ├── run_annotation.sh       # Main execution script
│   └── download_data.sh        # Sample data download
├── data/                       # Input VCF files (gitignored)
├── results/                    # Output reports (gitignored)
├── docs/
│   ├── LEARNING.md            # Learning resources
│   └── HIPAA_COMPLIANCE.md    # HIPAA documentation
└── requirements.txt            # Python dependencies
```

---

## Quick Start

### Prerequisites

- Docker installed
- Python 3.11+ (for local development)
- At least 8GB RAM

### Step 1: Clone the Repository

```bash
git clone https://github.com/ngandjuialphonse/clinical-variant-annotation.git
cd clinical-variant-annotation
```

### Step 2: Build the Docker Image

```bash
docker build -t clinical-annotation:latest -f docker/Dockerfile .
```

### Step 3: Download Sample Data

```bash
bash scripts/download_data.sh
```

### Step 4: Run the Annotation Pipeline

```bash
bash scripts/run_annotation.sh data/sample.vcf
```

### Step 5: View Results

Open `results/clinical_report.pdf` to view the generated clinical report.

---

## Clinical Annotation Pipeline

### Step 1: VCF Parsing

The pipeline reads the input VCF file and extracts variant information:

```python
from src.utils.vcf_parser import VCFParser

parser = VCFParser("sample.vcf")
variants = parser.parse()
```

### Step 2: VEP Annotation

Each variant is annotated with functional consequences:

```python
from src.annotation.vep_annotator import VEPAnnotator

annotator = VEPAnnotator()
annotated_variants = annotator.annotate(variants)
```

### Step 3: ClinVar Lookup

Clinical significance is retrieved from ClinVar:

```python
from src.annotation.clinvar_lookup import ClinVarClient

clinvar = ClinVarClient()
for variant in annotated_variants:
    variant.clinical_significance = clinvar.lookup(variant)
```

### Step 4: Frequency Filtering

Common variants are filtered out:

```python
from src.annotation.frequency_filter import FrequencyFilter

filter = FrequencyFilter(max_af=0.01)  # 1% threshold
rare_variants = filter.apply(annotated_variants)
```

### Step 5: Report Generation

A clinical report is generated:

```python
from src.reporting.report_generator import ReportGenerator

generator = ReportGenerator()
report = generator.generate(rare_variants, patient_info)
report.save_pdf("clinical_report.pdf")
```

---

## HIPAA Compliance

### Overview

This project implements basic HIPAA compliance measures for handling Protected Health Information (PHI):

| Requirement | Implementation |
|-------------|----------------|
| **Access Control** | Role-based access, audit logging |
| **Encryption at Rest** | AES-256 encryption for stored data |
| **Encryption in Transit** | TLS 1.3 for all network communication |
| **Audit Trails** | Comprehensive logging of all data access |
| **Data Minimization** | Only necessary PHI included in reports |

### Security Features

```python
from src.utils.security import SecurityManager

# Initialize security manager
security = SecurityManager(kms_key_id="your-kms-key")

# Encrypt sensitive data
encrypted_data = security.encrypt(patient_data)

# Log access
security.log_access(user_id, action="view_report", resource_id=report_id)
```

### AWS Integration

For production deployment, the pipeline integrates with AWS security services:

- **AWS KMS**: Key management for encryption
- **AWS CloudTrail**: Audit logging
- **AWS S3**: Encrypted storage with bucket policies
- **AWS IAM**: Fine-grained access control

---

## Interview Preparation

### Common Interview Questions

1. **"How would you annotate a VCF file for clinical interpretation?"**
   > I would use Ensembl VEP to add functional annotations, then query ClinVar for known clinical significance, filter by population frequency using gnomAD, and apply ACMG guidelines for classification.

2. **"What is the difference between a pathogenic and a VUS variant?"**
   > A pathogenic variant has strong evidence that it causes disease and should be acted upon clinically. A VUS (Variant of Uncertain Significance) lacks sufficient evidence to classify as pathogenic or benign, and clinical decisions should not be based solely on a VUS.

3. **"How would you ensure HIPAA compliance in a genomics pipeline?"**
   > I would implement encryption at rest and in transit, use role-based access control, maintain comprehensive audit logs, minimize PHI in outputs, and use HIPAA-eligible cloud services like AWS with BAA agreements.

4. **"What population databases would you use for variant filtering?"**
   > gnomAD is the primary resource for population allele frequencies. I would filter variants with allele frequency >1% as likely benign, but consider disease-specific thresholds for dominant vs. recessive conditions.

5. **"How do you handle variants of uncertain significance in clinical reports?"**
   > VUS should be reported with clear language indicating uncertainty. They should not drive clinical decisions but may warrant periodic re-evaluation as new evidence emerges. I would include recommendations for genetic counseling.

### Talking Points

- **VEP vs. ANNOVAR**: VEP is more comprehensive and actively maintained; ANNOVAR is faster but requires manual database updates.

- **ClinVar Limitations**: ClinVar contains user-submitted data of varying quality. Always check the review status and submitter credentials.

- **ACMG Guidelines**: Understanding the 28 criteria (PVS1, PS1-4, PM1-6, PP1-5, BA1, BS1-4, BP1-7) is essential for clinical bioinformatics roles.

---

## Stretch Goals

1. **Interactive Dashboard**: Build a Streamlit or Flask dashboard for variant exploration
2. **Automated Classification**: Implement ACMG criteria programmatically using InterVar
3. **Multi-Sample Reports**: Generate family-based reports for trio analysis
4. **Integration Testing**: Add comprehensive tests with GIAB truth sets
5. **Cloud Deployment**: Deploy on AWS with full HIPAA compliance

---

## References

1. [Ensembl VEP Documentation](https://www.ensembl.org/info/docs/tools/vep/index.html)
2. [ClinVar Database](https://www.ncbi.nlm.nih.gov/clinvar/)
3. [gnomAD Browser](https://gnomad.broadinstitute.org/)
4. [ACMG Guidelines](https://www.acmg.net/ACMG/Medical-Genetics-Practice-Resources/Practice-Guidelines.aspx)
5. [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Created as a portfolio project for clinical bioinformatics interview preparation.
