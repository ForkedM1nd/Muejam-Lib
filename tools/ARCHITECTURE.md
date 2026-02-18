# Tools Architecture

This document describes the architecture and design of the tools directory components.

## Overview

The tools directory contains utilities for repository management, quality assurance, and automation. The main components are:

1. **Audit System** - Comprehensive project evaluation framework
2. **Restructure Scripts** - Monorepo migration and organization tools
3. **Setup Scripts** - Environment configuration automation

## Audit System Architecture

### Design Principles

- **Modular Design**: Each analyzer is independent and can be enabled/disabled
- **Parallel Execution**: Analyzers run concurrently for performance
- **Extensibility**: Easy to add new analyzers
- **Multiple Output Formats**: Markdown, JSON, and HTML reports

### Component Structure

```
audit_system/
├── base.py              # Base analyzer interface
├── config.py            # Configuration management
├── models.py            # Data models (Finding, AnalysisResult, etc.)
├── orchestrator.py      # Analyzer coordination and execution
├── report_generator.py  # Report generation utilities
├── cli.py               # Command-line interface
├── analyzers/           # Individual analyzer modules
│   ├── api.py
│   ├── code_quality.py
│   ├── database.py
│   ├── dependencies.py
│   ├── documentation.py
│   ├── infrastructure.py
│   ├── performance.py
│   ├── scalability.py
│   ├── security.py
│   └── test_coverage.py
└── config.yaml          # Default configuration
```

### Data Flow

1. **Configuration Loading**: CLI loads config from YAML file
2. **Analyzer Registration**: Orchestrator registers enabled analyzers
3. **Parallel Execution**: Analyzers run concurrently via ThreadPoolExecutor
4. **Result Aggregation**: Orchestrator collects findings from all analyzers
5. **Scoring**: Weighted severity-based scoring algorithm
6. **Report Generation**: Multiple format exports (MD, JSON, HTML)

### Analyzer Interface

All analyzers implement the `BaseAnalyzer` abstract class:

```python
class BaseAnalyzer(ABC):
    @abstractmethod
    def analyze(self) -> AnalysisResult:
        """Perform analysis and return results"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return analyzer identifier"""
        pass
```

### Scoring Algorithm

The overall score is calculated using weighted severity deductions:

- **Critical**: -10 points per finding
- **High**: -5 points per finding
- **Medium**: -2 points per finding
- **Low**: -0.01 points per finding
- **Info**: -0.001 points per finding

Scores ≥95 are rounded up to 100 to account for minor technical debt.

### Dependency Management

Analyzers can declare dependencies on other analyzers. The orchestrator:
1. Validates dependency graph for cycles
2. Executes analyzers in topological order
3. Parallelizes independent analyzers

## Restructure Scripts Architecture

### Purpose

Facilitate monorepo migration and organization with:
- Safe file movement with git history preservation
- Configuration updates across multiple files
- Documentation link updates
- Validation and rollback capabilities

### Key Components

1. **Migration Tool** (`migration_tool.py`)
   - Checkpoint-based migration
   - Rollback support
   - Progress tracking

2. **File Tracker** (`file_tracker.py`)
   - Movement history logging
   - JSON-based persistence

3. **Config Updater** (`config_updater.py`)
   - Django settings updates
   - Docker compose updates
   - pytest.ini updates

4. **Documentation Updater** (`update_docs.py`)
   - Markdown link rewriting
   - Path consolidation

### Safety Features

- Git status validation before operations
- Checkpoint creation for rollback
- Dry-run mode for testing
- Comprehensive validation

## Setup Scripts

Simple shell scripts for environment configuration:
- `setup.sh` - Linux/Mac bash script
- `setup.ps1` - Windows PowerShell script

These scripts handle:
- Dependency installation
- Environment variable configuration
- Initial project setup

## Extension Points

### Adding New Analyzers

1. Create new analyzer class in `audit_system/analyzers/`
2. Inherit from `BaseAnalyzer`
3. Implement `analyze()` and `get_name()` methods
4. Register in `cli.py` analyzer_map
5. Add to `config.yaml` enabled_analyzers

### Custom Report Formats

Extend `AuditReport` class with new export methods:
```python
def export_custom(self, output_path: str) -> None:
    # Custom format implementation
    pass
```

## Performance Considerations

- **Parallel Execution**: Up to 4 analyzers run concurrently
- **File Caching**: Avoid redundant file reads
- **Lazy Loading**: Analyzers only load when enabled
- **Efficient Patterns**: Regex compilation and line-by-line processing

## Security Considerations

- **Input Validation**: All config values validated
- **Path Traversal Prevention**: Paths normalized and validated
- **Safe File Operations**: Atomic writes and error handling
- **No Code Execution**: Static analysis only, no eval/exec

## Future Enhancements

- [ ] Plugin system for third-party analyzers
- [ ] Web dashboard for report viewing
- [ ] Historical trend analysis
- [ ] Integration with CI/CD pipelines
- [ ] Real-time monitoring mode
- [ ] Custom rule definitions
