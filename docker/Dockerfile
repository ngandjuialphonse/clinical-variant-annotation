# Clinical Variant Annotation Pipeline Docker Image
# Includes VEP, Python dependencies, and reporting tools

FROM python:3.11-slim

LABEL maintainer="Clinical Bioinformatics Portfolio"
LABEL description="Clinical Variant Annotation and Reporting Pipeline"
LABEL version="1.0"

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    build-essential \
    libpq-dev \
    # WeasyPrint dependencies for PDF generation
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY templates/ ./templates/
COPY scripts/ ./scripts/

# Create directories for data and results
RUN mkdir -p /data /results /logs

# Set environment variables
ENV PYTHONPATH=/app

# Default command
CMD ["python", "-m", "src.annotation.vep_annotator"]

# Usage:
# Build: docker build -t clinical-annotation:latest -f docker/Dockerfile .
# Run: docker run -v $(pwd)/data:/data -v $(pwd)/results:/results clinical-annotation:latest
