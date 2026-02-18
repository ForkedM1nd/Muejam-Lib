# Project Evaluation and Audit System

A comprehensive analysis tool for evaluating code quality, security, performance, architecture, and operational readiness across the MueJam Library application.

## Overview

The audit system systematically assesses:
- **Code Quality**: PEP 8 compliance, complexity metrics, code duplication, Django/React patterns
- **Security**: Vulnerability scanning, authentication analysis, injection detection, GDPR compliance
- **Performance**: N+1 queries, missing indexes, bundle sizes, React optimization
- **Architecture**: Separation of concerns, coupling analysis, architectural patterns
- **Database**: Schema design, constraints, migrations, Prisma/Django consistency
- **API Design**: RESTful principles, documentation, consistency
- **Testing**: Coverage analysis, critical path testing, property-based tests
- **Infrastructure**: Docker configuration, monitoring, logging, deployment readiness
- **Dependencies**: Outdated packages, vulnerabilities, license compatibility
- **Documentation**: Docstring coverage, README completeness, architecture docs
- **Scalability**: Single points of failure, stateful components, technical debt

## Installation

```bash
cd tools/audit_system
pip install -r requirements.txt
```

## Configuration

Copy the example configuration and customize it:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` to match your project structure and preferences.

## Usage

```python
from audit_system.config import AuditConfig
from audit_system.orchestrator import AuditOrchestrator
from audit_system.logging_config import setup_logging

# Setup logging
setup_logging(level="INFO", log_file="audit.log")

# Load configuration
config = AuditConfig.from_file("config.yaml")

# Create orchestrator
orchestrator = AuditOrchestrator(config)

# Register analyzers (to be implemented)
# orchestrator.register_analyzer(CodeQualityAnalyzer(config))
# orchestrator.register_analyzer(SecurityScanner(config))
# ... etc

# Run audit
report = orchestrator.run_audit()

# Export reports
report.export_markdown("audit_reports/report.md")
report.export_json("audit_reports/report.json")
report.export_html("audit_reports/report.html")
```

## Project Structure

```
audit_system/
├── __init__.py           # Package initialization
├── base.py               # BaseAnalyzer interface
├── config.py             # Configuration management
├── models.py             # Data models (Finding, AnalysisResult, AuditReport)
├── orchestrator.py       # Audit orchestrator
├── logging_config.py     # Logging setup
├── exceptions.py         # Exception classes
├── requirements.txt      # Python dependencies
├── config.example.yaml   # Example configuration
└── README.md            # This file
```

## Development

### Adding a New Analyzer

1. Create a new file for your analyzer (e.g., `code_quality.py`)
2. Inherit from `BaseAnalyzer`
3. Implement the `analyze()` and `get_name()` methods
4. Register the analyzer with the orchestrator

Example:

```python
from audit_system.base import BaseAnalyzer
from audit_system.models import AnalysisResult, Finding, Category, Severity

class MyAnalyzer(BaseAnalyzer):
    def get_name(self) -> str:
        return "my_analyzer"
    
    def analyze(self) -> AnalysisResult:
        # Perform analysis
        finding = Finding(
            id="MY-001",
            category=Category.CODE_QUALITY,
            severity=Severity.MEDIUM,
            title="Example Finding",
            description="This is an example finding",
            recommendation="Fix the issue",
            effort_estimate="low"
        )
        self.add_finding(finding)
        
        return AnalysisResult(
            analyzer_name=self.get_name(),
            execution_time=0.0,
            findings=self.findings,
            metrics={},
            success=True
        )
```

## Testing

Run tests with pytest:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest --cov=audit_system tests/
```

## License

Part of the MueJam Library project.
