"""Integration tests for the audit system."""

import pytest
from pathlib import Path
from ..config import AuditConfig
from ..orchestrator import AuditOrchestrator
from ..analyzers import (
    CodeQualityAnalyzer, SecurityScanner, PerformanceProfiler,
    DatabaseAnalyzer, APIEvaluator, TestCoverageAnalyzer,
    InfrastructureAuditor, DependencyChecker, DocumentationEvaluator,
    ScalabilityAssessor
)


def test_full_audit_execution():
    """Test that full audit can execute all analyzers."""
    # Create minimal config
    config = AuditConfig(
        project_root=".",
        backend_path="backend",
        frontend_path="frontend",
        infra_path="infra",
        docs_path="docs",
        enabled_analyzers=["code_quality"],
        min_code_coverage=80.0,
        max_complexity=10,
        max_function_length=50,
        output_dir="output",
        output_formats=["json"]
    )
    
    # Create orchestrator
    orchestrator = AuditOrchestrator(config)
    
    # Register one analyzer for basic test
    orchestrator.register_analyzer(CodeQualityAnalyzer(config.to_dict()))
    
    # Run audit
    report = orchestrator.run_audit()
    
    # Verify report structure
    assert report is not None
    assert report.project_name == "."
    assert report.execution_time >= 0
    assert report.summary is not None
    assert report.action_plan is not None
    assert "code_quality_analyzer" in report.results


def test_analyzer_registration():
    """Test that analyzers can be registered."""
    config = AuditConfig(
        project_root=".",
        backend_path="backend",
        frontend_path="frontend",
        infra_path="infra",
        docs_path="docs",
        enabled_analyzers=[],
        min_code_coverage=80.0,
        max_complexity=10,
        max_function_length=50,
        output_dir="output",
        output_formats=["json"]
    )
    
    orchestrator = AuditOrchestrator(config)
    
    # Register multiple analyzers
    analyzers = [
        CodeQualityAnalyzer(config.to_dict()),
        SecurityScanner(config.to_dict()),
        PerformanceProfiler(config.to_dict()),
    ]
    
    for analyzer in analyzers:
        orchestrator.register_analyzer(analyzer)
    
    assert len(orchestrator.analyzers) == 3


def test_report_export_formats():
    """Test that reports can be exported in different formats."""
    config = AuditConfig(
        project_root=".",
        backend_path="backend",
        frontend_path="frontend",
        infra_path="infra",
        docs_path="docs",
        enabled_analyzers=["code_quality"],
        min_code_coverage=80.0,
        max_complexity=10,
        max_function_length=50,
        output_dir="output",
        output_formats=["json", "markdown", "html"]
    )
    
    orchestrator = AuditOrchestrator(config)
    orchestrator.register_analyzer(CodeQualityAnalyzer(config.to_dict()))
    
    report = orchestrator.run_audit()
    
    # Test export methods exist and can be called
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "report.json"
        md_path = Path(tmpdir) / "report.md"
        html_path = Path(tmpdir) / "report.html"
        
        report.export_json(str(json_path))
        report.export_markdown(str(md_path))
        report.export_html(str(html_path))
        
        assert json_path.exists()
        assert md_path.exists()
        assert html_path.exists()


def test_all_analyzers_can_be_instantiated():
    """Test that all analyzer classes can be instantiated."""
    config_dict = {
        "project_root": ".",
        "backend_path": "backend",
        "frontend_path": "frontend",
        "infra_path": "infra",
        "docs_path": "docs",
        "min_code_coverage": 80.0,
        "max_complexity": 10,
        "max_function_length": 50,
    }
    
    analyzers = [
        CodeQualityAnalyzer(config_dict),
        SecurityScanner(config_dict),
        PerformanceProfiler(config_dict),
        DatabaseAnalyzer(config_dict),
        APIEvaluator(config_dict),
        TestCoverageAnalyzer(config_dict),
        InfrastructureAuditor(config_dict),
        DependencyChecker(config_dict),
        DocumentationEvaluator(config_dict),
        ScalabilityAssessor(config_dict),
    ]
    
    # Verify all have required methods
    for analyzer in analyzers:
        assert hasattr(analyzer, 'analyze')
        assert hasattr(analyzer, 'get_name')
        assert callable(analyzer.analyze)
        assert callable(analyzer.get_name)
        assert isinstance(analyzer.get_name(), str)
