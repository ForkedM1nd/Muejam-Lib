"""Documentation Evaluator for assessing documentation completeness."""

import re
from pathlib import Path
from typing import List

from ..base import BaseAnalyzer
from ..models import AnalysisResult, Finding, Severity, Category


class DocumentationEvaluator(BaseAnalyzer):
    """Evaluates documentation completeness and quality."""

    def get_name(self) -> str:
        return "DocumentationEvaluator"

    def analyze(self) -> AnalysisResult:
        self.logger.info("Starting documentation evaluation")
        findings = []
        findings.extend(self._check_docstring_coverage())
        findings.extend(self._check_readme())
        findings.extend(self._check_architecture_docs())
        self.logger.info(f"Documentation evaluation complete. Found {len(findings)} issues")
        return AnalysisResult(
            analyzer_name=self.get_name(),
            findings=findings,
            metrics={"total_issues": len(findings)},
            success=True
        )

    def _check_docstring_coverage(self) -> List[Finding]:
        findings = []
        project_root = Path(self.config.get("project_root", "."))
        
        for py_file in project_root.rglob("*.py"):
            if "venv" in str(py_file) or "test" in str(py_file) or "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text()
                lines = content.split('\n')
                
                # Check for functions without docstrings
                for i, line in enumerate(lines):
                    # Match function definitions
                    func_match = re.match(r'\s*def\s+(\w+)\s*\([^)]*\):', line)
                    if func_match:
                        func_name = func_match.group(1)
                        if not func_name.startswith("_"):  # Skip private functions
                            # Check if next non-empty line is a docstring
                            has_docstring = False
                            for j in range(i + 1, min(i + 5, len(lines))):
                                stripped = lines[j].strip()
                                if stripped:
                                    if stripped.startswith('"""') or stripped.startswith("'''"):
                                        has_docstring = True
                                    break
                            
                            if not has_docstring:
                                findings.append(Finding(
                                    category=Category.DOCUMENTATION,
                                    severity=Severity.LOW,
                                    title=f"Function without docstring: {func_name}",
                                    description="Public function lacks documentation",
                                    file_path=str(py_file.relative_to(project_root)),
                                    line_number=i + 1,
                                    recommendation="Add docstring describing function purpose and parameters",
                                    effort_estimate="low"
                                ))
                    
                    # Match class definitions
                    class_match = re.match(r'\s*class\s+(\w+)', line)
                    if class_match:
                        class_name = class_match.group(1)
                        # Check if next non-empty line is a docstring
                        has_docstring = False
                        for j in range(i + 1, min(i + 5, len(lines))):
                            stripped = lines[j].strip()
                            if stripped:
                                if stripped.startswith('"""') or stripped.startswith("'''"):
                                    has_docstring = True
                                break
                        
                        if not has_docstring:
                            findings.append(Finding(
                                category=Category.DOCUMENTATION,
                                severity=Severity.LOW,
                                title=f"Class without docstring: {class_name}",
                                description="Class lacks documentation",
                                file_path=str(py_file.relative_to(project_root)),
                                line_number=i + 1,
                                recommendation="Add docstring describing class purpose",
                                effort_estimate="low"
                            ))
            except Exception as e:
                self.logger.debug(f"Error checking docstrings in {py_file}: {e}")
        
        return findings

    def _check_readme(self) -> List[Finding]:
        findings = []
        project_root = Path(self.config.get("project_root", "."))
        readme = project_root / "README.md"
        
        if not readme.exists():
            findings.append(Finding(
                category=Category.DOCUMENTATION,
                severity=Severity.HIGH,
                title="Missing README.md",
                description="Project lacks README documentation",
                file_path=str(project_root),
                recommendation="Create README.md with setup and usage instructions",
                effort_estimate="medium"
            ))
            return findings
        
        try:
            content = readme.read_text()
            required_sections = ["installation", "setup", "usage", "configuration"]
            missing = [s for s in required_sections if s not in content.lower()]
            
            if missing:
                findings.append(Finding(
                    category=Category.DOCUMENTATION,
                    severity=Severity.MEDIUM,
                    title="Incomplete README",
                    description=f"Missing sections: {', '.join(missing)}",
                    file_path=str(readme),
                    recommendation="Add missing sections to README",
                    effort_estimate="medium"
                ))
        except Exception as e:
            self.logger.debug(f"Error checking README: {e}")
        
        return findings

    def _check_architecture_docs(self) -> List[Finding]:
        findings = []
        project_root = Path(self.config.get("project_root", "."))
        docs_path = Path(self.config.get("docs_path", "docs"))
        
        # Check for architecture documentation
        arch_files = list(docs_path.glob("*architecture*")) + list(docs_path.glob("*design*"))
        if not arch_files:
            findings.append(Finding(
                category=Category.DOCUMENTATION,
                severity=Severity.MEDIUM,
                title="Missing architecture documentation",
                description="No architecture or design documentation found",
                file_path=str(docs_path),
                recommendation="Create architecture documentation describing system design",
                effort_estimate="high"
            ))
        
        return findings
