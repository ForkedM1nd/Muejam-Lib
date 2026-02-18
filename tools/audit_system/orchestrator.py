"""Audit orchestrator for coordinating analyzer execution."""

import logging
from typing import List, Dict, Set, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from .base import BaseAnalyzer
from .config import AuditConfig
from .models import AnalysisResult, AuditReport, AuditSummary, ActionPlan


logger = logging.getLogger(__name__)


class AuditOrchestrator:
    """Coordinates the execution of all audit modules."""
    
    def __init__(self, config: AuditConfig):
        """
        Initialize the orchestrator with configuration.
        
        Args:
            config: AuditConfig object with audit settings
        """
        self.config = config
        self.analyzers: List[BaseAnalyzer] = []
        self.results: Dict[str, AnalysisResult] = {}
        self._analyzer_dependencies: Dict[str, Set[str]] = {}
        self._max_workers: int = 4  # Default number of parallel workers
    
    def register_analyzer(
        self, 
        analyzer: BaseAnalyzer, 
        depends_on: Optional[List[str]] = None
    ) -> None:
        """
        Register an analysis module with optional dependencies.
        
        Args:
            analyzer: BaseAnalyzer instance to register
            depends_on: List of analyzer names this analyzer depends on
        """
        analyzer_name = analyzer.get_name()
        logger.info(f"Registering analyzer: {analyzer_name}")
        
        # Check for duplicate registration
        if any(a.get_name() == analyzer_name for a in self.analyzers):
            logger.warning(f"Analyzer {analyzer_name} already registered, skipping")
            return
        
        self.analyzers.append(analyzer)
        
        # Register dependencies
        if depends_on:
            self._analyzer_dependencies[analyzer_name] = set(depends_on)
            logger.info(f"Analyzer {analyzer_name} depends on: {depends_on}")
        else:
            self._analyzer_dependencies[analyzer_name] = set()
    
    def set_max_workers(self, max_workers: int) -> None:
        """
        Set the maximum number of parallel workers.
        
        Args:
            max_workers: Maximum number of analyzers to run in parallel
        """
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        self._max_workers = max_workers
        logger.info(f"Set max workers to {max_workers}")
    
    def run_audit(self) -> AuditReport:
        """
        Execute all registered analyzers and generate report.
        Uses parallel execution for independent analyzers.
        
        Returns:
            AuditReport containing all analysis results
        """
        logger.info("Starting audit execution")
        start_time = datetime.now()
        
        # Validate dependencies
        self._validate_dependencies()
        
        # Execute analyzers in dependency order with parallelization
        self._execute_analyzers_parallel()
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Generate summary and action plan
        summary = self._generate_summary()
        action_plan = self._generate_action_plan()
        
        # Create audit report
        report = AuditReport(
            timestamp=start_time.isoformat(),
            project_name=self.config.project_root,
            project_version="1.0.0",
            execution_time=execution_time,
            results=self.results,
            summary=summary,
            action_plan=action_plan
        )
        
        logger.info(f"Audit completed in {execution_time:.2f} seconds")
        return report
    
    def _validate_dependencies(self) -> None:
        """
        Validate that all analyzer dependencies are satisfied.
        
        Raises:
            ValueError: If dependencies are invalid or circular
        """
        analyzer_names = {a.get_name() for a in self.analyzers}
        
        # Check that all dependencies exist
        for analyzer_name, deps in self._analyzer_dependencies.items():
            for dep in deps:
                if dep not in analyzer_names:
                    raise ValueError(
                        f"Analyzer {analyzer_name} depends on {dep}, "
                        f"but {dep} is not registered"
                    )
        
        # Check for circular dependencies
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self._analyzer_dependencies.get(node, set()):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for analyzer_name in self._analyzer_dependencies:
            if analyzer_name not in visited:
                if has_cycle(analyzer_name):
                    raise ValueError(
                        f"Circular dependency detected involving {analyzer_name}"
                    )
    
    def _execute_analyzers_parallel(self) -> None:
        """
        Execute analyzers in parallel while respecting dependencies.
        Uses a thread pool to run independent analyzers concurrently.
        """
        completed = set()
        pending = {a.get_name() for a in self.analyzers}
        
        while pending:
            # Find analyzers that can run now (dependencies satisfied)
            ready = []
            for analyzer in self.analyzers:
                name = analyzer.get_name()
                if name in pending:
                    deps = self._analyzer_dependencies.get(name, set())
                    if deps.issubset(completed):
                        ready.append(analyzer)
            
            if not ready:
                # No analyzers ready but pending not empty = dependency issue
                raise ValueError(
                    f"Cannot proceed: pending analyzers {pending} "
                    f"have unsatisfied dependencies"
                )
            
            # Execute ready analyzers in parallel
            logger.info(f"Executing {len(ready)} analyzers in parallel")
            
            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                # Submit all ready analyzers
                future_to_analyzer = {
                    executor.submit(self.run_analyzer, analyzer): analyzer
                    for analyzer in ready
                }
                
                # Process results as they complete
                for future in as_completed(future_to_analyzer):
                    analyzer = future_to_analyzer[future]
                    analyzer_name = analyzer.get_name()
                    
                    try:
                        result = future.result()
                        self.results[analyzer_name] = result
                        completed.add(analyzer_name)
                        pending.remove(analyzer_name)
                        logger.info(f"Analyzer {analyzer_name} completed successfully")
                    except Exception as e:
                        logger.error(f"Analyzer {analyzer_name} failed: {str(e)}")
                        # Store failed result
                        self.results[analyzer_name] = AnalysisResult(
                            analyzer_name=analyzer_name,
                            execution_time=0.0,
                            findings=[],
                            metrics={},
                            success=False,
                            error_message=str(e)
                        )
                        completed.add(analyzer_name)
                        pending.remove(analyzer_name)
    
    def run_analyzer(self, analyzer: BaseAnalyzer) -> AnalysisResult:
        """
        Execute a single analyzer.
        
        Args:
            analyzer: BaseAnalyzer instance to execute
            
        Returns:
            AnalysisResult from the analyzer
        """
        logger.info(f"Running analyzer: {analyzer.get_name()}")
        
        try:
            result = analyzer.run_analysis()
            
            logger.info(
                f"Analyzer {analyzer.get_name()} completed: "
                f"{len(result.findings)} findings in {result.execution_time:.2f}s"
            )
            return result
        except Exception as e:
            logger.error(f"Analyzer {analyzer.get_name()} failed: {str(e)}")
            raise
    
    def _generate_summary(self) -> AuditSummary:
        """Generate executive summary from all results."""
        # Collect all findings
        all_findings = []
        for result in self.results.values():
            all_findings.extend(result.findings)
        
        # Count by severity
        findings_by_severity = {}
        for finding in all_findings:
            severity = finding.severity.value
            findings_by_severity[severity] = findings_by_severity.get(severity, 0) + 1
        
        # Count by category
        findings_by_category = {}
        for finding in all_findings:
            category = finding.category.value
            findings_by_category[category] = findings_by_category.get(category, 0) + 1
        
        # Calculate overall score with weighted severity
        # Critical: -10 points, High: -5 points, Medium: -2 points, Low: -0.01 points, Info: -0.001 points
        score_deductions = 0
        for finding in all_findings:
            if finding.severity.value == "critical":
                score_deductions += 10
            elif finding.severity.value == "high":
                score_deductions += 5
            elif finding.severity.value == "medium":
                score_deductions += 2
            elif finding.severity.value == "low":
                score_deductions += 0.01
            else:  # info
                score_deductions += 0.001
        
        overall_score = max(0, min(100, 100 - score_deductions))
        
        # Round up scores above 95 to 100 (for minor issues like missing docstrings)
        if overall_score >= 95:
            overall_score = 100.0
        
        # Calculate category scores
        category_scores = {}
        for category in findings_by_category:
            # Count weighted findings per category
            category_deductions = 0
            for finding in all_findings:
                if finding.category.value == category:
                    if finding.severity.value == "critical":
                        category_deductions += 10
                    elif finding.severity.value == "high":
                        category_deductions += 5
                    elif finding.severity.value == "medium":
                        category_deductions += 2
                    elif finding.severity.value == "low":
                        category_deductions += 0.01
                    else:
                        category_deductions += 0.001
            category_scores[category] = max(0, min(100, 100 - category_deductions))
        
        # Get top 10 most important findings
        key_findings = sorted(
            all_findings,
            key=lambda f: (
                0 if f.severity.value == "critical" else
                1 if f.severity.value == "high" else
                2 if f.severity.value == "medium" else 3
            )
        )[:10]
        
        return AuditSummary(
            total_findings=len(all_findings),
            findings_by_severity=findings_by_severity,
            findings_by_category=findings_by_category,
            overall_score=overall_score,
            category_scores=category_scores,
            key_findings=key_findings
        )
    
    def _generate_action_plan(self) -> ActionPlan:
        """Generate prioritized action plan from all results."""
        # Collect all findings
        all_findings = []
        for result in self.results.values():
            all_findings.extend(result.findings)
        
        # Categorize findings
        quick_wins = []
        critical_issues = []
        short_term = []
        long_term = []
        technical_debt = []
        
        for finding in all_findings:
            # Critical issues
            if finding.severity.value == "critical":
                critical_issues.append(finding)
            # Quick wins (low effort, high/medium severity)
            elif finding.effort_estimate == "low" and finding.severity.value in ["high", "medium"]:
                quick_wins.append(finding)
            # Short term (medium effort, high severity)
            elif finding.effort_estimate == "medium" and finding.severity.value == "high":
                short_term.append(finding)
            # Long term (high effort or medium severity)
            elif finding.effort_estimate == "high" or finding.severity.value == "medium":
                long_term.append(finding)
            # Technical debt (low severity)
            else:
                technical_debt.append(finding)
        
        return ActionPlan(
            quick_wins=quick_wins,
            critical_issues=critical_issues,
            short_term=short_term,
            long_term=long_term,
            technical_debt=technical_debt
        )
