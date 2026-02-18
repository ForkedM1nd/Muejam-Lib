"""Test script to verify all fixes are working."""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(method, path, expected_status, description):
    """Test an endpoint and print results."""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json={}, timeout=5)
        
        status_icon = "✅" if response.status_code == expected_status else "❌"
        print(f"{status_icon} {method} {path}")
        print(f"   Expected: {expected_status}, Got: {response.status_code}")
        print(f"   {description}")
        
        if response.status_code != expected_status:
            print(f"   Response: {response.text[:200]}")
        
        return response.status_code == expected_status
    except Exception as e:
        print(f"❌ {method} {path}")
        print(f"   Error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 80)
    print("TESTING FIXED ENDPOINTS")
    print("=" * 80)
    print()
    
    tests = [
        # Discovery endpoints (previously had import errors)
        ("GET", "/v1/discover/trending/", 200, "Trending stories - Fixed StorySerializer import"),
        ("GET", "/v1/discover/new-and-noteworthy/", 200, "New and noteworthy - Fixed StorySerializer import"),
        ("GET", "/v1/discover/staff-picks/", 200, "Staff picks - Fixed StorySerializer import"),
        
        # Legal documents (previously 404)
        ("GET", "/v1/legal/documents/terms", 200, "Terms of Service - Seeded legal documents"),
        ("GET", "/v1/legal/documents/privacy", 200, "Privacy Policy - Seeded legal documents"),
        
        # Admin endpoints (verify namespace fix)
        ("GET", "/v1/admin/dashboard", 401, "Admin dashboard - Should require auth"),
        ("GET", "/v1/admin/health", 200, "Admin health check - Should be public"),
        
        # Django admin (moved to django-admin)
        ("GET", "/django-admin/", 302, "Django admin - Moved from /admin/ to /django-admin/"),
        
        # Core endpoints (should still work)
        ("GET", "/health", 200, "Health check"),
        ("GET", "/v1/search/stories?q=test", 200, "Search stories"),
        ("GET", "/v1/help/categories/", 200, "Help categories"),
    ]
    
    passed = 0
    failed = 0
    
    for method, path, expected, description in tests:
        if test_endpoint(method, path, expected, description):
            passed += 1
        else:
            failed += 1
        print()
    
    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Backend is production ready!")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Review the output above.")

if __name__ == "__main__":
    main()
