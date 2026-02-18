"""API Evaluator for assessing API design and documentation."""

import re
from pathlib import Path
from typing import List

from ..base import BaseAnalyzer
from ..models import AnalysisResult, Finding, Severity, Category


class APIEvaluator(BaseAnalyzer):
    """Evaluates API design consistency and documentation quality."""

    def get_name(self) -> str:
        return "APIEvaluator"

    def analyze(self) -> AnalysisResult:
        self.logger.info("Starting API evaluation")
        findings = []
        findings.extend(self._validate_restful_design())
        findings.extend(self._check_documentation())
        findings.extend(self._validate_consistency())
        self.logger.info(f"API evaluation complete. Found {len(findings)} issues")
        return AnalysisResult(
            analyzer_name=self.get_name(),
            findings=findings,
            metrics={"total_issues": len(findings)},
            success=True
        )

    def _validate_restful_design(self) -> List[Finding]:
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        for url_file in backend_path.rglob("urls.py"):
            try:
                content = url_file.read_text()
                # Check for non-RESTful URL patterns
                if re.search(r'path\(["\'].*\?', content):
                    findings.append(Finding(
                        category=Category.API_DESIGN,
                        severity=Severity.MEDIUM,
                        title="Query parameters in URL path",
                        description="URL contains query parameters in path definition",
                        file_path=str(url_file),
                        recommendation="Use path parameters or query strings properly",
                        effort_estimate="low"
                    ))
            except Exception as e:
                self.logger.debug(f"Error analyzing {url_file}: {e}")
        return findings

    def _check_documentation(self) -> List[Finding]:
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        for view_file in backend_path.rglob("views.py"):
            try:
                content = view_file.read_text()
                # Find views without docstrings
                view_pattern = r'@api_view\([^)]*\)\s*\ndef\s+(\w+)\([^)]*\):\s*(?!""")'
                for match in re.finditer(view_pattern, content):
                    line_num = content[:match.start()].count('\n') + 1
                    findings.append(Finding(
                        category=Category.API_DESIGN,
                        severity=Severity.LOW,
                        title=f"API view without docstring: {match.group(1)}",
                        description="API endpoint lacks documentation",
                        file_path=str(view_file),
                        line_number=line_num,
                        recommendation="Add docstring describing endpoint behavior",
                        effort_estimate="low"
                    ))
            except Exception as e:
                self.logger.debug(f"Error checking documentation in {view_file}: {e}")
        return findings

    def _validate_consistency(self) -> List[Finding]:
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        # Check for inconsistent error handling
        error_formats = set()
        for view_file in backend_path.rglob("views.py"):
            try:
                content = view_file.read_text()
                # Look for different error response formats
                if 'Response({"error":' in content:
                    error_formats.add('{"error":')
                if 'Response({"message":' in content:
                    error_formats.add('{"message":')
                if 'Response({"detail":' in content:
                    error_formats.add('{"detail":')
            except Exception as e:
                self.logger.debug(f"Error checking consistency in {view_file}: {e}")
        
        if len(error_formats) > 1:
            findings.append(Finding(
                category=Category.API_DESIGN,
                severity=Severity.MEDIUM,
                title="Inconsistent error response format",
                description=f"Multiple error formats found: {', '.join(error_formats)}",
                file_path=str(backend_path),
                recommendation="Standardize error response format across all endpoints",
                effort_estimate="medium"
            ))
        return findings
