"""Tests for data models."""

import pytest
from audit_system.models import (
    Finding, AnalysisResult, AuditSummary, ActionPlan, AuditReport,
    Severity, Category
)


def test_finding_creation():
    """Test creating a Finding object."""
    finding = Finding(
        id="TEST-001",
        category=Category.CODE_QUALITY,
        severity=Severity.HIGH,
        title="Test Finding",
        description="This is a test finding",
        recommendation="Fix the issue",
        effort_estimate="medium",
        file_path="test.py",
        line_number=42
    )
    
    assert finding.id == "TEST-001"
    assert finding.category == Category.CODE_QUALITY
    assert finding.severity == Severity.HIGH
    assert finding.title == "Test Finding"
    assert finding.file_path == "test.py"
    assert finding.line_number == 42


def test_finding_to_dict():
    """Test converting Finding to dictionary."""
    finding = Finding(
        id="TEST-001",
        category=Category.SECURITY,
        severity=Severity.CRITICAL,
        title="Security Issue",
        description="Critical security vulnerability",
        recommendation="Patch immediately",
        effort_estimate="high"
    )
    
    finding_dict = finding.to_dict()
    
    assert isinstance(finding_dict, dict)
    assert finding_dict['id'] == "TEST-001"
    assert finding_dict['category'] == "security"
    assert finding_dict['severity'] == "critical"
    assert finding_dict['title'] == "Security Issue"


def test_finding_from_dict():
    """Test creating Finding from dictionary."""
    data = {
        'id': 'TEST-002',
        'category': 'performance',
        'severity': 'high',
        'title': 'Performance Issue',
        'description': 'Slow database query',
        'recommendation': 'Add index to table',
        'effort_estimate': 'medium',
        'file_path': 'models.py',
        'line_number': 100,
        'code_snippet': 'User.objects.all()',
        'references': ['https://docs.djangoproject.com/'],
        'metadata': {'query_time': '500ms'}
    }
    
    finding = Finding.from_dict(data)
    
    assert finding.id == 'TEST-002'
    assert finding.category == Category.PERFORMANCE
    assert finding.severity == Severity.HIGH
    assert finding.title == 'Performance Issue'
    assert finding.description == 'Slow database query'
    assert finding.recommendation == 'Add index to table'
    assert finding.effort_estimate == 'medium'
    assert finding.file_path == 'models.py'
    assert finding.line_number == 100
    assert finding.code_snippet == 'User.objects.all()'
    assert finding.references == ['https://docs.djangoproject.com/']
    assert finding.metadata == {'query_time': '500ms'}


def test_finding_from_dict_minimal():
    """Test creating Finding from dictionary with minimal fields."""
    data = {
        'id': 'TEST-003',
        'category': 'code_quality',
        'severity': 'low',
        'title': 'Minor Issue',
        'description': 'Code style issue',
        'recommendation': 'Follow PEP 8',
        'effort_estimate': 'low'
    }
    
    finding = Finding.from_dict(data)
    
    assert finding.id == 'TEST-003'
    assert finding.category == Category.CODE_QUALITY
    assert finding.severity == Severity.LOW
    assert finding.file_path is None
    assert finding.line_number is None
    assert finding.code_snippet is None
    assert finding.references == []
    assert finding.metadata == {}


def test_finding_roundtrip():
    """Test that to_dict and from_dict are inverse operations."""
    original = Finding(
        id="TEST-004",
        category=Category.SECURITY,
        severity=Severity.CRITICAL,
        title="SQL Injection",
        description="Potential SQL injection vulnerability",
        recommendation="Use parameterized queries",
        effort_estimate="high",
        file_path="views.py",
        line_number=42,
        code_snippet='query = f"SELECT * FROM users WHERE id={user_id}"',
        references=['https://owasp.org/sql-injection'],
        metadata={'cwe': 'CWE-89'}
    )
    
    # Convert to dict and back
    finding_dict = original.to_dict()
    restored = Finding.from_dict(finding_dict)
    
    # Verify all fields match
    assert restored.id == original.id
    assert restored.category == original.category
    assert restored.severity == original.severity
    assert restored.title == original.title
    assert restored.description == original.description
    assert restored.recommendation == original.recommendation
    assert restored.effort_estimate == original.effort_estimate
    assert restored.file_path == original.file_path
    assert restored.line_number == original.line_number
    assert restored.code_snippet == original.code_snippet
    assert restored.references == original.references
    assert restored.metadata == original.metadata


def test_finding_with_all_optional_fields():
    """Test Finding with all optional fields populated."""
    finding = Finding(
        id="TEST-005",
        category=Category.ARCHITECTURE,
        severity=Severity.MEDIUM,
        title="Tight Coupling",
        description="Module has tight coupling with another module",
        recommendation="Introduce abstraction layer",
        effort_estimate="high",
        file_path="services/user_service.py",
        line_number=150,
        code_snippet="from payment.processor import PaymentProcessor",
        references=[
            'https://refactoring.guru/design-patterns',
            'https://martinfowler.com/articles/injection.html'
        ],
        metadata={
            'coupling_score': 8.5,
            'affected_modules': ['user_service', 'payment_processor']
        }
    )
    
    assert finding.file_path == "services/user_service.py"
    assert finding.line_number == 150
    assert finding.code_snippet is not None
    assert len(finding.references) == 2
    assert 'coupling_score' in finding.metadata


def test_severity_enum_values():
    """Test all Severity enum values."""
    assert Severity.CRITICAL.value == "critical"
    assert Severity.HIGH.value == "high"
    assert Severity.MEDIUM.value == "medium"
    assert Severity.LOW.value == "low"
    assert Severity.INFO.value == "info"


def test_category_enum_values():
    """Test all Category enum values."""
    assert Category.CODE_QUALITY.value == "code_quality"
    assert Category.SECURITY.value == "security"
    assert Category.PERFORMANCE.value == "performance"
    assert Category.ARCHITECTURE.value == "architecture"
    assert Category.DATABASE.value == "database"
    assert Category.API_DESIGN.value == "api_design"
    assert Category.TESTING.value == "testing"
    assert Category.INFRASTRUCTURE.value == "infrastructure"
    assert Category.DEPENDENCIES.value == "dependencies"
    assert Category.DOCUMENTATION.value == "documentation"
    assert Category.SCALABILITY.value == "scalability"


def test_effort_estimate_values():
    """Test valid effort estimate values."""
    valid_estimates = ["low", "medium", "high"]
    
    for estimate in valid_estimates:
        finding = Finding(
            id=f"TEST-{estimate}",
            category=Category.CODE_QUALITY,
            severity=Severity.LOW,
            title="Test",
            description="Test",
            recommendation="Test",
            effort_estimate=estimate
        )
        assert finding.effort_estimate == estimate


def test_analysis_result_creation():
    """Test creating an AnalysisResult object."""
    finding = Finding(
        id="TEST-001",
        category=Category.PERFORMANCE,
        severity=Severity.MEDIUM,
        title="Performance Issue",
        description="Slow query detected",
        recommendation="Add index",
        effort_estimate="low"
    )
    
    result = AnalysisResult(
        analyzer_name="test_analyzer",
        execution_time=1.5,
        findings=[finding],
        metrics={"queries_analyzed": 10},
        success=True
    )
    
    assert result.analyzer_name == "test_analyzer"
    assert result.execution_time == 1.5
    assert len(result.findings) == 1
    assert result.success is True


def test_analysis_result_get_findings_by_severity():
    """Test filtering findings by severity."""
    findings = [
        Finding(
            id="TEST-001",
            category=Category.CODE_QUALITY,
            severity=Severity.HIGH,
            title="High Issue",
            description="High severity issue",
            recommendation="Fix it",
            effort_estimate="medium"
        ),
        Finding(
            id="TEST-002",
            category=Category.CODE_QUALITY,
            severity=Severity.LOW,
            title="Low Issue",
            description="Low severity issue",
            recommendation="Fix it",
            effort_estimate="low"
        ),
        Finding(
            id="TEST-003",
            category=Category.CODE_QUALITY,
            severity=Severity.HIGH,
            title="Another High Issue",
            description="Another high severity issue",
            recommendation="Fix it",
            effort_estimate="medium"
        )
    ]
    
    result = AnalysisResult(
        analyzer_name="test",
        execution_time=1.0,
        findings=findings,
        metrics={},
        success=True
    )
    
    high_findings = result.get_findings_by_severity(Severity.HIGH)
    assert len(high_findings) == 2
    
    low_findings = result.get_findings_by_severity(Severity.LOW)
    assert len(low_findings) == 1


def test_analysis_result_get_findings_by_category():
    """Test filtering findings by category."""
    findings = [
        Finding(
            id="TEST-001",
            category=Category.SECURITY,
            severity=Severity.HIGH,
            title="Security Issue",
            description="Security problem",
            recommendation="Fix it",
            effort_estimate="high"
        ),
        Finding(
            id="TEST-002",
            category=Category.PERFORMANCE,
            severity=Severity.MEDIUM,
            title="Performance Issue",
            description="Performance problem",
            recommendation="Optimize",
            effort_estimate="medium"
        ),
        Finding(
            id="TEST-003",
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            title="Critical Security Issue",
            description="Critical security problem",
            recommendation="Fix immediately",
            effort_estimate="high"
        )
    ]
    
    result = AnalysisResult(
        analyzer_name="test",
        execution_time=1.0,
        findings=findings,
        metrics={},
        success=True
    )
    
    security_findings = result.get_findings_by_category(Category.SECURITY)
    assert len(security_findings) == 2
    
    performance_findings = result.get_findings_by_category(Category.PERFORMANCE)
    assert len(performance_findings) == 1


def test_analysis_result_get_severity_counts():
    """Test getting count of findings by severity."""
    findings = [
        Finding(
            id="TEST-001",
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            title="Critical Issue",
            description="Critical",
            recommendation="Fix",
            effort_estimate="high"
        ),
        Finding(
            id="TEST-002",
            category=Category.SECURITY,
            severity=Severity.HIGH,
            title="High Issue",
            description="High",
            recommendation="Fix",
            effort_estimate="medium"
        ),
        Finding(
            id="TEST-003",
            category=Category.PERFORMANCE,
            severity=Severity.HIGH,
            title="Another High Issue",
            description="High",
            recommendation="Fix",
            effort_estimate="medium"
        ),
        Finding(
            id="TEST-004",
            category=Category.CODE_QUALITY,
            severity=Severity.MEDIUM,
            title="Medium Issue",
            description="Medium",
            recommendation="Fix",
            effort_estimate="low"
        ),
        Finding(
            id="TEST-005",
            category=Category.CODE_QUALITY,
            severity=Severity.LOW,
            title="Low Issue",
            description="Low",
            recommendation="Fix",
            effort_estimate="low"
        )
    ]
    
    result = AnalysisResult(
        analyzer_name="test",
        execution_time=1.0,
        findings=findings,
        metrics={},
        success=True
    )
    
    severity_counts = result.get_severity_counts()
    
    assert severity_counts[Severity.CRITICAL] == 1
    assert severity_counts[Severity.HIGH] == 2
    assert severity_counts[Severity.MEDIUM] == 1
    assert severity_counts[Severity.LOW] == 1
    assert severity_counts[Severity.INFO] == 0


def test_analysis_result_get_category_counts():
    """Test getting count of findings by category."""
    findings = [
        Finding(
            id="TEST-001",
            category=Category.SECURITY,
            severity=Severity.HIGH,
            title="Security Issue 1",
            description="Security",
            recommendation="Fix",
            effort_estimate="high"
        ),
        Finding(
            id="TEST-002",
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            title="Security Issue 2",
            description="Security",
            recommendation="Fix",
            effort_estimate="high"
        ),
        Finding(
            id="TEST-003",
            category=Category.PERFORMANCE,
            severity=Severity.MEDIUM,
            title="Performance Issue",
            description="Performance",
            recommendation="Optimize",
            effort_estimate="medium"
        ),
        Finding(
            id="TEST-004",
            category=Category.CODE_QUALITY,
            severity=Severity.LOW,
            title="Code Quality Issue",
            description="Code quality",
            recommendation="Refactor",
            effort_estimate="low"
        )
    ]
    
    result = AnalysisResult(
        analyzer_name="test",
        execution_time=1.0,
        findings=findings,
        metrics={},
        success=True
    )
    
    category_counts = result.get_category_counts()
    
    assert category_counts[Category.SECURITY] == 2
    assert category_counts[Category.PERFORMANCE] == 1
    assert category_counts[Category.CODE_QUALITY] == 1
    assert category_counts[Category.ARCHITECTURE] == 0
    assert category_counts[Category.DATABASE] == 0


def test_analysis_result_get_total_findings():
    """Test getting total number of findings."""
    findings = [
        Finding(
            id=f"TEST-{i:03d}",
            category=Category.CODE_QUALITY,
            severity=Severity.LOW,
            title=f"Issue {i}",
            description="Test",
            recommendation="Fix",
            effort_estimate="low"
        )
        for i in range(1, 6)
    ]
    
    result = AnalysisResult(
        analyzer_name="test",
        execution_time=1.0,
        findings=findings,
        metrics={},
        success=True
    )
    
    assert result.get_total_findings() == 5


def test_analysis_result_get_total_findings_empty():
    """Test getting total findings when there are none."""
    result = AnalysisResult(
        analyzer_name="test",
        execution_time=1.0,
        findings=[],
        metrics={},
        success=True
    )
    
    assert result.get_total_findings() == 0


def test_analysis_result_has_critical_findings():
    """Test checking for critical findings."""
    # Result with critical finding
    findings_with_critical = [
        Finding(
            id="TEST-001",
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            title="Critical Issue",
            description="Critical",
            recommendation="Fix now",
            effort_estimate="high"
        ),
        Finding(
            id="TEST-002",
            category=Category.CODE_QUALITY,
            severity=Severity.LOW,
            title="Low Issue",
            description="Low",
            recommendation="Fix later",
            effort_estimate="low"
        )
    ]
    
    result_with_critical = AnalysisResult(
        analyzer_name="test",
        execution_time=1.0,
        findings=findings_with_critical,
        metrics={},
        success=True
    )
    
    assert result_with_critical.has_critical_findings() is True
    
    # Result without critical finding
    findings_without_critical = [
        Finding(
            id="TEST-003",
            category=Category.CODE_QUALITY,
            severity=Severity.HIGH,
            title="High Issue",
            description="High",
            recommendation="Fix",
            effort_estimate="medium"
        ),
        Finding(
            id="TEST-004",
            category=Category.CODE_QUALITY,
            severity=Severity.LOW,
            title="Low Issue",
            description="Low",
            recommendation="Fix",
            effort_estimate="low"
        )
    ]
    
    result_without_critical = AnalysisResult(
        analyzer_name="test",
        execution_time=1.0,
        findings=findings_without_critical,
        metrics={},
        success=True
    )
    
    assert result_without_critical.has_critical_findings() is False


def test_analysis_result_has_critical_findings_empty():
    """Test checking for critical findings when there are no findings."""
    result = AnalysisResult(
        analyzer_name="test",
        execution_time=1.0,
        findings=[],
        metrics={},
        success=True
    )
    
    assert result.has_critical_findings() is False


def test_analysis_result_get_findings_by_effort():
    """Test filtering findings by effort estimate."""
    findings = [
        Finding(
            id="TEST-001",
            category=Category.SECURITY,
            severity=Severity.CRITICAL,
            title="Critical Issue",
            description="Critical",
            recommendation="Fix",
            effort_estimate="high"
        ),
        Finding(
            id="TEST-002",
            category=Category.PERFORMANCE,
            severity=Severity.MEDIUM,
            title="Medium Issue",
            description="Medium",
            recommendation="Optimize",
            effort_estimate="medium"
        ),
        Finding(
            id="TEST-003",
            category=Category.CODE_QUALITY,
            severity=Severity.LOW,
            title="Low Issue 1",
            description="Low",
            recommendation="Fix",
            effort_estimate="low"
        ),
        Finding(
            id="TEST-004",
            category=Category.CODE_QUALITY,
            severity=Severity.LOW,
            title="Low Issue 2",
            description="Low",
            recommendation="Fix",
            effort_estimate="low"
        ),
        Finding(
            id="TEST-005",
            category=Category.SECURITY,
            severity=Severity.HIGH,
            title="High Issue",
            description="High",
            recommendation="Fix",
            effort_estimate="high"
        )
    ]
    
    result = AnalysisResult(
        analyzer_name="test",
        execution_time=1.0,
        findings=findings,
        metrics={},
        success=True
    )
    
    high_effort = result.get_findings_by_effort("high")
    assert len(high_effort) == 2
    assert all(f.effort_estimate == "high" for f in high_effort)
    
    medium_effort = result.get_findings_by_effort("medium")
    assert len(medium_effort) == 1
    assert medium_effort[0].effort_estimate == "medium"
    
    low_effort = result.get_findings_by_effort("low")
    assert len(low_effort) == 2
    assert all(f.effort_estimate == "low" for f in low_effort)


def test_analysis_result_get_findings_by_effort_empty():
    """Test filtering by effort when no findings match."""
    findings = [
        Finding(
            id="TEST-001",
            category=Category.CODE_QUALITY,
            severity=Severity.LOW,
            title="Low Issue",
            description="Low",
            recommendation="Fix",
            effort_estimate="low"
        )
    ]
    
    result = AnalysisResult(
        analyzer_name="test",
        execution_time=1.0,
        findings=findings,
        metrics={},
        success=True
    )
    
    high_effort = result.get_findings_by_effort("high")
    assert len(high_effort) == 0
    assert high_effort == []


def test_audit_summary_creation():
    """Test creating an AuditSummary object."""
    finding = Finding(
        id="TEST-001",
        category=Category.CODE_QUALITY,
        severity=Severity.HIGH,
        title="Test Finding",
        description="Test",
        recommendation="Fix",
        effort_estimate="low"
    )
    
    summary = AuditSummary(
        total_findings=5,
        findings_by_severity={"high": 2, "medium": 3},
        findings_by_category={"code_quality": 3, "security": 2},
        overall_score=85.0,
        category_scores={"code_quality": 80.0, "security": 90.0},
        key_findings=[finding]
    )
    
    assert summary.total_findings == 5
    assert summary.overall_score == 85.0
    assert len(summary.key_findings) == 1


def test_action_plan_creation():
    """Test creating an ActionPlan object."""
    finding = Finding(
        id="TEST-001",
        category=Category.SECURITY,
        severity=Severity.CRITICAL,
        title="Critical Issue",
        description="Critical security issue",
        recommendation="Fix now",
        effort_estimate="high"
    )
    
    action_plan = ActionPlan(
        quick_wins=[],
        critical_issues=[finding],
        short_term=[],
        long_term=[],
        technical_debt=[]
    )
    
    assert len(action_plan.critical_issues) == 1
    assert action_plan.critical_issues[0].severity == Severity.CRITICAL


def test_audit_report_creation():
    """Test creating an AuditReport object."""
    finding = Finding(
        id="TEST-001",
        category=Category.CODE_QUALITY,
        severity=Severity.MEDIUM,
        title="Test",
        description="Test",
        recommendation="Fix",
        effort_estimate="low"
    )
    
    result = AnalysisResult(
        analyzer_name="test",
        execution_time=1.0,
        findings=[finding],
        metrics={},
        success=True
    )
    
    summary = AuditSummary(
        total_findings=1,
        findings_by_severity={"medium": 1},
        findings_by_category={"code_quality": 1},
        overall_score=95.0,
        category_scores={"code_quality": 95.0},
        key_findings=[finding]
    )
    
    action_plan = ActionPlan(
        quick_wins=[],
        critical_issues=[],
        short_term=[],
        long_term=[finding],
        technical_debt=[]
    )
    
    report = AuditReport(
        timestamp="2024-01-01T00:00:00",
        project_name="test_project",
        project_version="1.0.0",
        execution_time=5.0,
        results={"test": result},
        summary=summary,
        action_plan=action_plan
    )
    
    assert report.project_name == "test_project"
    assert report.execution_time == 5.0
    assert len(report.results) == 1


def test_audit_report_to_dict():
    """Test converting AuditReport to dictionary."""
    finding = Finding(
        id="TEST-001",
        category=Category.CODE_QUALITY,
        severity=Severity.LOW,
        title="Test",
        description="Test",
        recommendation="Fix",
        effort_estimate="low"
    )
    
    result = AnalysisResult(
        analyzer_name="test",
        execution_time=1.0,
        findings=[finding],
        metrics={},
        success=True
    )
    
    summary = AuditSummary(
        total_findings=1,
        findings_by_severity={"low": 1},
        findings_by_category={"code_quality": 1},
        overall_score=99.0,
        category_scores={"code_quality": 99.0},
        key_findings=[finding]
    )
    
    action_plan = ActionPlan(
        quick_wins=[],
        critical_issues=[],
        short_term=[],
        long_term=[],
        technical_debt=[finding]
    )
    
    report = AuditReport(
        timestamp="2024-01-01T00:00:00",
        project_name="test",
        project_version="1.0.0",
        execution_time=1.0,
        results={"test": result},
        summary=summary,
        action_plan=action_plan
    )
    
    report_dict = report.to_dict()
    
    assert isinstance(report_dict, dict)
    assert report_dict['project_name'] == "test"
    assert 'results' in report_dict
    assert 'summary' in report_dict
    assert 'action_plan' in report_dict



def test_analysis_result_to_dict():
    """Test converting AnalysisResult to dictionary."""
    finding = Finding(
        id="TEST-001",
        category=Category.SECURITY,
        severity=Severity.HIGH,
        title="Security Issue",
        description="Security problem",
        recommendation="Fix it",
        effort_estimate="high"
    )
    
    result = AnalysisResult(
        analyzer_name="security_scanner",
        execution_time=2.5,
        findings=[finding],
        metrics={"scanned_files": 100},
        success=True
    )
    
    result_dict = result.to_dict()
    
    assert isinstance(result_dict, dict)
    assert result_dict['analyzer_name'] == "security_scanner"
    assert result_dict['execution_time'] == 2.5
    assert result_dict['success'] is True
    assert len(result_dict['findings']) == 1
    assert result_dict['metrics'] == {"scanned_files": 100}
    assert result_dict['error_message'] is None


def test_analysis_result_to_dict_with_error():
    """Test converting AnalysisResult with error to dictionary."""
    result = AnalysisResult(
        analyzer_name="failed_analyzer",
        execution_time=0.5,
        findings=[],
        metrics={},
        success=False,
        error_message="Tool execution failed"
    )
    
    result_dict = result.to_dict()
    
    assert result_dict['success'] is False
    assert result_dict['error_message'] == "Tool execution failed"


def test_audit_summary_to_dict():
    """Test converting AuditSummary to dictionary."""
    finding = Finding(
        id="TEST-001",
        category=Category.CODE_QUALITY,
        severity=Severity.MEDIUM,
        title="Code Quality Issue",
        description="Test",
        recommendation="Fix",
        effort_estimate="low"
    )
    
    summary = AuditSummary(
        total_findings=10,
        findings_by_severity={"critical": 1, "high": 3, "medium": 4, "low": 2},
        findings_by_category={"code_quality": 5, "security": 3, "performance": 2},
        overall_score=78.5,
        category_scores={"code_quality": 75.0, "security": 80.0, "performance": 82.0},
        key_findings=[finding]
    )
    
    summary_dict = summary.to_dict()
    
    assert isinstance(summary_dict, dict)
    assert summary_dict['total_findings'] == 10
    assert summary_dict['overall_score'] == 78.5
    assert len(summary_dict['key_findings']) == 1
    assert summary_dict['findings_by_severity'] == {"critical": 1, "high": 3, "medium": 4, "low": 2}
    assert summary_dict['findings_by_category'] == {"code_quality": 5, "security": 3, "performance": 2}


def test_action_plan_to_dict():
    """Test converting ActionPlan to dictionary."""
    critical_finding = Finding(
        id="TEST-001",
        category=Category.SECURITY,
        severity=Severity.CRITICAL,
        title="Critical Security Issue",
        description="Critical",
        recommendation="Fix now",
        effort_estimate="high"
    )
    
    quick_win = Finding(
        id="TEST-002",
        category=Category.CODE_QUALITY,
        severity=Severity.LOW,
        title="Quick Fix",
        description="Easy fix",
        recommendation="Fix quickly",
        effort_estimate="low"
    )
    
    action_plan = ActionPlan(
        quick_wins=[quick_win],
        critical_issues=[critical_finding],
        short_term=[],
        long_term=[],
        technical_debt=[]
    )
    
    plan_dict = action_plan.to_dict()
    
    assert isinstance(plan_dict, dict)
    assert len(plan_dict['quick_wins']) == 1
    assert len(plan_dict['critical_issues']) == 1
    assert len(plan_dict['short_term']) == 0
    assert len(plan_dict['long_term']) == 0
    assert len(plan_dict['technical_debt']) == 0


def test_audit_report_export_json(tmp_path):
    """Test exporting AuditReport as JSON."""
    import json
    
    finding = Finding(
        id="TEST-001",
        category=Category.CODE_QUALITY,
        severity=Severity.MEDIUM,
        title="Test Finding",
        description="Test description",
        recommendation="Fix it",
        effort_estimate="low"
    )
    
    result = AnalysisResult(
        analyzer_name="test_analyzer",
        execution_time=1.0,
        findings=[finding],
        metrics={"files_analyzed": 50},
        success=True
    )
    
    summary = AuditSummary(
        total_findings=1,
        findings_by_severity={"medium": 1},
        findings_by_category={"code_quality": 1},
        overall_score=95.0,
        category_scores={"code_quality": 95.0},
        key_findings=[finding]
    )
    
    action_plan = ActionPlan(
        quick_wins=[],
        critical_issues=[],
        short_term=[],
        long_term=[finding],
        technical_debt=[]
    )
    
    report = AuditReport(
        timestamp="2024-01-01T00:00:00",
        project_name="test_project",
        project_version="1.0.0",
        execution_time=5.0,
        results={"test_analyzer": result},
        summary=summary,
        action_plan=action_plan
    )
    
    output_path = tmp_path / "report.json"
    report.export_json(str(output_path))
    
    # Verify file was created
    assert output_path.exists()
    
    # Verify content is valid JSON
    with open(output_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data['project_name'] == "test_project"
    assert data['project_version'] == "1.0.0"
    assert 'results' in data
    assert 'summary' in data
    assert 'action_plan' in data


def test_audit_report_export_json_creates_directory(tmp_path):
    """Test that export_json creates parent directories if they don't exist."""
    import json
    
    finding = Finding(
        id="TEST-001",
        category=Category.CODE_QUALITY,
        severity=Severity.LOW,
        title="Test",
        description="Test",
        recommendation="Fix",
        effort_estimate="low"
    )
    
    result = AnalysisResult(
        analyzer_name="test",
        execution_time=1.0,
        findings=[finding],
        metrics={},
        success=True
    )
    
    summary = AuditSummary(
        total_findings=1,
        findings_by_severity={"low": 1},
        findings_by_category={"code_quality": 1},
        overall_score=99.0,
        category_scores={"code_quality": 99.0},
        key_findings=[finding]
    )
    
    action_plan = ActionPlan(
        quick_wins=[],
        critical_issues=[],
        short_term=[],
        long_term=[],
        technical_debt=[finding]
    )
    
    report = AuditReport(
        timestamp="2024-01-01T00:00:00",
        project_name="test",
        project_version="1.0.0",
        execution_time=1.0,
        results={"test": result},
        summary=summary,
        action_plan=action_plan
    )
    
    # Use nested directory that doesn't exist
    output_path = tmp_path / "reports" / "2024" / "report.json"
    report.export_json(str(output_path))
    
    assert output_path.exists()
    
    with open(output_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data['project_name'] == "test"


def test_audit_report_export_markdown(tmp_path):
    """Test exporting AuditReport as Markdown."""
    finding = Finding(
        id="TEST-001",
        category=Category.SECURITY,
        severity=Severity.HIGH,
        title="Security Vulnerability",
        description="SQL injection vulnerability detected",
        recommendation="Use parameterized queries",
        effort_estimate="medium",
        file_path="views.py",
        line_number=42
    )
    
    result = AnalysisResult(
        analyzer_name="security_scanner",
        execution_time=2.5,
        findings=[finding],
        metrics={"files_scanned": 100, "vulnerabilities_found": 1},
        success=True
    )
    
    summary = AuditSummary(
        total_findings=1,
        findings_by_severity={"high": 1},
        findings_by_category={"security": 1},
        overall_score=85.0,
        category_scores={"security": 85.0},
        key_findings=[finding]
    )
    
    action_plan = ActionPlan(
        quick_wins=[],
        critical_issues=[],
        short_term=[finding],
        long_term=[],
        technical_debt=[]
    )
    
    report = AuditReport(
        timestamp="2024-01-01T12:00:00",
        project_name="MyProject",
        project_version="2.0.0",
        execution_time=10.5,
        results={"security_scanner": result},
        summary=summary,
        action_plan=action_plan
    )
    
    output_path = tmp_path / "report.md"
    report.export_markdown(str(output_path))
    
    # Verify file was created
    assert output_path.exists()
    
    # Verify content
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert "# Audit Report: MyProject" in content
    assert "**Version:** 2.0.0" in content
    assert "**Date:** 2024-01-01T12:00:00" in content
    assert "**Execution Time:** 10.50s" in content
    assert "## Executive Summary" in content
    assert "**Overall Score:** 85.0/100" in content
    assert "**Total Findings:** 1" in content
    assert "Security Vulnerability" in content
    assert "SQL injection vulnerability detected" in content
    assert "Use parameterized queries" in content
    assert "`views.py:42`" in content


def test_audit_report_export_markdown_creates_directory(tmp_path):
    """Test that export_markdown creates parent directories if they don't exist."""
    finding = Finding(
        id="TEST-001",
        category=Category.CODE_QUALITY,
        severity=Severity.LOW,
        title="Test",
        description="Test",
        recommendation="Fix",
        effort_estimate="low"
    )
    
    result = AnalysisResult(
        analyzer_name="test",
        execution_time=1.0,
        findings=[finding],
        metrics={},
        success=True
    )
    
    summary = AuditSummary(
        total_findings=1,
        findings_by_severity={"low": 1},
        findings_by_category={"code_quality": 1},
        overall_score=99.0,
        category_scores={"code_quality": 99.0},
        key_findings=[finding]
    )
    
    action_plan = ActionPlan(
        quick_wins=[],
        critical_issues=[],
        short_term=[],
        long_term=[],
        technical_debt=[finding]
    )
    
    report = AuditReport(
        timestamp="2024-01-01T00:00:00",
        project_name="test",
        project_version="1.0.0",
        execution_time=1.0,
        results={"test": result},
        summary=summary,
        action_plan=action_plan
    )
    
    # Use nested directory that doesn't exist
    output_path = tmp_path / "reports" / "markdown" / "report.md"
    report.export_markdown(str(output_path))
    
    assert output_path.exists()


def test_audit_report_export_html(tmp_path):
    """Test exporting AuditReport as HTML."""
    finding = Finding(
        id="TEST-001",
        category=Category.PERFORMANCE,
        severity=Severity.MEDIUM,
        title="N+1 Query Detected",
        description="Database query in loop without prefetch",
        recommendation="Use select_related or prefetch_related",
        effort_estimate="medium",
        file_path="models.py",
        line_number=100
    )
    
    result = AnalysisResult(
        analyzer_name="performance_profiler",
        execution_time=3.0,
        findings=[finding],
        metrics={"queries_analyzed": 50, "n_plus_one_found": 1},
        success=True
    )
    
    summary = AuditSummary(
        total_findings=1,
        findings_by_severity={"medium": 1},
        findings_by_category={"performance": 1},
        overall_score=90.0,
        category_scores={"performance": 90.0},
        key_findings=[finding]
    )
    
    action_plan = ActionPlan(
        quick_wins=[finding],
        critical_issues=[],
        short_term=[],
        long_term=[],
        technical_debt=[]
    )
    
    report = AuditReport(
        timestamp="2024-01-01T15:30:00",
        project_name="WebApp",
        project_version="3.1.0",
        execution_time=15.0,
        results={"performance_profiler": result},
        summary=summary,
        action_plan=action_plan
    )
    
    output_path = tmp_path / "report.html"
    report.export_html(str(output_path))
    
    # Verify file was created
    assert output_path.exists()
    
    # Verify content
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert "<!DOCTYPE html>" in content
    assert "<html lang=\"en\">" in content
    assert "<title>Audit Report: WebApp</title>" in content
    assert "WebApp" in content
    assert "3.1.0" in content
    assert "2024-01-01T15:30:00" in content
    assert "15.00s" in content
    assert "Executive Summary" in content
    assert "90.0/100" in content
    assert "N+1 Query Detected" in content
    assert "Database query in loop without prefetch" in content
    assert "Use select_related or prefetch_related" in content
    assert "models.py:100" in content
    assert "Quick Wins" in content


def test_audit_report_export_html_creates_directory(tmp_path):
    """Test that export_html creates parent directories if they don't exist."""
    finding = Finding(
        id="TEST-001",
        category=Category.CODE_QUALITY,
        severity=Severity.LOW,
        title="Test",
        description="Test",
        recommendation="Fix",
        effort_estimate="low"
    )
    
    result = AnalysisResult(
        analyzer_name="test",
        execution_time=1.0,
        findings=[finding],
        metrics={},
        success=True
    )
    
    summary = AuditSummary(
        total_findings=1,
        findings_by_severity={"low": 1},
        findings_by_category={"code_quality": 1},
        overall_score=99.0,
        category_scores={"code_quality": 99.0},
        key_findings=[finding]
    )
    
    action_plan = ActionPlan(
        quick_wins=[],
        critical_issues=[],
        short_term=[],
        long_term=[],
        technical_debt=[finding]
    )
    
    report = AuditReport(
        timestamp="2024-01-01T00:00:00",
        project_name="test",
        project_version="1.0.0",
        execution_time=1.0,
        results={"test": result},
        summary=summary,
        action_plan=action_plan
    )
    
    # Use nested directory that doesn't exist
    output_path = tmp_path / "reports" / "html" / "report.html"
    report.export_html(str(output_path))
    
    assert output_path.exists()


def test_audit_report_export_all_formats(tmp_path):
    """Test exporting AuditReport in all formats."""
    finding = Finding(
        id="TEST-001",
        category=Category.CODE_QUALITY,
        severity=Severity.MEDIUM,
        title="Code Quality Issue",
        description="Test issue",
        recommendation="Fix it",
        effort_estimate="low"
    )
    
    result = AnalysisResult(
        analyzer_name="code_quality_analyzer",
        execution_time=2.0,
        findings=[finding],
        metrics={"files_analyzed": 100},
        success=True
    )
    
    summary = AuditSummary(
        total_findings=1,
        findings_by_severity={"medium": 1},
        findings_by_category={"code_quality": 1},
        overall_score=92.0,
        category_scores={"code_quality": 92.0},
        key_findings=[finding]
    )
    
    action_plan = ActionPlan(
        quick_wins=[],
        critical_issues=[],
        short_term=[finding],
        long_term=[],
        technical_debt=[]
    )
    
    report = AuditReport(
        timestamp="2024-01-01T00:00:00",
        project_name="TestProject",
        project_version="1.0.0",
        execution_time=5.0,
        results={"code_quality_analyzer": result},
        summary=summary,
        action_plan=action_plan
    )
    
    # Export in all formats
    json_path = tmp_path / "report.json"
    md_path = tmp_path / "report.md"
    html_path = tmp_path / "report.html"
    
    report.export_json(str(json_path))
    report.export_markdown(str(md_path))
    report.export_html(str(html_path))
    
    # Verify all files were created
    assert json_path.exists()
    assert md_path.exists()
    assert html_path.exists()
    
    # Verify all contain project name
    with open(json_path, 'r', encoding='utf-8') as f:
        assert "TestProject" in f.read()
    
    with open(md_path, 'r', encoding='utf-8') as f:
        assert "TestProject" in f.read()
    
    with open(html_path, 'r', encoding='utf-8') as f:
        assert "TestProject" in f.read()


def test_audit_report_with_multiple_analyzers(tmp_path):
    """Test AuditReport with multiple analyzer results."""
    security_finding = Finding(
        id="SEC-001",
        category=Category.SECURITY,
        severity=Severity.CRITICAL,
        title="SQL Injection",
        description="SQL injection vulnerability",
        recommendation="Use parameterized queries",
        effort_estimate="high"
    )
    
    performance_finding = Finding(
        id="PERF-001",
        category=Category.PERFORMANCE,
        severity=Severity.MEDIUM,
        title="Slow Query",
        description="Query takes too long",
        recommendation="Add index",
        effort_estimate="low"
    )
    
    security_result = AnalysisResult(
        analyzer_name="security_scanner",
        execution_time=2.0,
        findings=[security_finding],
        metrics={"files_scanned": 50},
        success=True
    )
    
    performance_result = AnalysisResult(
        analyzer_name="performance_profiler",
        execution_time=3.0,
        findings=[performance_finding],
        metrics={"queries_analyzed": 100},
        success=True
    )
    
    summary = AuditSummary(
        total_findings=2,
        findings_by_severity={"critical": 1, "medium": 1},
        findings_by_category={"security": 1, "performance": 1},
        overall_score=80.0,
        category_scores={"security": 75.0, "performance": 85.0},
        key_findings=[security_finding, performance_finding]
    )
    
    action_plan = ActionPlan(
        quick_wins=[performance_finding],
        critical_issues=[security_finding],
        short_term=[],
        long_term=[],
        technical_debt=[]
    )
    
    report = AuditReport(
        timestamp="2024-01-01T00:00:00",
        project_name="MultiAnalyzer",
        project_version="1.0.0",
        execution_time=5.0,
        results={
            "security_scanner": security_result,
            "performance_profiler": performance_result
        },
        summary=summary,
        action_plan=action_plan
    )
    
    # Test JSON export
    json_path = tmp_path / "multi.json"
    report.export_json(str(json_path))
    
    import json
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert len(data['results']) == 2
    assert 'security_scanner' in data['results']
    assert 'performance_profiler' in data['results']
    
    # Test Markdown export
    md_path = tmp_path / "multi.md"
    report.export_markdown(str(md_path))
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert "Security Scanner" in content
    assert "Performance Profiler" in content
    assert "SQL Injection" in content
    assert "Slow Query" in content
