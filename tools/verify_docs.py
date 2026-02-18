#!/usr/bin/env python
"""
Verification script to check if API documentation is properly configured.
Run this after starting the Django server to verify documentation endpoints.
"""

import sys
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import reverse
from django.conf import settings


def verify_documentation():
    """
    Verify that API documentation is properly configured.
    
    Checks for:
    - drf-spectacular installation
    - Proper Django settings configuration
    - Documentation URL configuration
    
    Returns:
        bool: True if all checks pass, False otherwise
    """
    
    print("=" * 60)
    print("MueJam Library API Documentation Verification")
    print("=" * 60)
    print()
    
    # Check if drf-spectacular is installed
    try:
        import drf_spectacular
        print("✓ drf-spectacular is installed")
        print(f"  Version: {drf_spectacular.__version__}")
    except ImportError:
        print("✗ drf-spectacular is NOT installed")
        print("  Run: pip install drf-spectacular")
        return False
    
    print()
    
    # Check if drf-spectacular is in INSTALLED_APPS
    if 'drf_spectacular' in settings.INSTALLED_APPS:
        print("✓ drf_spectacular is in INSTALLED_APPS")
    else:
        print("✗ drf_spectacular is NOT in INSTALLED_APPS")
        return False
    
    print()
    
    # Check if REST_FRAMEWORK has the correct schema class
    schema_class = settings.REST_FRAMEWORK.get('DEFAULT_SCHEMA_CLASS')
    if schema_class == 'drf_spectacular.openapi.AutoSchema':
        print("✓ REST_FRAMEWORK uses drf_spectacular.openapi.AutoSchema")
    else:
        print(f"✗ REST_FRAMEWORK schema class: {schema_class}")
        print("  Expected: drf_spectacular.openapi.AutoSchema")
        return False
    
    print()
    
    # Check if SPECTACULAR_SETTINGS exists
    if hasattr(settings, 'SPECTACULAR_SETTINGS'):
        print("✓ SPECTACULAR_SETTINGS is configured")
        spectacular_settings = settings.SPECTACULAR_SETTINGS
        print(f"  Title: {spectacular_settings.get('TITLE')}")
        print(f"  Version: {spectacular_settings.get('VERSION')}")
        print(f"  Tags: {len(spectacular_settings.get('TAGS', []))} categories")
    else:
        print("✗ SPECTACULAR_SETTINGS is NOT configured")
        return False
    
    print()
    
    # Check if documentation URLs are configured
    try:
        schema_url = reverse('schema')
        swagger_url = reverse('swagger-ui')
        print("✓ Documentation URLs are configured")
        print(f"  Schema URL: {schema_url}")
        print(f"  Swagger UI URL: {swagger_url}")
    except Exception as e:
        print(f"✗ Documentation URLs are NOT configured: {e}")
        return False
    
    print()
    print("=" * 60)
    print("All checks passed! ✓")
    print("=" * 60)
    print()
    print("To access the API documentation:")
    print(f"  1. Start the Django server: python manage.py runserver")
    print(f"  2. Open your browser to: http://localhost:8000/v1/docs/")
    print(f"  3. View the OpenAPI schema at: http://localhost:8000/v1/schema/")
    print()
    print("To generate a static schema file:")
    print(f"  python manage.py spectacular --color --file schema.yml")
    print()
    
    return True


if __name__ == '__main__':
    success = verify_documentation()
    sys.exit(0 if success else 1)
