# Tools Directory

This directory contains build tools, scripts, and utilities for repository management.

## Contents

- `setup.sh` - Linux/Mac setup script
- `setup.ps1` - Windows setup script
- `restructure/` - Monorepo restructure scripts
- `audit_system/` - Project audit and evaluation system

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. For the audit system, ensure you have the required packages:
   ```bash
   pip install pyyaml
   ```

## Configuration

### Audit System Configuration

The audit system can be configured via `audit_system/config.yaml`:

```yaml
# Project paths
project_root: "."
backend_path: "apps/backend"
frontend_path: "apps/frontend"

# Enabled analyzers
enabled_analyzers:
  - code_quality
  - security
  - performance
  - database
  - api
  - test_coverage
  - infrastructure
  - dependencies
  - documentation
  - scalability

# Thresholds
min_code_coverage: 70.0
max_complexity: 20
max_function_length: 1100

# Output configuration
output_dir: "audit_reports"
output_formats:
  - markdown
  - json
  - html
```

### Environment Variables

No environment variables are required for basic operation.

## Usage

### Setup Scripts

Run the appropriate setup script for your platform to configure the development environment:

**Linux/Mac:**
```bash
./setup.sh
```

**Windows:**
```powershell
.\setup.ps1
```

### Audit System

Run the audit system to evaluate project quality:

```bash
cd tools
python -m audit_system.cli --config audit_system/config.yaml
```

View the generated reports in `audit_reports/`:
- `audit_report.md` - Markdown format
- `audit_report.json` - JSON format
- `audit_report.html` - HTML format
