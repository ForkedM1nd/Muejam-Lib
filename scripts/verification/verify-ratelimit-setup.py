#!/usr/bin/env python
"""
Verification script for django-ratelimit Redis backend configuration.
This script verifies that django-ratelimit is properly configured to use Redis.

Usage:
    cd apps/backend
    python ../../scripts/verification/verify-ratelimit-setup.py
"""

import os
import sys
from pathlib import Path
import django

# Add backend to path and setup Django environment
backend_path = Path(__file__).parent.parent.parent / 'apps' / 'backend'
sys.path.insert(0, str(backend_path))
os.chdir(backend_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.core.cache import cache
from django_ratelimit.core import is_ratelimited
from django.test import RequestFactory


def verify_redis_connection():
    """Verify Redis connection is working."""
    print("1. Verifying Redis connection...")
    try:
        cache.set('test_key', 'test_value', 10)
        value = cache.get('test_key')
        if value == 'test_value':
            print("   ✓ Redis connection successful")
            cache.delete('test_key')
            return True
        else:
            print("   ✗ Redis connection failed: value mismatch")
            return False
    except Exception as e:
        print(f"   ✗ Redis connection failed: {e}")
        return False


def verify_ratelimit_settings():
    """Verify django-ratelimit settings are configured."""
    print("\n2. Verifying django-ratelimit settings...")
    
    checks = [
        ('RATELIMIT_USE_CACHE', 'default'),
        ('RATELIMIT_ENABLE', True),
        ('RATE_LIMIT_ENABLED', True),
    ]
    
    all_passed = True
    for setting_name, expected_value in checks:
        actual_value = getattr(settings, setting_name, None)
        if actual_value == expected_value:
            print(f"   ✓ {setting_name} = {actual_value}")
        else:
            print(f"   ✗ {setting_name} = {actual_value} (expected {expected_value})")
            all_passed = False
    
    return all_passed


def verify_ratelimit_functionality():
    """Verify django-ratelimit can track rate limits in Redis."""
    print("\n3. Verifying django-ratelimit functionality...")
    
    try:
        # Create a mock request
        factory = RequestFactory()
        request = factory.get('/test')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        # Test rate limiting with a very low limit
        test_group = 'test_verification'
        test_key = 'ip'
        test_rate = '2/m'  # 2 requests per minute
        
        # First request should not be rate limited
        limited1 = is_ratelimited(
            request=request,
            group=test_group,
            key=test_key,
            rate=test_rate,
            increment=True
        )
        
        # Second request should not be rate limited
        limited2 = is_ratelimited(
            request=request,
            group=test_group,
            key=test_key,
            rate=test_rate,
            increment=True
        )
        
        # Third request should be rate limited
        limited3 = is_ratelimited(
            request=request,
            group=test_group,
            key=test_key,
            rate=test_rate,
            increment=True
        )
        
        if not limited1 and not limited2 and limited3:
            print("   ✓ Rate limiting working correctly")
            print(f"     - Request 1: Not limited (expected)")
            print(f"     - Request 2: Not limited (expected)")
            print(f"     - Request 3: Limited (expected)")
            
            # Clean up test keys from Redis
            cache_key = f'rl:{test_group}:127.0.0.1'
            cache.delete(cache_key)
            
            return True
        else:
            print("   ✗ Rate limiting not working as expected")
            print(f"     - Request 1: {'Limited' if limited1 else 'Not limited'}")
            print(f"     - Request 2: {'Limited' if limited2 else 'Not limited'}")
            print(f"     - Request 3: {'Limited' if limited3 else 'Not limited'}")
            return False
            
    except Exception as e:
        print(f"   ✗ Rate limiting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("django-ratelimit Redis Backend Verification")
    print("=" * 60)
    
    results = []
    
    # Run all checks
    results.append(("Redis Connection", verify_redis_connection()))
    results.append(("Settings Configuration", verify_ratelimit_settings()))
    results.append(("Rate Limiting Functionality", verify_ratelimit_functionality()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All checks passed! django-ratelimit is properly configured with Redis.")
        return 0
    else:
        print("\n✗ Some checks failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
