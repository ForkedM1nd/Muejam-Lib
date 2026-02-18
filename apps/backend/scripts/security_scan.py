"""
Security Scan Script

This script performs a comprehensive security scan of the application,
checking for common security issues and misconfigurations.

Requirements: 4.5
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from infrastructure.https_enforcement import get_https_status


class SecurityScanner:
    """Comprehensive security scanner for Django application."""
    
    def __init__(self):
        self.findings = []
        self.warnings = []
        self.passed = []
    
    def run_all_checks(self):
        """Run all security checks."""
        print("=" * 80)
        print("SECURITY SCAN REPORT")
        print("=" * 80)
        print()
        
        self.check_debug_mode()
        self.check_secret_key()
        self.check_https_configuration()
        self.check_security_headers()
        self.check_cookie_security()
        self.check_csrf_protection()
        self.check_allowed_hosts()
        self.check_database_security()
        self.check_secrets_manager()
        self.check_cors_configuration()
        
        self.print_summary()
    
    def check_debug_mode(self):
        """Check if DEBUG mode is disabled in production."""
        print("[*] Checking DEBUG mode...")
        
        debug = getattr(settings, 'DEBUG', True)
        environment = getattr(settings, 'ENVIRONMENT', 'development')
        
        if environment == 'production' and debug:
            self.findings.append({
                'severity': 'CRITICAL',
                'check': 'DEBUG Mode',
                'issue': 'DEBUG is True in production environment',
                'recommendation': 'Set DEBUG=False in production'
            })
        elif debug:
            self.warnings.append({
                'check': 'DEBUG Mode',
                'issue': f'DEBUG is True in {environment} environment',
                'recommendation': 'Ensure DEBUG=False before deploying to production'
            })
        else:
            self.passed.append('DEBUG mode is disabled')
    
    def check_secret_key(self):
        """Check SECRET_KEY configuration."""
        print("[*] Checking SECRET_KEY...")
        
        secret_key = getattr(settings, 'SECRET_KEY', '')
        
        # Check for insecure patterns
        insecure_patterns = [
            'django-insecure',
            'change-this',
            'your-secret-key',
            'example',
            'test-key'
        ]
        
        if any(pattern in secret_key.lower() for pattern in insecure_patterns):
            self.findings.append({
                'severity': 'CRITICAL',
                'check': 'SECRET_KEY',
                'issue': 'SECRET_KEY appears to be an example/insecure value',
                'recommendation': 'Generate a secure SECRET_KEY using: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"'
            })
        elif len(secret_key) < 50:
            self.findings.append({
                'severity': 'HIGH',
                'check': 'SECRET_KEY',
                'issue': f'SECRET_KEY is too short ({len(secret_key)} chars)',
                'recommendation': 'SECRET_KEY should be at least 50 characters'
            })
        else:
            self.passed.append('SECRET_KEY is properly configured')
    
    def check_https_configuration(self):
        """Check HTTPS enforcement configuration."""
        print("[*] Checking HTTPS configuration...")
        
        https_status = get_https_status()
        environment = https_status.get('environment', 'development')
        
        if environment == 'production':
            if not https_status.get('enforce_https'):
                self.findings.append({
                    'severity': 'CRITICAL',
                    'check': 'HTTPS Enforcement',
                    'issue': 'HTTPS enforcement is disabled in production',
                    'recommendation': 'Set SECURE_SSL_REDIRECT=True'
                })
            else:
                self.passed.append('HTTPS enforcement is enabled')
            
            if not https_status.get('hsts_enabled'):
                self.findings.append({
                    'severity': 'HIGH',
                    'check': 'HSTS',
                    'issue': 'HSTS is not configured',
                    'recommendation': 'Set SECURE_HSTS_SECONDS=31536000'
                })
            elif https_status.get('hsts_seconds', 0) < 31536000:
                self.warnings.append({
                    'check': 'HSTS',
                    'issue': f'HSTS max-age is {https_status.get("hsts_seconds")} seconds',
                    'recommendation': 'Recommended minimum is 31536000 (1 year)'
                })
            else:
                self.passed.append('HSTS is properly configured')
        else:
            self.passed.append(f'HTTPS checks skipped in {environment} environment')
    
    def check_security_headers(self):
        """Check security headers configuration."""
        print("[*] Checking security headers...")
        
        # X-Content-Type-Options
        if not getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False):
            self.findings.append({
                'severity': 'MEDIUM',
                'check': 'X-Content-Type-Options',
                'issue': 'SECURE_CONTENT_TYPE_NOSNIFF is not enabled',
                'recommendation': 'Set SECURE_CONTENT_TYPE_NOSNIFF=True'
            })
        else:
            self.passed.append('X-Content-Type-Options header is configured')
        
        # X-Frame-Options
        x_frame_options = getattr(settings, 'X_FRAME_OPTIONS', None)
        if x_frame_options not in ['DENY', 'SAMEORIGIN']:
            self.findings.append({
                'severity': 'MEDIUM',
                'check': 'X-Frame-Options',
                'issue': 'X_FRAME_OPTIONS is not properly configured',
                'recommendation': 'Set X_FRAME_OPTIONS="DENY" or "SAMEORIGIN"'
            })
        else:
            self.passed.append(f'X-Frame-Options is set to {x_frame_options}')
        
        # CSP
        csp_default_src = getattr(settings, 'CSP_DEFAULT_SRC', None)
        if not csp_default_src:
            self.warnings.append({
                'check': 'Content-Security-Policy',
                'issue': 'CSP_DEFAULT_SRC is not configured',
                'recommendation': 'Configure Content Security Policy headers'
            })
        else:
            self.passed.append('Content Security Policy is configured')
    
    def check_cookie_security(self):
        """Check cookie security settings."""
        print("[*] Checking cookie security...")
        
        environment = getattr(settings, 'ENVIRONMENT', 'development')
        
        if environment == 'production':
            # Session cookie
            if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
                self.findings.append({
                    'severity': 'HIGH',
                    'check': 'Session Cookie Security',
                    'issue': 'SESSION_COOKIE_SECURE is False',
                    'recommendation': 'Set SESSION_COOKIE_SECURE=True in production'
                })
            else:
                self.passed.append('Session cookies are secure')
            
            if not getattr(settings, 'SESSION_COOKIE_HTTPONLY', False):
                self.findings.append({
                    'severity': 'HIGH',
                    'check': 'Session Cookie HttpOnly',
                    'issue': 'SESSION_COOKIE_HTTPONLY is False',
                    'recommendation': 'Set SESSION_COOKIE_HTTPONLY=True'
                })
            else:
                self.passed.append('Session cookies are HttpOnly')
            
            # CSRF cookie
            if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
                self.findings.append({
                    'severity': 'HIGH',
                    'check': 'CSRF Cookie Security',
                    'issue': 'CSRF_COOKIE_SECURE is False',
                    'recommendation': 'Set CSRF_COOKIE_SECURE=True in production'
                })
            else:
                self.passed.append('CSRF cookies are secure')
        else:
            self.passed.append(f'Cookie security checks skipped in {environment} environment')
    
    def check_csrf_protection(self):
        """Check CSRF protection configuration."""
        print("[*] Checking CSRF protection...")
        
        middleware = getattr(settings, 'MIDDLEWARE', [])
        
        if 'django.middleware.csrf.CsrfViewMiddleware' not in middleware:
            self.findings.append({
                'severity': 'CRITICAL',
                'check': 'CSRF Protection',
                'issue': 'CsrfViewMiddleware is not in MIDDLEWARE',
                'recommendation': 'Add django.middleware.csrf.CsrfViewMiddleware to MIDDLEWARE'
            })
        else:
            self.passed.append('CSRF protection is enabled')
    
    def check_allowed_hosts(self):
        """Check ALLOWED_HOSTS configuration."""
        print("[*] Checking ALLOWED_HOSTS...")
        
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        environment = getattr(settings, 'ENVIRONMENT', 'development')
        
        if environment == 'production':
            if not allowed_hosts or '*' in allowed_hosts:
                self.findings.append({
                    'severity': 'HIGH',
                    'check': 'ALLOWED_HOSTS',
                    'issue': 'ALLOWED_HOSTS is empty or contains wildcard',
                    'recommendation': 'Configure specific allowed hosts for production'
                })
            else:
                self.passed.append(f'ALLOWED_HOSTS is configured with {len(allowed_hosts)} host(s)')
        else:
            self.passed.append(f'ALLOWED_HOSTS checks skipped in {environment} environment')
    
    def check_database_security(self):
        """Check database security configuration."""
        print("[*] Checking database security...")
        
        databases = getattr(settings, 'DATABASES', {})
        default_db = databases.get('default', {})
        
        # Check for connection pooling
        conn_max_age = default_db.get('CONN_MAX_AGE', 0)
        if conn_max_age == 0:
            self.warnings.append({
                'check': 'Database Connection Pooling',
                'issue': 'CONN_MAX_AGE is 0 (no connection pooling)',
                'recommendation': 'Configure connection pooling with CONN_MAX_AGE > 0'
            })
        else:
            self.passed.append(f'Database connection pooling is configured (CONN_MAX_AGE={conn_max_age})')
        
        # Check for SSL
        options = default_db.get('OPTIONS', {})
        if 'sslmode' not in options and getattr(settings, 'ENVIRONMENT', 'development') == 'production':
            self.warnings.append({
                'check': 'Database SSL',
                'issue': 'Database SSL is not configured',
                'recommendation': 'Configure SSL for database connections in production'
            })
        else:
            self.passed.append('Database configuration reviewed')
    
    def check_secrets_manager(self):
        """Check secrets manager integration."""
        print("[*] Checking secrets manager...")
        
        use_secrets_manager = getattr(settings, 'USE_SECRETS_MANAGER', False)
        environment = getattr(settings, 'ENVIRONMENT', 'development')
        
        if environment == 'production' and not use_secrets_manager:
            self.warnings.append({
                'check': 'Secrets Manager',
                'issue': 'Secrets Manager is not enabled in production',
                'recommendation': 'Set USE_SECRETS_MANAGER=True and migrate secrets to AWS Secrets Manager'
            })
        elif use_secrets_manager:
            self.passed.append('Secrets Manager is enabled')
        else:
            self.passed.append(f'Secrets Manager checks skipped in {environment} environment')
    
    def check_cors_configuration(self):
        """Check CORS configuration."""
        print("[*] Checking CORS configuration...")
        
        cors_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        
        if not cors_origins:
            self.warnings.append({
                'check': 'CORS Configuration',
                'issue': 'CORS_ALLOWED_ORIGINS is empty',
                'recommendation': 'Configure specific allowed origins'
            })
        elif '*' in str(cors_origins):
            self.findings.append({
                'severity': 'MEDIUM',
                'check': 'CORS Configuration',
                'issue': 'CORS allows all origins (wildcard)',
                'recommendation': 'Configure specific allowed origins instead of wildcard'
            })
        else:
            self.passed.append(f'CORS is configured with {len(cors_origins)} origin(s)')
    
    def print_summary(self):
        """Print scan summary."""
        print()
        print("=" * 80)
        print("SCAN SUMMARY")
        print("=" * 80)
        print()
        
        # Print critical findings
        if self.findings:
            print(f"CRITICAL/HIGH FINDINGS: {len(self.findings)}")
            print("-" * 80)
            for finding in self.findings:
                print(f"[{finding['severity']}] {finding['check']}")
                print(f"  Issue: {finding['issue']}")
                print(f"  Recommendation: {finding['recommendation']}")
                print()
        
        # Print warnings
        if self.warnings:
            print(f"WARNINGS: {len(self.warnings)}")
            print("-" * 80)
            for warning in self.warnings:
                print(f"[WARNING] {warning['check']}")
                print(f"  Issue: {warning['issue']}")
                print(f"  Recommendation: {warning['recommendation']}")
                print()
        
        # Print passed checks
        if self.passed:
            print(f"PASSED CHECKS: {len(self.passed)}")
            print("-" * 80)
            for check in self.passed:
                print(f"[PASS] {check}")
            print()
        
        # Overall status
        print("=" * 80)
        if self.findings:
            print(f"STATUS: FAILED - {len(self.findings)} critical/high findings")
            print("ACTION REQUIRED: Fix critical findings before deploying to production")
        elif self.warnings:
            print(f"STATUS: WARNING - {len(self.warnings)} warnings")
            print("RECOMMENDATION: Address warnings to improve security posture")
        else:
            print("STATUS: PASSED - No critical findings")
            print("All security checks passed!")
        print("=" * 80)


def main():
    """Run security scan."""
    scanner = SecurityScanner()
    scanner.run_all_checks()
    
    # Exit with error code if critical findings
    if scanner.findings:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
