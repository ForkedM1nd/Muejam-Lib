"""Tests for audit orchestrator."""

import pytest
from audit_system.orchestrator import AuditOrchestrator
from audit_system.config import AuditConfig
from audit_system.base import BaseAnalyzer
from audit_system.models import Finding, AnalysisResult, Category, Severity


class MockAnalyzer(BaseAnalyzer):
    """Mock analyzer for testing."""
    
    def __init__(self, config, name="mock_analyzer", should_fail=False):
        super().__init__(config)
        self._name = name
        self._should_fail = should_fail
    
    def analyze(self) -> AnalysisResult:
        """Mock analysis that can succeed or fail."""
        if self._should_fail:
            raise Exception("Mock analyzer failure")
        
        finding = Finding(
            id=f"{self._name.upper()}-001",
            category=Category.CODE_QUALITY,
            severity=Severity.MEDIUM,
            title=f"Finding from {self._name}",
            description="Mock finding",
            recommendation="Fix it",
            effort_estimate="low"
        )
        self.add_finding(finding)
        
        return AnalysisResult(
            analyzer_name=self._name,
            execution_time=0.0,
            findings=self.findings,
            metrics={"mock_metric": 42},
            success=True
        )
    
    def get_name(self) -> str:
        """Return analyzer name."""
        return self._name


def test_orchestrator_initialization():
    """Test that orchestrator initializes correctly."""
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    
    assert orchestrator.config == config
    assert orchestrator.analyzers == []
    assert orchestrator.results == {}


def test_orchestrator_register_analyzer():
    """Test registering analyzers."""
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    
    analyzer = MockAnalyzer({})
    orchestrator.register_analyzer(analyzer)
    
    assert len(orchestrator.analyzers) == 1
    assert orchestrator.analyzers[0] == analyzer


def test_orchestrator_register_analyzer_with_dependencies():
    """Test registering analyzers with dependencies."""
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    
    analyzer1 = MockAnalyzer({}, name="analyzer1")
    analyzer2 = MockAnalyzer({}, name="analyzer2")
    
    orchestrator.register_analyzer(analyzer1)
    orchestrator.register_analyzer(analyzer2, depends_on=["analyzer1"])
    
    assert len(orchestrator.analyzers) == 2
    assert "analyzer2" in orchestrator._analyzer_dependencies
    assert "analyzer1" in orchestrator._analyzer_dependencies["analyzer2"]


def test_orchestrator_register_duplicate_analyzer():
    """Test that duplicate analyzer registration is prevented."""
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    
    analyzer1 = MockAnalyzer({}, name="same_name")
    analyzer2 = MockAnalyzer({}, name="same_name")
    
    orchestrator.register_analyzer(analyzer1)
    orchestrator.register_analyzer(analyzer2)
    
    # Should only have one analyzer
    assert len(orchestrator.analyzers) == 1


def test_orchestrator_set_max_workers():
    """Test setting max workers."""
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    
    orchestrator.set_max_workers(8)
    assert orchestrator._max_workers == 8


def test_orchestrator_set_max_workers_invalid():
    """Test that invalid max_workers raises error."""
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    
    with pytest.raises(ValueError, match="max_workers must be at least 1"):
        orchestrator.set_max_workers(0)


def test_orchestrator_run_analyzer():
    """Test running a single analyzer."""
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    
    analyzer = MockAnalyzer({})
    result = orchestrator.run_analyzer(analyzer)
    
    assert result.analyzer_name == "mock_analyzer"
    assert result.success is True
    assert len(result.findings) == 1
    assert result.execution_time >= 0


def test_orchestrator_run_analyzer_failure():
    """Test that analyzer failures are handled."""
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    
    analyzer = MockAnalyzer({}, should_fail=True)
    
    with pytest.raises(Exception, match="Mock analyzer failure"):
        orchestrator.run_analyzer(analyzer)


def test_orchestrator_run_audit():
    """Test running full audit with multiple analyzers."""
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    
    # Register multiple analyzers
    orchestrator.register_analyzer(MockAnalyzer({}, name="analyzer1"))
    orchestrator.register_analyzer(MockAnalyzer({}, name="analyzer2"))
    
    report = orchestrator.run_audit()
    
    assert report.project_name == "."
    assert len(report.results) == 2
    assert "analyzer1" in report.results
    assert "analyzer2" in report.results
    assert report.summary.total_findings == 2
    assert report.execution_time >= 0


def test_orchestrator_run_audit_with_failure():
    """Test that audit continues even if one analyzer fails."""
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    
    # Register one good and one failing analyzer
    orchestrator.register_analyzer(MockAnalyzer({}, name="good_analyzer"))
    orchestrator.register_analyzer(MockAnalyzer({}, name="bad_analyzer", should_fail=True))
    
    report = orchestrator.run_audit()
    
    # Both analyzers should have results
    assert len(report.results) == 2
    
    # Good analyzer should succeed
    assert report.results["good_analyzer"].success is True
    assert len(report.results["good_analyzer"].findings) == 1
    
    # Bad analyzer should fail gracefully
    assert report.results["bad_analyzer"].success is False
    assert report.results["bad_analyzer"].error_message == "Mock analyzer failure"
    assert len(report.results["bad_analyzer"].findings) == 0


def test_orchestrator_generate_summary():
    """Test summary generation."""
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    
    orchestrator.register_analyzer(MockAnalyzer({}, name="analyzer1"))
    orchestrator.register_analyzer(MockAnalyzer({}, name="analyzer2"))
    
    report = orchestrator.run_audit()
    summary = report.summary
    
    assert summary.total_findings == 2
    assert "medium" in summary.findings_by_severity
    assert "code_quality" in summary.findings_by_category
    assert summary.overall_score >= 0
    assert summary.overall_score <= 100


def test_orchestrator_generate_action_plan():
    """Test action plan generation."""
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    
    orchestrator.register_analyzer(MockAnalyzer({}, name="analyzer1"))
    
    report = orchestrator.run_audit()
    action_plan = report.action_plan
    
    # Mock analyzer creates medium severity, low effort findings
    # These should be categorized as quick wins
    assert len(action_plan.quick_wins) == 1
    assert len(action_plan.critical_issues) == 0


class CriticalAnalyzer(BaseAnalyzer):
    """Analyzer that generates critical findings."""
    
    def analyze(self) -> AnalysisResult:
        finding = Finding(
            id="CRIT-001",
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            title="Critical Security Issue",
            description="Critical issue",
            recommendation="Fix immediately",
            effort_estimate="high"
        )
        self.add_finding(finding)
        
        return AnalysisResult(
            analyzer_name="critical_analyzer",
            execution_time=0.0,
            findings=self.findings,
            metrics={},
            success=True
        )
    
    def get_name(self) -> str:
        return "critical_analyzer"


def test_orchestrator_action_plan_critical_issues():
    """Test that critical issues are properly categorized."""
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    
    orchestrator.register_analyzer(CriticalAnalyzer({}))
    
    report = orchestrator.run_audit()
    action_plan = report.action_plan
    
    assert len(action_plan.critical_issues) == 1
    assert action_plan.critical_issues[0].severity == Severity.CRITICAL


def test_orchestrator_validate_dependencies_missing():
    """Test that missing dependencies are detected."""
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    
    analyzer = MockAnalyzer({}, name="analyzer1")
    orchestrator.register_analyzer(analyzer, depends_on=["nonexistent"])
    
    with pytest.raises(ValueError, match="depends on nonexistent"):
        orchestrator.run_audit()


def test_orchestrator_validate_dependencies_circular():
    """Test that circular dependencies are detected."""
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    
    # Create circular dependency: A -> B -> C -> A
    analyzer_a = MockAnalyzer({}, name="analyzer_a")
    analyzer_b = MockAnalyzer({}, name="analyzer_b")
    analyzer_c = MockAnalyzer({}, name="analyzer_c")
    
    orchestrator.register_analyzer(analyzer_a, depends_on=["analyzer_c"])
    orchestrator.register_analyzer(analyzer_b, depends_on=["analyzer_a"])
    orchestrator.register_analyzer(analyzer_c, depends_on=["analyzer_b"])
    
    with pytest.raises(ValueError, match="Circular dependency detected"):
        orchestrator.run_audit()


def test_orchestrator_parallel_execution():
    """Test that independent analyzers run in parallel."""
    import time
    
    class SlowAnalyzer(BaseAnalyzer):
        """Analyzer that takes time to complete."""
        
        def __init__(self, config, name, delay=0.1):
            super().__init__(config)
            self._name = name
            self._delay = delay
        
        def analyze(self) -> AnalysisResult:
            time.sleep(self._delay)
            return AnalysisResult(
                analyzer_name=self._name,
                execution_time=self._delay,
                findings=[],
                metrics={},
                success=True
            )
        
        def get_name(self) -> str:
            return self._name
    
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    orchestrator.set_max_workers(3)
    
    # Register 3 independent analyzers that each take 0.1s
    for i in range(3):
        orchestrator.register_analyzer(SlowAnalyzer({}, name=f"slow_{i}", delay=0.1))
    
    start = time.time()
    report = orchestrator.run_audit()
    elapsed = time.time() - start
    
    # If run sequentially: 0.3s, if parallel: ~0.1s
    # Allow some overhead but should be much faster than sequential
    assert elapsed < 0.25, f"Parallel execution took {elapsed}s, expected < 0.25s"
    assert len(report.results) == 3
    assert all(r.success for r in report.results.values())


def test_orchestrator_dependency_order():
    """Test that analyzers run in dependency order."""
    execution_order = []
    
    class OrderTrackingAnalyzer(BaseAnalyzer):
        """Analyzer that tracks execution order."""
        
        def __init__(self, config, name):
            super().__init__(config)
            self._name = name
        
        def analyze(self) -> AnalysisResult:
            execution_order.append(self._name)
            return AnalysisResult(
                analyzer_name=self._name,
                execution_time=0.0,
                findings=[],
                metrics={},
                success=True
            )
        
        def get_name(self) -> str:
            return self._name
    
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    
    # Create dependency chain: A -> B -> C
    analyzer_a = OrderTrackingAnalyzer({}, name="analyzer_a")
    analyzer_b = OrderTrackingAnalyzer({}, name="analyzer_b")
    analyzer_c = OrderTrackingAnalyzer({}, name="analyzer_c")
    
    orchestrator.register_analyzer(analyzer_a)
    orchestrator.register_analyzer(analyzer_b, depends_on=["analyzer_a"])
    orchestrator.register_analyzer(analyzer_c, depends_on=["analyzer_b"])
    
    orchestrator.run_audit()
    
    # Verify execution order respects dependencies
    assert execution_order.index("analyzer_a") < execution_order.index("analyzer_b")
    assert execution_order.index("analyzer_b") < execution_order.index("analyzer_c")


def test_orchestrator_parallel_with_dependencies():
    """Test parallel execution with mixed dependencies."""
    execution_order = []
    
    class OrderTrackingAnalyzer(BaseAnalyzer):
        """Analyzer that tracks execution order."""
        
        def __init__(self, config, name):
            super().__init__(config)
            self._name = name
        
        def analyze(self) -> AnalysisResult:
            execution_order.append(self._name)
            return AnalysisResult(
                analyzer_name=self._name,
                execution_time=0.0,
                findings=[],
                metrics={},
                success=True
            )
        
        def get_name(self) -> str:
            return self._name
    
    config = AuditConfig(project_root=".")
    orchestrator = AuditOrchestrator(config)
    
    # Create dependency graph:
    #   A (independent)
    #   B (independent)
    #   C depends on A
    #   D depends on B
    #   E depends on C and D
    
    orchestrator.register_analyzer(OrderTrackingAnalyzer({}, name="A"))
    orchestrator.register_analyzer(OrderTrackingAnalyzer({}, name="B"))
    orchestrator.register_analyzer(OrderTrackingAnalyzer({}, name="C"), depends_on=["A"])
    orchestrator.register_analyzer(OrderTrackingAnalyzer({}, name="D"), depends_on=["B"])
    orchestrator.register_analyzer(OrderTrackingAnalyzer({}, name="E"), depends_on=["C", "D"])
    
    report = orchestrator.run_audit()
    
    # Verify all completed
    assert len(report.results) == 5
    assert all(r.success for r in report.results.values())
    
    # Verify dependency order
    assert execution_order.index("A") < execution_order.index("C")
    assert execution_order.index("B") < execution_order.index("D")
    assert execution_order.index("C") < execution_order.index("E")
    assert execution_order.index("D") < execution_order.index("E")
