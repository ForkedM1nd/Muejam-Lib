"""Tests for base analyzer class."""

import pytest
from audit_system.base import BaseAnalyzer
from audit_system.models import Finding, AnalysisResult, Category, Severity


class TestAnalyzer(BaseAnalyzer):
    """Concrete implementation of BaseAnalyzer for testing."""
    
    def analyze(self) -> AnalysisResult:
        """Simple test implementation."""
        return AnalysisResult(
            analyzer_name=self.get_name(),
            execution_time=0.0,
            findings=self.findings,
            metrics={},
            success=True
        )
    
    def get_name(self) -> str:
        """Return analyzer name."""
        return "test_analyzer"


def test_base_analyzer_initialization():
    """Test that BaseAnalyzer can be initialized with config."""
    config = {"test_key": "test_value"}
    analyzer = TestAnalyzer(config)
    
    assert analyzer.config == config
    assert analyzer.findings == []


def test_base_analyzer_add_finding():
    """Test adding findings to analyzer."""
    analyzer = TestAnalyzer({})
    
    finding = Finding(
        id="TEST-001",
        category=Category.CODE_QUALITY,
        severity=Severity.MEDIUM,
        title="Test Finding",
        description="Test description",
        recommendation="Fix it",
        effort_estimate="low"
    )
    
    analyzer.add_finding(finding)
    
    assert len(analyzer.findings) == 1
    assert analyzer.findings[0] == finding


def test_base_analyzer_clear_findings():
    """Test clearing findings from analyzer."""
    analyzer = TestAnalyzer({})
    
    finding = Finding(
        id="TEST-001",
        category=Category.CODE_QUALITY,
        severity=Severity.LOW,
        title="Test",
        description="Test",
        recommendation="Fix",
        effort_estimate="low"
    )
    
    analyzer.add_finding(finding)
    assert len(analyzer.findings) == 1
    
    analyzer.clear_findings()
    assert len(analyzer.findings) == 0


def test_base_analyzer_get_name():
    """Test that get_name returns correct name."""
    analyzer = TestAnalyzer({})
    assert analyzer.get_name() == "test_analyzer"


def test_base_analyzer_analyze():
    """Test that analyze method works."""
    analyzer = TestAnalyzer({})
    
    finding = Finding(
        id="TEST-001",
        category=Category.SECURITY,
        severity=Severity.HIGH,
        title="Security Issue",
        description="Security problem",
        recommendation="Fix it",
        effort_estimate="high"
    )
    
    analyzer.add_finding(finding)
    result = analyzer.analyze()
    
    assert result.analyzer_name == "test_analyzer"
    assert len(result.findings) == 1
    assert result.success is True
