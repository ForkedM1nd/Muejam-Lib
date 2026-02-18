"""Scalability Assessor for evaluating system scalability."""

import re
from pathlib import Path
from typing import List

from ..base import BaseAnalyzer
from ..models import AnalysisResult, Finding, Severity, Category


class ScalabilityAssessor(BaseAnalyzer):
    """Evaluates system scalability and maintainability."""

    def get_name(self) -> str:
        return "ScalabilityAssessor"

    def analyze(self) -> AnalysisResult:
        self.logger.info("Starting scalability assessment")
        findings = []
        findings.extend(self._detect_stateful_components())
        findings.extend(self._analyze_coupling())
        findings.extend(self._detect_technical_debt())
        self.logger.info(f"Scalability assessment complete. Found {len(findings)} issues")
        return AnalysisResult(
            analyzer_name=self.get_name(),
            findings=findings,
            metrics={"total_issues": len(findings)},
            success=True
        )

    def _detect_stateful_components(self) -> List[Finding]:
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        
        # Check for in-memory caching
        for py_file in backend_path.rglob("*.py"):
            if "test" in str(py_file):
                continue
            try:
                content = py_file.read_text()
                # Look for global state or in-memory caches
                if re.search(r'^\s*cache\s*=\s*\{', content, re.MULTILINE):
                    findings.append(Finding(
                        category=Category.SCALABILITY,
                        severity=Severity.MEDIUM,
                        title="In-memory cache detected",
                        description="Global in-memory cache limits horizontal scaling",
                        file_path=str(py_file),
                        recommendation="Use distributed cache like Redis/Valkey",
                        effort_estimate="medium"
                    ))
            except Exception as e:
                self.logger.debug(f"Error detecting stateful components in {py_file}: {e}")
        
        return findings

    def _analyze_coupling(self) -> List[Finding]:
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        
        # Check for circular imports
        for py_file in backend_path.rglob("*.py"):
            if "test" in str(py_file) or "__init__" in str(py_file):
                continue
            try:
                content = py_file.read_text()
                imports = re.findall(r'from\s+([a-zA-Z0-9_.]+)\s+import', content)
                
                # Count imports from same app
                app_name = py_file.parent.name
                same_app_imports = [i for i in imports if app_name in i]
                
                if len(same_app_imports) > 10:
                    findings.append(Finding(
                        category=Category.SCALABILITY,
                        severity=Severity.MEDIUM,
                        title="High module coupling detected",
                        description=f"File has {len(same_app_imports)} imports from same app",
                        file_path=str(py_file),
                        recommendation="Reduce coupling by refactoring dependencies",
                        effort_estimate="high"
                    ))
            except Exception as e:
                self.logger.debug(f"Error analyzing coupling in {py_file}: {e}")
        
        return findings

    def _detect_technical_debt(self) -> List[Finding]:
        findings = []
        project_root = Path(self.config.get("project_root", "."))
        
        # Check for TODO/FIXME comments
        for py_file in project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text()
                for match in re.finditer(r'#\s*(TODO|FIXME|HACK|XXX):\s*(.+)', content):
                    line_num = content[:match.start()].count('\n') + 1
                    findings.append(Finding(
                        category=Category.SCALABILITY,
                        severity=Severity.LOW,
                        title=f"Technical debt marker: {match.group(1)}",
                        description=match.group(2).strip(),
                        file_path=str(py_file),
                        line_number=line_num,
                        recommendation="Address technical debt item",
                        effort_estimate="medium"
                    ))
            except Exception as e:
                self.logger.debug(f"Error detecting technical debt in {py_file}: {e}")
        
        # Check for long functions (code smell)
        for py_file in project_root.rglob("*.py"):
            if "venv" in str(py_file) or "test" in str(py_file):
                continue
            try:
                content = py_file.read_text()
                func_pattern = r'def\s+(\w+)\([^)]*\):(.*?)(?=\ndef\s|\nclass\s|\Z)'
                for match in re.finditer(func_pattern, content, re.DOTALL):
                    func_name = match.group(1)
                    func_body = match.group(2)
                    line_count = func_body.count('\n')
                    max_length = self.config.get("max_function_length", 50)
                    
                    if line_count > max_length:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(Finding(
                            category=Category.SCALABILITY,
                            severity=Severity.MEDIUM,
                            title=f"Long function: {func_name} ({line_count} lines)",
                            description="Function exceeds recommended length",
                            file_path=str(py_file),
                            line_number=line_num,
                            recommendation="Refactor into smaller functions",
                            effort_estimate="medium"
                        ))
            except Exception as e:
                self.logger.debug(f"Error detecting long functions in {py_file}: {e}")
        
        return findings
