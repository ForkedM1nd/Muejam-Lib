"""Report generation utilities."""

import uuid
from typing import List, Dict
from datetime import datetime

from .models import (
    Finding, AnalysisResult, AuditReport, AuditSummary, ActionPlan,
    Severity, Category
)


class FindingsProcessor:
    """Processes and normalizes findings from different analyzers."""
    
    @staticmethod
    def normalize_findings(results: Dict[str, AnalysisResult]) -> List[Finding]:
        """Normalize findings from all analyzers."""
        all_findings = []
        for result in results.values():
            for finding in result.findings:
                # Ensure finding has an ID
                if not hasattr(finding, 'id') or not finding.id:
                    finding.id = str(uuid.uuid4())
                all_findings.append(finding)
        return all_findings
    
    @staticmethod
    def deduplicate_findings(findings: List[Finding]) -> List[Finding]:
        """Remove duplicate findings based on title and file path."""
        seen = set()
        unique_findings = []
        for finding in findings:
            key = (finding.title, finding.file_path, finding.line_number)
            if key not in seen:
                seen.add(key)
                unique_findings.append(finding)
        return unique_findings


class PriorityAnalyzer:
    """Analyzes and prioritizes findings."""
    
    @staticmethod
    def categorize_by_priority(findings: List[Finding]) -> ActionPlan:
        """Categorize findings into action plan buckets."""
        critical_issues = []
        quick_wins = []
        short_term = []
        long_term = []
        technical_debt = []
        
        for finding in findings:
            # Critical issues: Critical or High severity
            if finding.severity in [Severity.CRITICAL, Severity.HIGH]:
                critical_issues.append(finding)
            
            # Quick wins: Low effort, Medium+ severity
            elif finding.effort_estimate == "low" and finding.severity == Severity.MEDIUM:
                quick_wins.append(finding)
            
            # Technical debt: Scalability category
            elif finding.category == Category.SCALABILITY:
                technical_debt.append(finding)
            
            # Short term: Medium effort, Medium severity
            elif finding.effort_estimate == "medium" and finding.severity == Severity.MEDIUM:
                short_term.append(finding)
            
            # Long term: High effort or Low severity
            elif finding.effort_estimate == "high" or finding.severity == Severity.LOW:
                long_term.append(finding)
            
            # Default to short term
            else:
                short_term.append(finding)
        
        return ActionPlan(
            quick_wins=quick_wins,
            critical_issues=critical_issues,
            short_term=short_term,
            long_term=long_term,
            technical_debt=technical_debt
        )
    
    @staticmethod
    def identify_key_findings(findings: List[Finding], limit: int = 10) -> List[Finding]:
        """Identify the most important findings."""
        # Sort by severity (Critical > High > Medium > Low)
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4
        }
        
        sorted_findings = sorted(
            findings,
            key=lambda f: (severity_order.get(f.severity, 99), f.title)
        )
        
        return sorted_findings[:limit]


class ReportGenerator:
    """Generates audit reports."""
    
    @staticmethod
    def generate_summary(findings: List[Finding]) -> AuditSummary:
        """Generate executive summary from findings."""
        # Count findings by severity
        findings_by_severity = {}
        for severity in Severity:
            count = len([f for f in findings if f.severity == severity])
            if count > 0:
                findings_by_severity[severity.value] = count
        
        # Count findings by category
        findings_by_category = {}
        for category in Category:
            count = len([f for f in findings if f.category == category])
            if count > 0:
                findings_by_category[category.value] = count
        
        # Calculate overall score (100 - weighted penalty)
        penalty = 0
        penalty += len([f for f in findings if f.severity == Severity.CRITICAL]) * 10
        penalty += len([f for f in findings if f.severity == Severity.HIGH]) * 5
        penalty += len([f for f in findings if f.severity == Severity.MEDIUM]) * 2
        penalty += len([f for f in findings if f.severity == Severity.LOW]) * 0.5
        overall_score = max(0, 100 - penalty)
        
        # Calculate category scores
        category_scores = {}
        for category in Category:
            category_findings = [f for f in findings if f.category == category]
            if category_findings:
                cat_penalty = 0
                cat_penalty += len([f for f in category_findings if f.severity == Severity.CRITICAL]) * 10
                cat_penalty += len([f for f in category_findings if f.severity == Severity.HIGH]) * 5
                cat_penalty += len([f for f in category_findings if f.severity == Severity.MEDIUM]) * 2
                cat_penalty += len([f for f in category_findings if f.severity == Severity.LOW]) * 0.5
                category_scores[category.value] = max(0, 100 - cat_penalty)
            else:
                category_scores[category.value] = 100.0
        
        # Identify key findings
        key_findings = PriorityAnalyzer.identify_key_findings(findings)
        
        return AuditSummary(
            total_findings=len(findings),
            findings_by_severity=findings_by_severity,
            findings_by_category=findings_by_category,
            overall_score=overall_score,
            category_scores=category_scores,
            key_findings=key_findings
        )
    
    @staticmethod
    def generate_report(
        project_name: str,
        project_version: str,
        results: Dict[str, AnalysisResult],
        execution_time: float
    ) -> AuditReport:
        """Generate complete audit report."""
        # Process findings
        all_findings = FindingsProcessor.normalize_findings(results)
        all_findings = FindingsProcessor.deduplicate_findings(all_findings)
        
        # Generate summary
        summary = ReportGenerator.generate_summary(all_findings)
        
        # Generate action plan
        action_plan = PriorityAnalyzer.categorize_by_priority(all_findings)
        
        # Create report
        return AuditReport(
            timestamp=datetime.now().isoformat(),
            project_name=project_name,
            project_version=project_version,
            execution_time=execution_time,
            results=results,
            summary=summary,
            action_plan=action_plan
        )
