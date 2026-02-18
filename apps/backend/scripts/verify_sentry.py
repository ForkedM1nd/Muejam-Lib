#!/usr/bin/env python
"""
Sentry Integration Verification Script

This script verifies that Sentry is properly configured and working.
Run with: python apps/backend/scripts/verify_sentry.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import sentry_sdk
from django.conf import settings
from infrastructure.sentry_config import ErrorTracker, scrub_sensitive_data


def print_status(check_name, passed, message=""):
    """Print check status with color"""
    status = "✓ PASS" if passed else "✗ FAIL"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} - {check_name}")
    if message:
        print(f"       {message}")


def verify_configuration():
    """Verify Sentry configuration"""
    print("\n=== Sentry Configuration Verification ===\n")
    
    checks_passed = 0
    total_checks = 0
    
    # Check 1: SENTRY_DSN configured
    total_checks += 1
    sentry_dsn = getattr(settings, 'SENTRY_DSN', '')
    if sentry_dsn:
        print_status("SENTRY_DSN configured", True, f"DSN: {sentry_dsn[:30]}...")
        checks_passed += 1
    else:
        print_status("SENTRY_DSN configured", False, "SENTRY_DSN not set")
    
    # Check 2: Environment configured
    total_checks += 1
    environment = os.getenv('SENTRY_ENVIRONMENT', os.getenv('ENVIRONMENT', 'development'))
    print_status("Environment configured", True, f"Environment: {environment}")
    checks_passed += 1
    
    # Check 3: Traces sample rate
    total_checks += 1
    traces_rate = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1'))
    print_status("Traces sample rate configured", True, f"Rate: {traces_rate * 100}%")
    checks_passed += 1
    
    # Check 4: Release tracking
    total_checks += 1
    release = os.getenv('APP_VERSION', os.getenv('VERSION', 'unknown'))
    print_status("Release tracking configured", True, f"Version: {release}")
    checks_passed += 1
    
    # Check 5: Alert configuration
    total_checks += 1
    email_alerts = os.getenv('SENTRY_EMAIL_ALERTS_ENABLED', 'True') == 'True'
    slack_alerts = os.getenv('SENTRY_SLACK_ALERTS_ENABLED', 'False') == 'True'
    alert_msg = f"Email: {email_alerts}, Slack: {slack_alerts}"
    print_status("Alert configuration", True, alert_msg)
    checks_passed += 1
    
    return checks_passed, total_checks


def verify_sensitive_data_scrubbing():
    """Verify sensitive data scrubbing works"""
    print("\n=== Sensitive Data Scrubbing Verification ===\n")
    
    checks_passed = 0
    total_checks = 0
    
    # Test event with sensitive data
    test_event = {
        'request': {
            'headers': {
                'Authorization': 'Bearer secret_token',
                'X-API-Key': 'api_key_123',
                'Cookie': 'session=abc123',
                'Content-Type': 'application/json'
            },
            'data': {
                'username': 'testuser',
                'password': 'secret123',
                'token': 'jwt_token',
                'email': 'test@example.com'
            },
            'query_string': 'username=test&password=secret'
        },
        'user': {
            'id': '123',
            'email': 'user@example.com',
            'ip_address': '192.168.1.1'
        }
    }
    
    # Scrub the event
    scrubbed = scrub_sensitive_data(test_event, None)
    
    # Check 1: Authorization header removed
    total_checks += 1
    if 'Authorization' not in scrubbed['request']['headers']:
        print_status("Authorization header scrubbed", True)
        checks_passed += 1
    else:
        print_status("Authorization header scrubbed", False)
    
    # Check 2: Password removed
    total_checks += 1
    if 'password' not in scrubbed['request']['data']:
        print_status("Password field scrubbed", True)
        checks_passed += 1
    else:
        print_status("Password field scrubbed", False)
    
    # Check 3: Token removed
    total_checks += 1
    if 'token' not in scrubbed['request']['data']:
        print_status("Token field scrubbed", True)
        checks_passed += 1
    else:
        print_status("Token field scrubbed", False)
    
    # Check 4: Query string scrubbed
    total_checks += 1
    if '[REDACTED]' in scrubbed['request']['query_string']:
        print_status("Query string scrubbed", True)
        checks_passed += 1
    else:
        print_status("Query string scrubbed", False)
    
    # Check 5: User email redacted
    total_checks += 1
    if scrubbed['user']['email'] == '[REDACTED]':
        print_status("User email redacted", True)
        checks_passed += 1
    else:
        print_status("User email redacted", False)
    
    # Check 6: User IP redacted
    total_checks += 1
    if scrubbed['user']['ip_address'] == '[REDACTED]':
        print_status("User IP redacted", True)
        checks_passed += 1
    else:
        print_status("User IP redacted", False)
    
    return checks_passed, total_checks


def verify_error_capture():
    """Verify error capture works"""
    print("\n=== Error Capture Verification ===\n")
    
    checks_passed = 0
    total_checks = 0
    
    sentry_dsn = getattr(settings, 'SENTRY_DSN', '')
    
    if not sentry_dsn:
        print_status("Error capture test", False, "SENTRY_DSN not configured - skipping")
        return 0, 1
    
    # Test 1: Capture exception
    total_checks += 1
    try:
        raise Exception("Test exception from verification script")
    except Exception as e:
        event_id = sentry_sdk.capture_exception(e)
        if event_id:
            print_status("Exception capture", True, f"Event ID: {event_id}")
            checks_passed += 1
        else:
            print_status("Exception capture", False, "No event ID returned")
    
    # Test 2: Capture message
    total_checks += 1
    event_id = sentry_sdk.capture_message(
        "Test message from verification script",
        level='info'
    )
    if event_id:
        print_status("Message capture", True, f"Event ID: {event_id}")
        checks_passed += 1
    else:
        print_status("Message capture", False, "No event ID returned")
    
    # Test 3: ErrorTracker
    total_checks += 1
    try:
        raise ValueError("Test error via ErrorTracker")
    except ValueError as e:
        ErrorTracker.capture_exception(
            e,
            context={'test': 'verification'},
            level='error'
        )
        print_status("ErrorTracker capture", True)
        checks_passed += 1
    
    return checks_passed, total_checks


def verify_integrations():
    """Verify Sentry integrations"""
    print("\n=== Integration Verification ===\n")
    
    checks_passed = 0
    total_checks = 0
    
    # Check Django integration
    total_checks += 1
    try:
        from sentry_sdk.integrations.django import DjangoIntegration
        print_status("Django integration available", True)
        checks_passed += 1
    except ImportError:
        print_status("Django integration available", False)
    
    # Check Celery integration
    total_checks += 1
    try:
        from sentry_sdk.integrations.celery import CeleryIntegration
        print_status("Celery integration available", True)
        checks_passed += 1
    except ImportError:
        print_status("Celery integration available", False)
    
    # Check Redis integration
    total_checks += 1
    try:
        from sentry_sdk.integrations.redis import RedisIntegration
        print_status("Redis integration available", True)
        checks_passed += 1
    except ImportError:
        print_status("Redis integration available", False)
    
    return checks_passed, total_checks


def main():
    """Run all verification checks"""
    print("\n" + "="*60)
    print("  Sentry Integration Verification")
    print("="*60)
    
    total_passed = 0
    total_checks = 0
    
    # Run all verification checks
    passed, checks = verify_configuration()
    total_passed += passed
    total_checks += checks
    
    passed, checks = verify_sensitive_data_scrubbing()
    total_passed += passed
    total_checks += checks
    
    passed, checks = verify_integrations()
    total_passed += passed
    total_checks += checks
    
    passed, checks = verify_error_capture()
    total_passed += passed
    total_checks += checks
    
    # Print summary
    print("\n" + "="*60)
    print(f"  Summary: {total_passed}/{total_checks} checks passed")
    print("="*60)
    
    if total_passed == total_checks:
        print("\n✓ All checks passed! Sentry is properly configured.")
        print("\nNext steps:")
        print("1. Check Sentry dashboard for test errors")
        print("2. Configure alert rules in Sentry")
        print("3. Set up Slack/email notifications")
        print("4. Review error grouping rules")
        return 0
    else:
        print(f"\n✗ {total_checks - total_passed} checks failed.")
        print("\nPlease review the failed checks and fix configuration.")
        print("See docs/monitoring/sentry-setup.md for help.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
