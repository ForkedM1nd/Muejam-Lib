"""Test Coverage Analyzer for measuring testing quality."""

import re
import subprocess
import json
from pathlib import Path
from typing import List

from ..base import BaseAnalyzer
from ..models import AnalysisResult, Finding, Severity, Category


class TestCoverageAnalyzer(BaseAnalyzer):
    """Analyzes test coverage and quality."""

    def get_name(self) -> str:
        return "TestCoverageAnalyzer"

    def analyze(self) -> AnalysisResult:
        self.logger.info("Starting test coverage analysis")
        findings = []
        findings.extend(self._measure_backend_coverage())
        findings.extend(self._identify_critical_gaps())
        findings.extend(self._check_property_tests())
        findings.extend(self._evaluate_test_quality())
        self.logger.info(f"Test coverage analysis complete. Found {len(findings)} issues")
        return AnalysisResult(
            analyzer_name=self.get_name(),
            findings=findings,
            metrics={"total_issues": len(findings)},
            success=True
        )

    def _measure_backend_coverage(self) -> List[Finding]:
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        if not backend_path.exists():
            return findings
        
        try:
            # Run pytest with coverage
            result = subprocess.run(
                ["pytest", "--cov=.", "--cov-report=json", "--cov-report=term"],
                cwd=str(backend_path),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            coverage_file = backend_path / "coverage.json"
            if coverage_file.exists():
                data = json.loads(coverage_file.read_text())
                total_coverage = data.get("totals", {}).get("percent_covered", 0)
                min_coverage = self.config.get("min_code_coverage", 80.0)
                
                if total_coverage < min_coverage:
                    findings.append(Finding(
                        category=Category.TESTING,
                        severity=Severity.MEDIUM,
                        title=f"Low test coverage: {total_coverage:.1f}%",
                        description=f"Coverage below threshold of {min_coverage}%",
                        file_path=str(backend_path),
                        recommendation="Add tests to increase coverage",
                        effort_estimate="high"
                    ))
        except Exception as e:
            self.logger.debug(f"Error measuring coverage: {e}")
        
        return findings

    def _identify_critical_gaps(self) -> List[Finding]:
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        
        # Identify critical endpoints without tests
        critical_patterns = ["login", "auth", "payment", "delete", "admin"]
        for view_file in backend_path.rglob("views.py"):
            try:
                content = view_file.read_text()
                for pattern in critical_patterns:
                    if pattern in content.lower():
                        # Check if corresponding test exists
                        test_file = view_file.parent / "tests" / f"test_{view_file.name}"
                        if not test_file.exists():
                            findings.append(Finding(
                                category=Category.TESTING,
                                severity=Severity.HIGH,
                                title=f"Critical path without tests: {pattern}",
                                description="Critical functionality lacks test coverage",
                                file_path=str(view_file),
                                recommendation="Add comprehensive tests for critical paths",
                                effort_estimate="high"
                            ))
            except Exception as e:
                self.logger.debug(f"Error checking critical gaps in {view_file}: {e}")
        
        return findings

    def _check_property_tests(self) -> List[Finding]:
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        
        # Check for serializers without property tests
        for serializer_file in backend_path.rglob("serializers.py"):
            try:
                content = serializer_file.read_text()
                if "Serializer" in content:
                    # Check if hypothesis tests exist
                    test_dir = serializer_file.parent / "tests"
                    has_hypothesis = False
                    if test_dir.exists():
                        for test_file in test_dir.glob("test_*.py"):
                            if "hypothesis" in test_file.read_text().lower():
                                has_hypothesis = True
                                break
                    
                    if not has_hypothesis:
                        findings.append(Finding(
                            category=Category.TESTING,
                            severity=Severity.LOW,
                            title="Serializer without property-based tests",
                            description="Consider adding Hypothesis tests for serializers",
                            file_path=str(serializer_file),
                            recommendation="Add property-based tests using Hypothesis",
                            effort_estimate="medium"
                        ))
            except Exception as e:
                self.logger.debug(f"Error checking property tests in {serializer_file}: {e}")
        
        return findings

    def _evaluate_test_quality(self) -> List[Finding]:
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        
        for test_file in backend_path.rglob("test_*.py"):
            try:
                content = test_file.read_text()
                # Check for tests without assertions
                test_pattern = r'def\s+test_\w+\([^)]*\):(.*?)(?=\n    def|\nclass|\Z)'
                for match in re.finditer(test_pattern, content, re.DOTALL):
                    test_body = match.group(1)
                    if "assert" not in test_body.lower():
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(Finding(
                            category=Category.TESTING,
                            severity=Severity.MEDIUM,
                            title="Test without assertions",
                            description="Test function lacks assertions",
                            file_path=str(test_file),
                            line_number=line_num,
                            recommendation="Add assertions to verify test behavior",
                            effort_estimate="low"
                        ))
            except Exception as e:
                self.logger.debug(f"Error evaluating test quality in {test_file}: {e}")
        
        return findings
