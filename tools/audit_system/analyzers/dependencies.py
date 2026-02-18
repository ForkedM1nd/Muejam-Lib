"""Dependency Checker for analyzing project dependencies."""

import re
import subprocess
import json
from pathlib import Path
from typing import List

from ..base import BaseAnalyzer
from ..models import AnalysisResult, Finding, Severity, Category


class DependencyChecker(BaseAnalyzer):
    """Analyzes project dependencies for updates and vulnerabilities."""

    def get_name(self) -> str:
        return "DependencyChecker"

    def analyze(self) -> AnalysisResult:
        self.logger.info("Starting dependency analysis")
        findings = []
        findings.extend(self._analyze_python_dependencies())
        findings.extend(self._analyze_javascript_dependencies())
        findings.extend(self._check_unused_dependencies())
        self.logger.info(f"Dependency analysis complete. Found {len(findings)} issues")
        return AnalysisResult(
            analyzer_name=self.get_name(),
            findings=findings,
            metrics={"total_issues": len(findings)},
            success=True
        )

    def _analyze_python_dependencies(self) -> List[Finding]:
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        requirements_file = backend_path / "requirements.txt"
        
        if not requirements_file.exists():
            return findings
        
        try:
            # Check for outdated packages
            result = subprocess.run(
                ["pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                outdated = json.loads(result.stdout)
                for pkg in outdated:
                    findings.append(Finding(
                        category=Category.DEPENDENCIES,
                        severity=Severity.LOW,
                        title=f"Outdated Python package: {pkg['name']}",
                        description=f"Current: {pkg['version']}, Latest: {pkg['latest_version']}",
                        file_path=str(requirements_file),
                        recommendation=f"Update to version {pkg['latest_version']}",
                        effort_estimate="low"
                    ))
        except Exception as e:
            self.logger.debug(f"Error analyzing Python dependencies: {e}")
        
        return findings

    def _analyze_javascript_dependencies(self) -> List[Finding]:
        findings = []
        frontend_path = Path(self.config.get("frontend_path", "frontend"))
        package_json = frontend_path / "package.json"
        
        if not package_json.exists():
            return findings
        
        try:
            result = subprocess.run(
                ["npm", "outdated", "--json"],
                cwd=str(frontend_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                outdated = json.loads(result.stdout)
                for pkg_name, pkg_info in outdated.items():
                    findings.append(Finding(
                        category=Category.DEPENDENCIES,
                        severity=Severity.LOW,
                        title=f"Outdated npm package: {pkg_name}",
                        description=f"Current: {pkg_info.get('current')}, Latest: {pkg_info.get('latest')}",
                        file_path=str(package_json),
                        recommendation=f"Update to version {pkg_info.get('latest')}",
                        effort_estimate="low"
                    ))
        except Exception as e:
            self.logger.debug(f"Error analyzing JavaScript dependencies: {e}")
        
        return findings

    def _check_unused_dependencies(self) -> List[Finding]:
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        requirements_file = backend_path / "requirements.txt"
        
        if not requirements_file.exists():
            return findings
        
        try:
            # Get declared dependencies
            content = requirements_file.read_text()
            declared = set(re.findall(r'^([a-zA-Z0-9_-]+)', content, re.MULTILINE))
            
            # Get imported modules
            imported = set()
            for py_file in backend_path.rglob("*.py"):
                if "venv" in str(py_file):
                    continue
                try:
                    file_content = py_file.read_text()
                    imports = re.findall(r'^\s*(?:from|import)\s+([a-zA-Z0-9_]+)', file_content, re.MULTILINE)
                    imported.update(imports)
                except Exception:
                    pass
            
            # Find potentially unused (simple heuristic)
            unused = declared - imported
            # Filter out common packages that might be used indirectly
            common_indirect = {"setuptools", "wheel", "pip", "gunicorn", "uwsgi"}
            unused = unused - common_indirect
            
            for pkg in unused:
                findings.append(Finding(
                    category=Category.DEPENDENCIES,
                    severity=Severity.LOW,
                    title=f"Potentially unused dependency: {pkg}",
                    description="Package not directly imported in code",
                    file_path=str(requirements_file),
                    recommendation="Verify if package is needed and remove if unused",
                    effort_estimate="low"
                ))
        except Exception as e:
            self.logger.debug(f"Error checking unused dependencies: {e}")
        
        return findings
