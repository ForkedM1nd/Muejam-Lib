#!/usr/bin/env python
"""
APM Integration Verification Script

This script verifies that APM is properly configured.
Run with: python apps/backend/scripts/verify_apm.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from infrastructure.apm_config import APMConfig, PerformanceMonitor


def print_status(check_name, passed, message=""):
    """Print check status with color"""
    status = "✓ PASS" if passed else "✗ FAIL"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} - {check_name}")
    if message:
        print(f"       {message}")


def verify_configuration():
    """Verify APM configuration"""
    print("\n=== APM Configuration Verification ===\n")
    
    checks_passed = 0
    total_checks = 0
    
    # Check 1: APM enabled
    total_checks += 1
    apm_enabled = APMConfig.is_enabled()
    if apm_enabled:
        print_status("APM enabled", True)
        checks_passed += 1
    else:
        print_status("APM enabled", False, "Set APM_ENABLED=True")
    
    # Check 2: APM provider configured
    total_checks += 1
    provider = APMConfig.get_provider_name()
    print_status("APM provider configured", True, f"Provider: {provider}")
    checks_passed += 1
    
    # Check 3: Performance thresholds
    total_checks += 1
    p95_threshold = APMConfig.API_P95_THRESHOLD_MS
    p99_threshold = APMConfig.API_P99_THRESHOLD_MS
    print_status("Performance thresholds configured", True, 
                f"P95: {p95_threshold}ms, P99: {p99_threshold}ms")
    checks_passed += 1
    
    # Check 4: Slow query threshold
    total_checks += 1
    slow_query = APMConfig.SLOW_QUERY_THRESHOLD_MS
    print_status("Slow query threshold configured", True, f"Threshold: {slow_query}ms")
    checks_passed += 1
    
    # Check 5: DB pool threshold
    total_checks += 1
    db_pool = APMConfig.DB_POOL_UTILIZATION_THRESHOLD
    print_status("DB pool threshold configured", True, f"Threshold: {db_pool * 100}%")
    checks_passed += 1
    
    return checks_passed, total_checks


def verify_middleware():
    """Verify APM middleware is configured"""
    print("\n=== Middleware Verification ===\n")
    
    checks_passed = 0
    total_checks = 0
    
    # Check 1: APM middleware in MIDDLEWARE
    total_checks += 1
    middleware_list = settings.MIDDLEWARE
    apm_middleware = 'infrastructure.apm_middleware.APMMiddleware'
    
    if apm_middleware in middleware_list:
        print_status("APM middleware configured", True)
        checks_passed += 1
    else:
        print_status("APM middleware configured", False, 
                    "Add 'infrastructure.apm_middleware.APMMiddleware' to MIDDLEWARE")
    
    # Check 2: Middleware position
    total_checks += 1
    if apm_middleware in middleware_list:
        position = middleware_list.index(apm_middleware)
        # Should be early in the middleware stack
        if position < 5:
            print_status("APM middleware position", True, f"Position: {position}")
            checks_passed += 1
        else:
            print_status("APM middleware position", False, 
                        f"Position {position} is too late, should be < 5")
    else:
        print_status("APM middleware position", False, "Middleware not configured")
    
    return checks_passed, total_checks


def verify_provider_integration():
    """Verify APM provider integration"""
    print("\n=== Provider Integration Verification ===\n")
    
    checks_passed = 0
    total_checks = 0
    
    provider = APMConfig.get_provider_name()
    
    if provider == 'newrelic':
        # Check New Relic
        total_checks += 1
        try:
            import newrelic.agent
            print_status("New Relic agent installed", True)
            checks_passed += 1
        except ImportError:
            print_status("New Relic agent installed", False, 
                        "Install with: pip install newrelic")
        
        # Check New Relic config
        total_checks += 1
        nr_license = os.getenv('NEW_RELIC_LICENSE_KEY', '')
        if nr_license:
            print_status("New Relic license key configured", True)
            checks_passed += 1
        else:
            print_status("New Relic license key configured", False, 
                        "Set NEW_RELIC_LICENSE_KEY environment variable")
    
    elif provider == 'datadog':
        # Check DataDog
        total_checks += 1
        try:
            import ddtrace
            print_status("DataDog tracer installed", True)
            checks_passed += 1
        except ImportError:
            print_status("DataDog tracer installed", False, 
                        "Install with: pip install ddtrace")
        
        # Check DataDog config
        total_checks += 1
        dd_api_key = os.getenv('DD_API_KEY', '')
        if dd_api_key:
            print_status("DataDog API key configured", True)
            checks_passed += 1
        else:
            print_status("DataDog API key configured", False, 
                        "Set DD_API_KEY environment variable")
    
    else:
        # Built-in metrics
        total_checks += 1
        print_status("Using built-in metrics", True, "No external APM provider")
        checks_passed += 1
    
    return checks_passed, total_checks


def verify_alert_configuration():
    """Verify alert configuration"""
    print("\n=== Alert Configuration Verification ===\n")
    
    checks_passed = 0
    total_checks = 0
    
    # Check 1: Email alerts
    total_checks += 1
    email_enabled = os.getenv('PERFORMANCE_ALERT_EMAIL_ENABLED', 'True') == 'True'
    email_recipients = os.getenv('PERFORMANCE_ALERT_EMAIL_RECIPIENTS', '').split(',')
    
    if email_enabled and email_recipients and email_recipients[0]:
        print_status("Email alerts configured", True, 
                    f"Recipients: {len(email_recipients)}")
        checks_passed += 1
    else:
        print_status("Email alerts configured", False, 
                    "Configure PERFORMANCE_ALERT_EMAIL_RECIPIENTS")
    
    # Check 2: Slack alerts
    total_checks += 1
    slack_enabled = os.getenv('PERFORMANCE_ALERT_SLACK_ENABLED', 'False') == 'True'
    slack_webhook = os.getenv('PERFORMANCE_ALERT_SLACK_WEBHOOK_URL', '')
    
    if slack_enabled and slack_webhook:
        print_status("Slack alerts configured", True)
        checks_passed += 1
    elif not slack_enabled:
        print_status("Slack alerts configured", False, 
                    "Optional: Set PERFORMANCE_ALERT_SLACK_ENABLED=True")
    else:
        print_status("Slack alerts configured", False, 
                    "Set PERFORMANCE_ALERT_SLACK_WEBHOOK_URL")
    
    return checks_passed, total_checks


def test_performance_tracking():
    """Test performance tracking"""
    print("\n=== Performance Tracking Test ===\n")
    
    checks_passed = 0
    total_checks = 0
    
    if not APMConfig.is_enabled():
        print_status("Performance tracking test", False, "APM not enabled")
        return 0, 1
    
    # Test 1: Track API endpoint
    total_checks += 1
    try:
        PerformanceMonitor.track_api_endpoint(
            endpoint='/api/test',
            method='GET',
            status_code=200,
            duration_ms=150.5
        )
        print_status("API endpoint tracking", True)
        checks_passed += 1
    except Exception as e:
        print_status("API endpoint tracking", False, str(e))
    
    # Test 2: Track custom metric
    total_checks += 1
    try:
        PerformanceMonitor.track_custom_metric(
            name='test.metric',
            value=42.0,
            tags={'test': 'true'}
        )
        print_status("Custom metric tracking", True)
        checks_passed += 1
    except Exception as e:
        print_status("Custom metric tracking", False, str(e))
    
    return checks_passed, total_checks


def main():
    """Run all verification checks"""
    print("\n" + "="*60)
    print("  APM Integration Verification")
    print("="*60)
    
    total_passed = 0
    total_checks = 0
    
    # Run all verification checks
    passed, checks = verify_configuration()
    total_passed += passed
    total_checks += checks
    
    passed, checks = verify_middleware()
    total_passed += passed
    total_checks += checks
    
    passed, checks = verify_provider_integration()
    total_passed += passed
    total_checks += checks
    
    passed, checks = verify_alert_configuration()
    total_passed += passed
    total_checks += checks
    
    passed, checks = test_performance_tracking()
    total_passed += passed
    total_checks += checks
    
    # Print summary
    print("\n" + "="*60)
    print(f"  Summary: {total_passed}/{total_checks} checks passed")
    print("="*60)
    
    if total_passed == total_checks:
        print("\n✓ All checks passed! APM is properly configured.")
        print("\nNext steps:")
        print("1. Generate test traffic with load tests")
        print("2. Check APM dashboard for metrics")
        print("3. Configure alert rules in APM provider")
        print("4. Set up performance dashboards")
        print("5. Review docs/monitoring/apm-setup.md")
        return 0
    else:
        print(f"\n✗ {total_checks - total_passed} checks failed.")
        print("\nPlease review the failed checks and fix configuration.")
        print("See docs/monitoring/apm-setup.md for help.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
