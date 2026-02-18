"""Data models for the audit system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid


class Severity(Enum):
    """Severity levels for findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Category(Enum):
    """Categories for findings."""
    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    DATABASE = "database"
    API_DESIGN = "api_design"
    TESTING = "testing"
    INFRASTRUCTURE = "infrastructure"
    DEPENDENCIES = "dependencies"
    DOCUMENTATION = "documentation"
    SCALABILITY = "scalability"


@dataclass
class Finding:
    """Represents a single audit finding."""
    
    category: Category
    severity: Severity
    title: str
    description: str
    recommendation: str
    effort_estimate: str  # "low", "medium", "high"
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary."""
        return {
            'id': self.id,
            'category': self.category.value,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'recommendation': self.recommendation,
            'effort_estimate': self.effort_estimate,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'code_snippet': self.code_snippet,
            'references': self.references,
            'metadata': self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Finding':
        """Create finding from dictionary."""
        return cls(
            id=data['id'],
            category=Category(data['category']),
            severity=Severity(data['severity']),
            title=data['title'],
            description=data['description'],
            recommendation=data['recommendation'],
            effort_estimate=data['effort_estimate'],
            file_path=data.get('file_path'),
            line_number=data.get('line_number'),
            code_snippet=data.get('code_snippet'),
            references=data.get('references', []),
            metadata=data.get('metadata', {}),
        )


@dataclass
class AnalysisResult:
    """Results from a single analyzer."""
    
    analyzer_name: str
    findings: List[Finding]
    metrics: Dict[str, Any]
    success: bool
    execution_time: float = 0.0
    error_message: Optional[str] = None
    
    def get_findings_by_severity(self, severity: Severity) -> List[Finding]:
        """Get findings filtered by severity."""
        return [f for f in self.findings if f.severity == severity]
    
    def get_findings_by_category(self, category: Category) -> List[Finding]:
        """Get findings filtered by category."""
        return [f for f in self.findings if f.category == category]
    
    def get_severity_counts(self) -> Dict[Severity, int]:
        """Get count of findings by severity level."""
        counts = {severity: 0 for severity in Severity}
        for finding in self.findings:
            counts[finding.severity] += 1
        return counts
    
    def get_category_counts(self) -> Dict[Category, int]:
        """Get count of findings by category."""
        counts = {category: 0 for category in Category}
        for finding in self.findings:
            counts[finding.category] += 1
        return counts
    
    def get_total_findings(self) -> int:
        """Get total number of findings."""
        return len(self.findings)
    
    def has_critical_findings(self) -> bool:
        """Check if there are any critical severity findings."""
        return any(f.severity == Severity.CRITICAL for f in self.findings)
    
    def get_findings_by_effort(self, effort: str) -> List[Finding]:
        """Get findings filtered by effort estimate.
        
        Args:
            effort: One of "low", "medium", or "high"
        """
        return [f for f in self.findings if f.effort_estimate == effort]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'analyzer_name': self.analyzer_name,
            'execution_time': self.execution_time,
            'findings': [f.to_dict() for f in self.findings],
            'metrics': self.metrics,
            'success': self.success,
            'error_message': self.error_message,
        }


@dataclass
class AuditSummary:
    """Executive summary of audit results."""
    
    total_findings: int
    findings_by_severity: Dict[str, int]
    findings_by_category: Dict[str, int]
    overall_score: float  # 0-100
    category_scores: Dict[str, float]
    key_findings: List[Finding]  # Top 10 most important
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary."""
        return {
            'total_findings': self.total_findings,
            'findings_by_severity': self.findings_by_severity,
            'findings_by_category': self.findings_by_category,
            'overall_score': self.overall_score,
            'category_scores': self.category_scores,
            'key_findings': [f.to_dict() for f in self.key_findings],
        }


@dataclass
class ActionPlan:
    """Prioritized action plan."""
    
    quick_wins: List[Finding]  # Low effort, high impact
    critical_issues: List[Finding]  # Must fix immediately
    short_term: List[Finding]  # Fix within 1-2 sprints
    long_term: List[Finding]  # Fix within 3-6 months
    technical_debt: List[Finding]  # Ongoing refactoring
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert action plan to dictionary."""
        return {
            'quick_wins': [f.to_dict() for f in self.quick_wins],
            'critical_issues': [f.to_dict() for f in self.critical_issues],
            'short_term': [f.to_dict() for f in self.short_term],
            'long_term': [f.to_dict() for f in self.long_term],
            'technical_debt': [f.to_dict() for f in self.technical_debt],
        }


@dataclass
class AuditReport:
    """Complete audit report."""
    
    timestamp: str
    project_name: str
    project_version: str
    execution_time: float
    results: Dict[str, AnalysisResult]
    summary: AuditSummary
    action_plan: ActionPlan
    
    def export_json(self, output_path: str) -> None:
        """Export report as JSON.
        
        Args:
            output_path: Path to write the JSON file
        """
        import json
        from pathlib import Path
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    def export_markdown(self, output_path: str) -> None:
        """Export report as Markdown.
        
        Args:
            output_path: Path to write the Markdown file
        """
        from pathlib import Path
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        lines = []
        lines.append(f"# Audit Report: {self.project_name}")
        lines.append(f"\n**Version:** {self.project_version}")
        lines.append(f"**Date:** {self.timestamp}")
        lines.append(f"**Execution Time:** {self.execution_time:.2f}s\n")
        
        # Executive Summary
        lines.append("## Executive Summary\n")
        lines.append(f"**Overall Score:** {self.summary.overall_score:.1f}/100")
        lines.append(f"**Total Findings:** {self.summary.total_findings}\n")
        
        # Findings by Severity
        lines.append("### Findings by Severity\n")
        for severity, count in sorted(self.summary.findings_by_severity.items()):
            lines.append(f"- **{severity.title()}:** {count}")
        
        # Findings by Category
        lines.append("\n### Findings by Category\n")
        for category, count in sorted(self.summary.findings_by_category.items()):
            lines.append(f"- **{category.replace('_', ' ').title()}:** {count}")
        
        # Category Scores
        lines.append("\n### Category Scores\n")
        for category, score in sorted(self.summary.category_scores.items()):
            lines.append(f"- **{category.replace('_', ' ').title()}:** {score:.1f}/100")
        
        # Key Findings
        if self.summary.key_findings:
            lines.append("\n### Key Findings\n")
            for i, finding in enumerate(self.summary.key_findings[:10], 1):
                lines.append(f"\n#### {i}. {finding.title}")
                lines.append(f"**Severity:** {finding.severity.value.title()} | "
                           f"**Category:** {finding.category.value.replace('_', ' ').title()} | "
                           f"**Effort:** {finding.effort_estimate.title()}")
                lines.append(f"\n{finding.description}")
                if finding.file_path:
                    location = f"{finding.file_path}"
                    if finding.line_number:
                        location += f":{finding.line_number}"
                    lines.append(f"\n**Location:** `{location}`")
                lines.append(f"\n**Recommendation:** {finding.recommendation}")
        
        # Action Plan
        lines.append("\n## Action Plan\n")
        
        if self.action_plan.critical_issues:
            lines.append(f"### Critical Issues ({len(self.action_plan.critical_issues)})\n")
            lines.append("*Must fix immediately*\n")
            for finding in self.action_plan.critical_issues:
                lines.append(f"- **{finding.title}** ({finding.category.value})")
                if finding.file_path:
                    lines.append(f"  - Location: `{finding.file_path}`")
                lines.append(f"  - {finding.recommendation}")
        
        if self.action_plan.quick_wins:
            lines.append(f"\n### Quick Wins ({len(self.action_plan.quick_wins)})\n")
            lines.append("*Low effort, high impact*\n")
            for finding in self.action_plan.quick_wins:
                lines.append(f"- **{finding.title}** ({finding.category.value})")
                lines.append(f"  - {finding.recommendation}")
        
        if self.action_plan.short_term:
            lines.append(f"\n### Short Term ({len(self.action_plan.short_term)})\n")
            lines.append("*Fix within 1-2 sprints*\n")
            for finding in self.action_plan.short_term:
                lines.append(f"- **{finding.title}** ({finding.category.value})")
        
        if self.action_plan.long_term:
            lines.append(f"\n### Long Term ({len(self.action_plan.long_term)})\n")
            lines.append("*Fix within 3-6 months*\n")
            for finding in self.action_plan.long_term:
                lines.append(f"- **{finding.title}** ({finding.category.value})")
        
        if self.action_plan.technical_debt:
            lines.append(f"\n### Technical Debt ({len(self.action_plan.technical_debt)})\n")
            lines.append("*Ongoing refactoring*\n")
            for finding in self.action_plan.technical_debt:
                lines.append(f"- **{finding.title}** ({finding.category.value})")
        
        # Detailed Results
        lines.append("\n## Detailed Results\n")
        for analyzer_name, result in sorted(self.results.items()):
            lines.append(f"\n### {analyzer_name.replace('_', ' ').title()}")
            lines.append(f"\n**Execution Time:** {result.execution_time:.2f}s")
            lines.append(f"**Status:** {'✓ Success' if result.success else '✗ Failed'}")
            lines.append(f"**Findings:** {len(result.findings)}")
            
            if result.error_message:
                lines.append(f"\n**Error:** {result.error_message}")
            
            if result.metrics:
                lines.append("\n**Metrics:**")
                for key, value in result.metrics.items():
                    lines.append(f"- {key.replace('_', ' ').title()}: {value}")
            
            if result.findings:
                lines.append("\n**Issues Found:**\n")
                for finding in result.findings:
                    lines.append(f"- [{finding.severity.value.upper()}] {finding.title}")
                    if finding.file_path:
                        location = f"{finding.file_path}"
                        if finding.line_number:
                            location += f":{finding.line_number}"
                        lines.append(f"  - Location: `{location}`")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def export_html(self, output_path: str) -> None:
        """Export report as HTML.
        
        Args:
            output_path: Path to write the HTML file
        """
        from pathlib import Path
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Severity color mapping
        severity_colors = {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745',
            'info': '#17a2b8'
        }
        
        html = []
        html.append('<!DOCTYPE html>')
        html.append('<html lang="en">')
        html.append('<head>')
        html.append('    <meta charset="UTF-8">')
        html.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html.append(f'    <title>Audit Report: {self.project_name}</title>')
        html.append('    <style>')
        html.append('        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }')
        html.append('        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }')
        html.append('        h1 { color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }')
        html.append('        h2 { color: #555; margin-top: 30px; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; }')
        html.append('        h3 { color: #666; margin-top: 20px; }')
        html.append('        .metadata { color: #666; margin-bottom: 20px; }')
        html.append('        .score { font-size: 48px; font-weight: bold; color: #007bff; }')
        html.append('        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }')
        html.append('        .summary-card { background: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #007bff; }')
        html.append('        .summary-card h4 { margin: 0 0 10px 0; color: #555; }')
        html.append('        .summary-card .value { font-size: 32px; font-weight: bold; color: #333; }')
        html.append('        .finding { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 6px; border-left: 4px solid #ccc; }')
        html.append('        .finding-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }')
        html.append('        .finding-title { font-weight: bold; font-size: 16px; color: #333; }')
        html.append('        .badge { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; color: white; }')
        html.append('        .location { font-family: monospace; background: #e9ecef; padding: 2px 6px; border-radius: 3px; font-size: 14px; }')
        html.append('        .recommendation { margin-top: 10px; padding: 10px; background: #e7f3ff; border-radius: 4px; }')
        html.append('        .analyzer-result { margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 6px; }')
        html.append('        .metrics { display: flex; flex-wrap: wrap; gap: 15px; margin: 10px 0; }')
        html.append('        .metric { background: white; padding: 10px 15px; border-radius: 4px; }')
        html.append('        ul { list-style-type: none; padding-left: 0; }')
        html.append('        li { padding: 5px 0; }')
        html.append('    </style>')
        html.append('</head>')
        html.append('<body>')
        html.append('    <div class="container">')
        
        # Header
        html.append(f'        <h1>Audit Report: {self.project_name}</h1>')
        html.append(f'        <div class="metadata">')
        html.append(f'            <strong>Version:</strong> {self.project_version} | ')
        html.append(f'            <strong>Date:</strong> {self.timestamp} | ')
        html.append(f'            <strong>Execution Time:</strong> {self.execution_time:.2f}s')
        html.append(f'        </div>')
        
        # Executive Summary
        html.append('        <h2>Executive Summary</h2>')
        html.append('        <div class="summary-grid">')
        html.append('            <div class="summary-card">')
        html.append('                <h4>Overall Score</h4>')
        html.append(f'                <div class="value">{self.summary.overall_score:.1f}/100</div>')
        html.append('            </div>')
        html.append('            <div class="summary-card">')
        html.append('                <h4>Total Findings</h4>')
        html.append(f'                <div class="value">{self.summary.total_findings}</div>')
        html.append('            </div>')
        html.append('        </div>')
        
        # Findings by Severity
        html.append('        <h3>Findings by Severity</h3>')
        html.append('        <ul>')
        for severity, count in sorted(self.summary.findings_by_severity.items()):
            color = severity_colors.get(severity, '#6c757d')
            html.append(f'            <li><span class="badge" style="background-color: {color};">{severity.upper()}</span> {count}</li>')
        html.append('        </ul>')
        
        # Key Findings
        if self.summary.key_findings:
            html.append('        <h3>Key Findings</h3>')
            for i, finding in enumerate(self.summary.key_findings[:10], 1):
                color = severity_colors.get(finding.severity.value, '#6c757d')
                html.append(f'        <div class="finding" style="border-left-color: {color};">')
                html.append('            <div class="finding-header">')
                html.append(f'                <div class="finding-title">{i}. {finding.title}</div>')
                html.append(f'                <span class="badge" style="background-color: {color};">{finding.severity.value.upper()}</span>')
                html.append('            </div>')
                html.append(f'            <p>{finding.description}</p>')
                if finding.file_path:
                    location = f"{finding.file_path}"
                    if finding.line_number:
                        location += f":{finding.line_number}"
                    html.append(f'            <div><strong>Location:</strong> <span class="location">{location}</span></div>')
                html.append(f'            <div class="recommendation"><strong>Recommendation:</strong> {finding.recommendation}</div>')
                html.append('        </div>')
        
        # Action Plan
        html.append('        <h2>Action Plan</h2>')
        
        action_sections = [
            ('Critical Issues', self.action_plan.critical_issues, 'Must fix immediately'),
            ('Quick Wins', self.action_plan.quick_wins, 'Low effort, high impact'),
            ('Short Term', self.action_plan.short_term, 'Fix within 1-2 sprints'),
            ('Long Term', self.action_plan.long_term, 'Fix within 3-6 months'),
            ('Technical Debt', self.action_plan.technical_debt, 'Ongoing refactoring')
        ]
        
        for section_name, findings, description in action_sections:
            if findings:
                html.append(f'        <h3>{section_name} ({len(findings)})</h3>')
                html.append(f'        <p><em>{description}</em></p>')
                html.append('        <ul>')
                for finding in findings:
                    html.append(f'            <li><strong>{finding.title}</strong> ({finding.category.value.replace("_", " ")})')
                    if finding.file_path:
                        html.append(f' - <span class="location">{finding.file_path}</span>')
                    html.append('</li>')
                html.append('        </ul>')
        
        # Detailed Results
        html.append('        <h2>Detailed Results</h2>')
        for analyzer_name, result in sorted(self.results.items()):
            html.append('        <div class="analyzer-result">')
            html.append(f'            <h3>{analyzer_name.replace("_", " ").title()}</h3>')
            html.append(f'            <p><strong>Execution Time:</strong> {result.execution_time:.2f}s | ')
            html.append(f'            <strong>Status:</strong> {"✓ Success" if result.success else "✗ Failed"} | ')
            html.append(f'            <strong>Findings:</strong> {len(result.findings)}</p>')
            
            if result.error_message:
                html.append(f'            <p style="color: #dc3545;"><strong>Error:</strong> {result.error_message}</p>')
            
            if result.metrics:
                html.append('            <div class="metrics">')
                for key, value in result.metrics.items():
                    html.append(f'                <div class="metric"><strong>{key.replace("_", " ").title()}:</strong> {value}</div>')
                html.append('            </div>')
            
            html.append('        </div>')
        
        html.append('    </div>')
        html.append('</body>')
        html.append('</html>')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            'timestamp': self.timestamp,
            'project_name': self.project_name,
            'project_version': self.project_version,
            'execution_time': self.execution_time,
            'results': {name: result.to_dict() for name, result in self.results.items()},
            'summary': self.summary.to_dict(),
            'action_plan': self.action_plan.to_dict(),
        }
