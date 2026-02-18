"""Security Scanner for detecting vulnerabilities and compliance issues."""

import re
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..base import BaseAnalyzer
from ..models import AnalysisResult, Finding, Severity, Category


class SecurityScanner(BaseAnalyzer):
    """Scans for security vulnerabilities and compliance issues."""

    def get_name(self) -> str:
        """Return the analyzer name."""
        return "SecurityScanner"

    def analyze(self) -> AnalysisResult:
        """Run security analysis."""
        self.logger.info("Starting security analysis")
        
        findings = []
        
        # Scan Python dependencies
        findings.extend(self._scan_python_dependencies())
        
        # Scan JavaScript dependencies
        findings.extend(self._scan_javascript_dependencies())
        
        # Analyze authentication code
        findings.extend(self._analyze_authentication())
        
        # Check for SQL injection vulnerabilities
        findings.extend(self._check_sql_injection())
        
        # Check for XSS vulnerabilities
        findings.extend(self._check_xss())
        
        # Scan for hardcoded secrets
        findings.extend(self._scan_secrets())
        
        # Verify security headers
        findings.extend(self._check_security_headers())
        
        # Check GDPR compliance
        findings.extend(self._check_gdpr_compliance())
        
        self.logger.info(f"Security analysis complete. Found {len(findings)} issues")
        
        return AnalysisResult(
            analyzer_name=self.get_name(),
            findings=findings,
            metrics={
                "total_issues": len(findings),
                "critical_issues": len([f for f in findings if f.severity == Severity.CRITICAL]),
                "high_issues": len([f for f in findings if f.severity == Severity.HIGH]),
            },
            success=True
        )

    def _scan_python_dependencies(self) -> List[Finding]:
        """Scan Python dependencies using Safety or pip-audit."""
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        requirements_file = backend_path / "requirements.txt"
        
        if not requirements_file.exists():
            return findings
        
        try:
            # Try using pip-audit first
            result = subprocess.run(
                ["pip-audit", "-r", str(requirements_file), "--format", "json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                for vuln in data.get("vulnerabilities", []):
                    findings.append(Finding(
                        category=Category.SECURITY,
                        severity=Severity.CRITICAL if vuln.get("fix_versions") else Severity.HIGH,
                        title=f"Vulnerable Python package: {vuln.get('name')}",
                        description=f"Package {vuln.get('name')} {vuln.get('version')} has known vulnerability: {vuln.get('description', 'No description')}",
                        file_path=str(requirements_file),
                        recommendation=f"Update to version {vuln.get('fix_versions', ['latest'])[0] if vuln.get('fix_versions') else 'latest'}",
                        effort_estimate="low"
                    ))
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.warning(f"Failed to scan Python dependencies: {e}")
        
        return findings

    def _scan_javascript_dependencies(self) -> List[Finding]:
        """Scan JavaScript dependencies using npm audit."""
        findings = []
        frontend_path = Path(self.config.get("frontend_path", "frontend"))
        package_json = frontend_path / "package.json"
        
        if not package_json.exists():
            return findings
        
        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                cwd=str(frontend_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                for vuln_id, vuln in data.get("vulnerabilities", {}).items():
                    severity_map = {
                        "critical": Severity.CRITICAL,
                        "high": Severity.HIGH,
                        "moderate": Severity.MEDIUM,
                        "low": Severity.LOW
                    }
                    findings.append(Finding(
                        category=Category.SECURITY,
                        severity=severity_map.get(vuln.get("severity", "low"), Severity.MEDIUM),
                        title=f"Vulnerable npm package: {vuln.get('name')}",
                        description=f"Package {vuln.get('name')} has {vuln.get('severity')} severity vulnerability",
                        file_path=str(package_json),
                        recommendation=f"Update package to fix vulnerability",
                        effort_estimate="low"
                    ))
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.warning(f"Failed to scan JavaScript dependencies: {e}")
        
        return findings

    def _analyze_authentication(self) -> List[Finding]:
        """Analyze authentication and authorization code."""
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        
        # Patterns indicating potential authentication issues
        patterns = [
            (r'password\s*=\s*["\'].*["\']', "Hardcoded password detected", Severity.CRITICAL),
            (r'authenticate\([^)]*\)\s*(?!if|and|or)', "Authentication without validation", Severity.HIGH),
            (r'@api_view.*\n(?!.*@permission_classes)', "API view without permission classes", Severity.MEDIUM),
        ]
        
        for py_file in backend_path.rglob("*.py"):
            try:
                content = py_file.read_text()
                for pattern, message, severity in patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(Finding(
                            category=Category.SECURITY,
                            severity=severity,
                            title=message,
                            description=f"Potential security issue in authentication code",
                            file_path=str(py_file),
                            line_number=line_num,
                            recommendation="Review authentication implementation and ensure proper security measures",
                            effort_estimate="medium"
                        ))
            except Exception as e:
                self.logger.debug(f"Error analyzing {py_file}: {e}")
        
        return findings

    def _check_sql_injection(self) -> List[Finding]:
        """Check for SQL injection vulnerabilities."""
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        
        # Patterns indicating potential SQL injection
        patterns = [
            (r'\.raw\([^)]*%s[^)]*%', "String formatting in raw SQL", Severity.CRITICAL),
            (r'\.raw\([^)]*\+[^)]*\)', "String concatenation in raw SQL", Severity.CRITICAL),
            (r'cursor\.execute\([^)]*%[^)]*\)', "String formatting in cursor.execute", Severity.CRITICAL),
        ]
        
        for py_file in backend_path.rglob("*.py"):
            try:
                content = py_file.read_text()
                for pattern, message, severity in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(Finding(
                            category=Category.SECURITY,
                            severity=severity,
                            title=f"Potential SQL injection: {message}",
                            description="Raw SQL query with string formatting or concatenation",
                            file_path=str(py_file),
                            line_number=line_num,
                            recommendation="Use parameterized queries instead of string formatting",
                            effort_estimate="medium"
                        ))
            except Exception as e:
                self.logger.debug(f"Error checking SQL injection in {py_file}: {e}")
        
        return findings

    def _check_xss(self) -> List[Finding]:
        """Check for XSS vulnerabilities."""
        findings = []
        frontend_path = Path(self.config.get("frontend_path", "frontend"))
        
        # Patterns indicating potential XSS
        patterns = [
            (r'dangerouslySetInnerHTML', "Use of dangerouslySetInnerHTML", Severity.HIGH),
            (r'innerHTML\s*=', "Direct innerHTML assignment", Severity.HIGH),
        ]
        
        for tsx_file in frontend_path.rglob("*.tsx"):
            try:
                content = tsx_file.read_text()
                for pattern, message, severity in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(Finding(
                            category=Category.SECURITY,
                            severity=severity,
                            title=f"Potential XSS vulnerability: {message}",
                            description="Unsafe HTML rendering detected",
                            file_path=str(tsx_file),
                            line_number=line_num,
                            recommendation="Sanitize user input or use safe rendering methods",
                            effort_estimate="medium"
                        ))
            except Exception as e:
                self.logger.debug(f"Error checking XSS in {tsx_file}: {e}")
        
        return findings

    def _scan_secrets(self) -> List[Finding]:
        """Scan for hardcoded secrets."""
        findings = []
        project_root = Path(self.config.get("project_root", "."))
        
        # Patterns for detecting secrets
        secret_patterns = [
            (r'api[_-]?key\s*=\s*["\'][^"\']{20,}["\']', "API key"),
            (r'secret[_-]?key\s*=\s*["\'][^"\']{20,}["\']', "Secret key"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Password"),
            (r'token\s*=\s*["\'][^"\']{20,}["\']', "Token"),
            (r'aws[_-]?access[_-]?key[_-]?id\s*=\s*["\'][^"\']+["\']', "AWS access key"),
        ]
        
        for py_file in project_root.rglob("*.py"):
            if "test" in str(py_file) or "venv" in str(py_file):
                continue
            try:
                content = py_file.read_text()
                for pattern, secret_type in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(Finding(
                            category=Category.SECURITY,
                            severity=Severity.CRITICAL,
                            title=f"Hardcoded {secret_type} detected",
                            description=f"Potential hardcoded secret found in code",
                            file_path=str(py_file),
                            line_number=line_num,
                            recommendation="Move secrets to environment variables or secure vault",
                            effort_estimate="low"
                        ))
            except Exception as e:
                self.logger.debug(f"Error scanning secrets in {py_file}: {e}")
        
        return findings

    def _check_security_headers(self) -> List[Finding]:
        """Verify security headers configuration."""
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        
        # Check Django settings for security headers
        settings_files = list(backend_path.rglob("settings*.py"))
        
        required_settings = [
            ("SECURE_SSL_REDIRECT", "SSL redirect not enabled"),
            ("SECURE_HSTS_SECONDS", "HSTS not configured"),
            ("SECURE_CONTENT_TYPE_NOSNIFF", "Content type nosniff not enabled"),
            ("X_FRAME_OPTIONS", "X-Frame-Options not configured"),
            ("CSRF_COOKIE_SECURE", "CSRF cookie not secure"),
            ("SESSION_COOKIE_SECURE", "Session cookie not secure"),
        ]
        
        for settings_file in settings_files:
            try:
                content = settings_file.read_text()
                for setting, message in required_settings:
                    if setting not in content:
                        findings.append(Finding(
                            category=Category.SECURITY,
                            severity=Severity.MEDIUM,
                            title=f"Missing security setting: {setting}",
                            description=message,
                            file_path=str(settings_file),
                            recommendation=f"Add {setting} to Django settings",
                            effort_estimate="low"
                        ))
            except Exception as e:
                self.logger.debug(f"Error checking security headers in {settings_file}: {e}")
        
        return findings

    def _check_gdpr_compliance(self) -> List[Finding]:
        """Check GDPR compliance implementation."""
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        
        # Skip GDPR check if backend path doesn't exist (e.g., tools-only directory)
        if not backend_path.exists():
            self.logger.info(f"Skipping GDPR check - backend path does not exist: {backend_path}")
            return findings
        
        # Check for GDPR-related functionality
        gdpr_features = [
            ("data_export", "User data export functionality"),
            ("data_deletion", "User data deletion functionality"),
            ("consent", "User consent management"),
        ]
        
        found_features = set()
        for py_file in backend_path.rglob("*.py"):
            try:
                content = py_file.read_text().lower()
                for feature, _ in gdpr_features:
                    if feature in content:
                        found_features.add(feature)
            except Exception as e:
                self.logger.debug(f"Error checking GDPR in {py_file}: {e}")
        
        for feature, description in gdpr_features:
            if feature not in found_features:
                findings.append(Finding(
                    category=Category.SECURITY,
                    severity=Severity.HIGH,
                    title=f"Missing GDPR feature: {description}",
                    description=f"GDPR compliance requires {description}",
                    file_path=str(backend_path),
                    recommendation=f"Implement {description} to comply with GDPR",
                    effort_estimate="high"
                ))
        
        return findings
