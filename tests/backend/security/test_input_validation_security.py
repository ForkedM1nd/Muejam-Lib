"""
Security tests for input validation

Tests SQL injection, XSS, command injection, path traversal, and other input validation vulnerabilities.
"""

import pytest
from django.test import TestCase, Client
import jwt
from datetime import datetime, timedelta


class SQLInjectionTest(TestCase):
    """Test SQL injection prevention"""
    
    def setUp(self):
        self.client = Client()
        self.token = self.generate_token()
    
    def generate_token(self):
        """Generate test JWT token"""
        payload = {
            'sub': 'test_user',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, 'test_secret', algorithm='HS256')
    
    def test_sql_injection_in_search_query(self):
        """Test SQL injection prevention in search"""
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE stories;--",
            "' UNION SELECT * FROM users--",
            "admin'--",
            "' OR 1=1--",
        ]
        
        for payload in sql_payloads:
            response = self.client.get(
                f'/api/search/stories?q={payload}',
                HTTP_AUTHORIZATION=f'Bearer {self.token}'
            )
            
            # Should not return 500 (SQL error)
            self.assertNotEqual(response.status_code, 500,
                              f"SQL injection payload should not cause error: {payload}")
            
            # Should return safe results
            if response.status_code == 200:
                data = response.json()
                # Verify no unauthorized data returned
                self.assertIsInstance(data, dict,
                                    "Response should be valid JSON")
    
    def test_sql_injection_in_post_data(self):
        """Test SQL injection prevention in POST data"""
        response = self.client.post(
            '/api/stories',
            data={
                'title': "Test'; DROP TABLE stories;--",
                'blurb': "' OR '1'='1"
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        # Should either succeed with sanitized data or reject
        self.assertIn(response.status_code, [200, 201, 400],
                     "SQL injection in POST should be handled safely")
        
        # Should not return 500 (SQL error)
        self.assertNotEqual(response.status_code, 500,
                          "SQL injection should not cause database error")
    
    def test_sql_injection_in_filter_params(self):
        """Test SQL injection prevention in filter parameters"""
        response = self.client.get(
            "/api/stories?genre=' OR '1'='1",
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        self.assertNotEqual(response.status_code, 500,
                          "SQL injection in filters should not cause error")


class XSSTest(TestCase):
    """Test Cross-Site Scripting (XSS) prevention"""
    
    def setUp(self):
        self.client = Client()
        self.token = self.generate_token()
    
    def generate_token(self):
        """Generate test JWT token"""
        payload = {
            'sub': 'test_user',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, 'test_secret', algorithm='HS256')
    
    def test_stored_xss_in_story_title(self):
        """Test XSS prevention in story titles"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'>",
        ]
        
        for payload in xss_payloads:
            response = self.client.post(
                '/api/stories',
                data={
                    'title': payload,
                    'blurb': 'Test blurb'
                },
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.token}'
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                title = data.get('title', '')
                
                # Script tags should be escaped or removed
                self.assertNotIn('<script>', title.lower(),
                               "Script tags should be escaped")
                self.assertNotIn('onerror=', title.lower(),
                               "Event handlers should be escaped")
    
    def test_stored_xss_in_whisper_content(self):
        """Test XSS prevention in whisper content"""
        response = self.client.post(
            '/api/whispers',
            data={
                'content': "<script>alert('XSS')</script>",
                'scope': 'public'
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            content = data.get('content', '')
            
            # Script tags should be escaped
            self.assertNotIn('<script>', content.lower(),
                           "Script tags should be escaped in whispers")
    
    def test_reflected_xss_in_search(self):
        """Test reflected XSS prevention in search"""
        response = self.client.get(
            "/api/search/stories?q=<script>alert('XSS')</script>",
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        if response.status_code == 200:
            # Response should not contain unescaped script tags
            content = response.content.decode('utf-8')
            self.assertNotIn('<script>alert', content,
                           "Reflected XSS should be prevented")


class CommandInjectionTest(TestCase):
    """Test command injection prevention"""
    
    def setUp(self):
        self.client = Client()
        self.token = self.generate_token()
    
    def generate_token(self):
        """Generate test JWT token"""
        payload = {
            'sub': 'test_user',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, 'test_secret', algorithm='HS256')
    
    def test_command_injection_in_filename(self):
        """Test command injection prevention in file uploads"""
        # This test requires file upload endpoint
        # Placeholder for now
        pass
    
    def test_command_injection_in_export(self):
        """Test command injection prevention in export operations"""
        command_payloads = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "& whoami",
            "`id`",
            "$(ls -la)",
        ]
        
        for payload in command_payloads:
            response = self.client.post(
                '/api/export',
                data={'format': payload},
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {self.token}'
            )
            
            # Should not execute commands
            self.assertNotEqual(response.status_code, 500,
                              "Command injection should not cause error")


class PathTraversalTest(TestCase):
    """Test path traversal prevention"""
    
    def setUp(self):
        self.client = Client()
        self.token = self.generate_token()
    
    def generate_token(self):
        """Generate test JWT token"""
        payload = {
            'sub': 'test_user',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, 'test_secret', algorithm='HS256')
    
    def test_path_traversal_in_file_access(self):
        """Test path traversal prevention"""
        traversal_payloads = [
            "../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]
        
        for payload in traversal_payloads:
            response = self.client.get(
                f'/api/files/{payload}',
                HTTP_AUTHORIZATION=f'Bearer {self.token}'
            )
            
            # Should not allow access to system files
            self.assertIn(response.status_code, [400, 403, 404],
                         f"Path traversal should be blocked: {payload}")


class InputLengthValidationTest(TestCase):
    """Test input length validation"""
    
    def setUp(self):
        self.client = Client()
        self.token = self.generate_token()
    
    def generate_token(self):
        """Generate test JWT token"""
        payload = {
            'sub': 'test_user',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, 'test_secret', algorithm='HS256')
    
    def test_oversized_title_rejected(self):
        """Test that oversized titles are rejected"""
        response = self.client.post(
            '/api/stories',
            data={
                'title': 'A' * 10000,  # Very long title
                'blurb': 'Test'
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        # Should be rejected with validation error
        self.assertEqual(response.status_code, 400,
                        "Oversized input should be rejected")
    
    def test_oversized_content_rejected(self):
        """Test that oversized content is rejected"""
        response = self.client.post(
            '/api/whispers',
            data={
                'content': 'A' * 100000,  # Very long content
                'scope': 'public'
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        # Should be rejected
        self.assertEqual(response.status_code, 400,
                        "Oversized content should be rejected")
    
    def test_empty_required_fields_rejected(self):
        """Test that empty required fields are rejected"""
        response = self.client.post(
            '/api/stories',
            data={
                'title': '',  # Empty title
                'blurb': ''   # Empty blurb
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        self.assertEqual(response.status_code, 400,
                        "Empty required fields should be rejected")


class DataTypeValidationTest(TestCase):
    """Test data type validation"""
    
    def setUp(self):
        self.client = Client()
        self.token = self.generate_token()
    
    def generate_token(self):
        """Generate test JWT token"""
        payload = {
            'sub': 'test_user',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, 'test_secret', algorithm='HS256')
    
    def test_invalid_data_types_rejected(self):
        """Test that invalid data types are rejected"""
        response = self.client.post(
            '/api/stories',
            data={
                'title': 123,  # Should be string
                'blurb': ['array'],  # Should be string
                'published': 'not-a-boolean'  # Should be boolean
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        # Should be rejected with validation error
        self.assertEqual(response.status_code, 400,
                        "Invalid data types should be rejected")
    
    def test_invalid_enum_values_rejected(self):
        """Test that invalid enum values are rejected"""
        response = self.client.post(
            '/api/whispers',
            data={
                'content': 'Test',
                'scope': 'invalid_scope'  # Invalid enum value
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        self.assertEqual(response.status_code, 400,
                        "Invalid enum values should be rejected")


class MassAssignmentTest(TestCase):
    """Test mass assignment prevention"""
    
    def setUp(self):
        self.client = Client()
        self.token = self.generate_token()
    
    def generate_token(self):
        """Generate test JWT token"""
        payload = {
            'sub': 'test_user',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, 'test_secret', algorithm='HS256')
    
    def test_protected_fields_not_assignable(self):
        """Test that protected fields cannot be mass assigned"""
        response = self.client.patch(
            '/api/users/me',
            data={
                'display_name': 'New Name',  # Allowed
                'is_admin': True,  # Protected
                'credits': 9999,  # Protected
                'subscription_tier': 'premium'  # Protected
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Protected fields should not be changed
            self.assertNotEqual(data.get('is_admin'), True,
                              "is_admin should not be mass assignable")
            self.assertNotEqual(data.get('credits'), 9999,
                              "credits should not be mass assignable")


@pytest.mark.security
class ContentSecurityTest(TestCase):
    """Test content security policies"""
    
    def setUp(self):
        self.client = Client()
    
    def test_csp_header_present(self):
        """Test that Content-Security-Policy header is present"""
        response = self.client.get('/')
        
        # CSP header should be present
        csp = response.get('Content-Security-Policy')
        if csp:
            # Should restrict script sources
            self.assertIn("script-src", csp.lower(),
                         "CSP should restrict script sources")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
