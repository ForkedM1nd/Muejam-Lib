"""Infrastructure Auditor for evaluating deployment readiness."""

import re
from pathlib import Path
from typing import List

from ..base import BaseAnalyzer
from ..models import AnalysisResult, Finding, Severity, Category


class InfrastructureAuditor(BaseAnalyzer):
    """Evaluates infrastructure configuration and deployment readiness."""

    def get_name(self) -> str:
        return "InfrastructureAuditor"

    def analyze(self) -> AnalysisResult:
        self.logger.info("Starting infrastructure audit")
        findings = []
        findings.extend(self._analyze_docker())
        findings.extend(self._analyze_docker_compose())
        findings.extend(self._check_env_documentation())
        findings.extend(self._check_monitoring())
        findings.extend(self._check_logging())
        self.logger.info(f"Infrastructure audit complete. Found {len(findings)} issues")
        return AnalysisResult(
            analyzer_name=self.get_name(),
            findings=findings,
            metrics={"total_issues": len(findings)},
            success=True
        )

    def _analyze_docker(self) -> List[Finding]:
        findings = []
        project_root = Path(self.config.get("project_root", "."))
        
        for dockerfile in project_root.rglob("Dockerfile*"):
            # Skip backup directories
            if 'backup' in str(dockerfile).lower() or '.backup' in str(dockerfile):
                continue
                
            try:
                content = dockerfile.read_text()
                # Check for multi-stage builds
                if content.count("FROM") < 2:
                    findings.append(Finding(
                        category=Category.INFRASTRUCTURE,
                        severity=Severity.LOW,
                        title="Dockerfile without multi-stage build",
                        description="Consider using multi-stage builds for optimization",
                        file_path=str(dockerfile),
                        recommendation="Use multi-stage builds to reduce image size",
                        effort_estimate="medium"
                    ))
                
                # Check for root user
                if "USER" not in content:
                    findings.append(Finding(
                        category=Category.INFRASTRUCTURE,
                        severity=Severity.MEDIUM,
                        title="Dockerfile runs as root user",
                        description="Container runs as root, security risk",
                        file_path=str(dockerfile),
                        recommendation="Add USER directive to run as non-root",
                        effort_estimate="low"
                    ))
            except Exception as e:
                self.logger.debug(f"Error analyzing {dockerfile}: {e}")
        
        return findings

    def _analyze_docker_compose(self) -> List[Finding]:
        findings = []
        project_root = Path(self.config.get("project_root", "."))
        compose_file = project_root / "docker-compose.yml"
        
        if not compose_file.exists():
            return findings
        
        try:
            content = compose_file.read_text()
            # Check for health checks
            services = re.findall(r'^\s{2}(\w+):', content, re.MULTILINE)
            for service in services:
                service_section = re.search(f'{service}:(.*?)(?=^  \\w+:|\\Z)', content, re.DOTALL | re.MULTILINE)
                if service_section and "healthcheck:" not in service_section.group(1):
                    findings.append(Finding(
                        category=Category.INFRASTRUCTURE,
                        severity=Severity.MEDIUM,
                        title=f"Service without health check: {service}",
                        description="Docker service lacks health check configuration",
                        file_path=str(compose_file),
                        recommendation="Add healthcheck configuration to service",
                        effort_estimate="low"
                    ))
        except Exception as e:
            self.logger.debug(f"Error analyzing docker-compose: {e}")
        
        return findings

    def _check_env_documentation(self) -> List[Finding]:
        findings = []
        project_root = Path(self.config.get("project_root", "."))
        
        # Skip this check for tools/utility directories
        abs_root = project_root.resolve()
        if 'tools' in abs_root.name.lower() or 'scripts' in abs_root.name.lower():
            return findings
            
        env_example = project_root / ".env.example"
        
        if not env_example.exists():
            findings.append(Finding(
                category=Category.INFRASTRUCTURE,
                severity=Severity.MEDIUM,
                title="Missing .env.example file",
                description="No environment variable documentation",
                file_path=str(project_root),
                recommendation="Create .env.example with all required variables",
                effort_estimate="low"
            ))
            return findings
        
        try:
            example_vars = set(re.findall(r'^([A-Z_]+)=', env_example.read_text(), re.MULTILINE))
            # Check code for undocumented env vars
            for py_file in project_root.rglob("*.py"):
                if "venv" in str(py_file) or "test" in str(py_file):
                    continue
                content = py_file.read_text()
                used_vars = set(re.findall(r'os\.environ\.get\(["\']([A-Z_]+)["\']', content))
                used_vars.update(re.findall(r'os\.getenv\(["\']([A-Z_]+)["\']', content))
                
                undocumented = used_vars - example_vars
                for var in undocumented:
                    findings.append(Finding(
                        category=Category.INFRASTRUCTURE,
                        severity=Severity.LOW,
                        title=f"Undocumented environment variable: {var}",
                        description="Environment variable not in .env.example",
                        file_path=str(py_file),
                        recommendation="Add variable to .env.example",
                        effort_estimate="low"
                    ))
        except Exception as e:
            self.logger.debug(f"Error checking env documentation: {e}")
        
        return findings

    def _check_monitoring(self) -> List[Finding]:
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        
        # Skip if backend path doesn't exist (e.g., tools-only directory)
        if not backend_path.exists():
            return findings
        
        # Check for Sentry configuration
        has_sentry = False
        for settings_file in backend_path.rglob("settings*.py"):
            if "sentry" in settings_file.read_text().lower():
                has_sentry = True
                break
        
        if not has_sentry:
            findings.append(Finding(
                category=Category.INFRASTRUCTURE,
                severity=Severity.MEDIUM,
                title="Sentry error tracking not configured",
                description="No error tracking setup found",
                file_path=str(backend_path),
                recommendation="Configure Sentry for error tracking",
                effort_estimate="medium"
            ))
        
        return findings

    def _check_logging(self) -> List[Finding]:
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        
        # Check for structured logging
        for py_file in backend_path.rglob("*.py"):
            if "test" in str(py_file):
                continue
            try:
                content = py_file.read_text()
                # Look for print statements instead of logging
                if re.search(r'\bprint\(', content):
                    line_num = content.find("print(")
                    if line_num != -1:
                        line_num = content[:line_num].count('\n') + 1
                        findings.append(Finding(
                            category=Category.INFRASTRUCTURE,
                            severity=Severity.LOW,
                            title="Using print() instead of logging",
                            description="Code uses print() for output",
                            file_path=str(py_file),
                            line_number=line_num,
                            recommendation="Use logging module instead of print()",
                            effort_estimate="low"
                        ))
            except Exception as e:
                self.logger.debug(f"Error checking logging in {py_file}: {e}")
        
        return findings
