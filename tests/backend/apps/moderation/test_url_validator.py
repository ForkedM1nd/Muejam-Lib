"""
Tests for URL validation service.

This module tests the URLValidator service for extracting and validating URLs
in content according to requirements 4.6 and 4.7.
"""

import pytest
from unittest.mock import Mock, patch
from apps.moderation.url_validator import URLValidator, URLValidationResult


class TestURLValidator:
    """Test suite for URLValidator service."""
    
    def test_extract_urls_from_content(self):
        """Test URL extraction from content."""
        validator = URLValidator()
        
        content = """
        Check out this article: https://example.com/article
        And this one: http://test.com/page
        """
        
        urls = validator.extract_urls(content)
        
        assert len(urls) == 2
        assert 'https://example.com/article' in urls
        assert 'http://test.com/page' in urls
    
    def test_extract_urls_removes_duplicates(self):
        """Test that duplicate URLs are removed."""
        validator = URLValidator()
        
        content = """
        https://example.com/page
        https://example.com/page
        https://example.com/page
        """
        
        urls = validator.extract_urls(content)
        
        assert len(urls) == 1
        assert 'https://example.com/page' in urls
    
    def test_extract_urls_empty_content(self):
        """Test URL extraction from empty content."""
        validator = URLValidator()
        
        urls = validator.extract_urls("")
        
        assert urls == []
    
    def test_whitelisted_domains_are_trusted(self):
        """Test that whitelisted domains are trusted."""
        validator = URLValidator()
        
        # Test default whitelist
        assert validator.is_whitelisted('https://github.com/user/repo')
        assert validator.is_whitelisted('https://www.wikipedia.org/wiki/Test')
        assert validator.is_whitelisted('https://stackoverflow.com/questions/123')
    
    def test_custom_whitelist(self):
        """Test custom whitelist configuration."""
        custom_whitelist = {'example.com', 'test.org'}
        validator = URLValidator(whitelist=custom_whitelist)
        
        assert validator.is_whitelisted('https://example.com/page')
        assert validator.is_whitelisted('https://test.org/article')
        assert not validator.is_whitelisted('https://unknown.com/page')
    
    def test_validate_safe_urls(self):
        """Test validation of safe URLs."""
        validator = URLValidator()
        
        urls = [
            'https://github.com/user/repo',
            'https://wikipedia.org/wiki/Test'
        ]
        
        result = validator.validate_urls(urls)
        
        assert result.is_safe is True
        assert len(result.malicious_urls) == 0
        assert result.total_urls == 2
    
    def test_validate_empty_url_list(self):
        """Test validation of empty URL list."""
        validator = URLValidator()
        
        result = validator.validate_urls([])
        
        assert result.is_safe is True
        assert len(result.malicious_urls) == 0
        assert result.total_urls == 0
    
    def test_heuristic_check_detects_ip_addresses(self):
        """Test that heuristic check flags IP addresses."""
        validator = URLValidator(api_key=None)  # Force heuristic mode
        
        urls = ['http://192.168.1.1/malware']
        
        result = validator.validate_urls(urls)
        
        assert result.is_safe is False
        assert len(result.malicious_urls) == 1
        assert 'http://192.168.1.1/malware' in result.malicious_urls
    
    def test_heuristic_check_detects_url_shorteners(self):
        """Test that heuristic check flags URL shorteners."""
        validator = URLValidator(api_key=None)  # Force heuristic mode
        
        urls = ['http://bit.ly/abc123']
        
        result = validator.validate_urls(urls)
        
        assert result.is_safe is False
        assert len(result.malicious_urls) == 1
    
    def test_heuristic_check_detects_suspicious_tlds(self):
        """Test that heuristic check flags suspicious TLDs."""
        validator = URLValidator(api_key=None)  # Force heuristic mode
        
        urls = ['http://login-verify.tk/account']
        
        result = validator.validate_urls(urls)
        
        assert result.is_safe is False
        assert len(result.malicious_urls) == 1
    
    def test_check_content_integration(self):
        """Test the main check_content method."""
        validator = URLValidator()
        
        content = """
        Check out my GitHub: https://github.com/user/repo
        And this article: https://wikipedia.org/wiki/Test
        """
        
        result = validator.check_content(content)
        
        assert result.is_safe is True
        assert result.total_urls == 2
    
    def test_check_content_with_malicious_url(self):
        """Test check_content with malicious URL."""
        validator = URLValidator(api_key=None)  # Force heuristic mode
        
        content = """
        Click here: http://192.168.1.1/malware
        """
        
        result = validator.check_content(content)
        
        assert result.is_safe is False
        assert len(result.malicious_urls) == 1
    
    def test_cache_functionality(self):
        """Test that URL validation results are cached."""
        validator = URLValidator(api_key=None, use_cache=True)
        
        urls = ['http://bit.ly/test123']
        
        # First check - should detect as malicious
        result1 = validator.validate_urls(urls)
        assert result1.is_safe is False
        
        # Manually add to cache to test cache retrieval
        validator._cache['http://bit.ly/test123'] = False
        
        # Second check - should use cache
        result2 = validator.validate_urls(urls)
        assert result2.is_safe is False
        assert 'http://bit.ly/test123' in result2.details
        assert result2.details['http://bit.ly/test123'] == 'cached_threat'
    
    @patch('apps.moderation.url_validator.requests.post')
    def test_safe_browsing_api_integration(self, mock_post):
        """Test Google Safe Browsing API integration."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'matches': [
                {
                    'threat': {'url': 'http://malicious.com/page'},
                    'threatType': 'MALWARE'
                }
            ]
        }
        mock_post.return_value = mock_response
        
        validator = URLValidator(api_key='test-api-key')
        
        urls = ['http://malicious.com/page', 'https://github.com/user/repo']
        result = validator.validate_urls(urls)
        
        # GitHub should be whitelisted, malicious.com should be flagged
        assert result.is_safe is False
        assert 'http://malicious.com/page' in result.malicious_urls
        assert result.details['http://malicious.com/page'] == 'MALWARE'
    
    @patch('apps.moderation.url_validator.requests.post')
    def test_safe_browsing_api_timeout_fallback(self, mock_post):
        """Test fallback to heuristic check on API timeout."""
        # Mock API timeout
        mock_post.side_effect = Exception("Timeout")
        
        validator = URLValidator(api_key='test-api-key')
        
        urls = ['http://bit.ly/test']
        result = validator.validate_urls(urls)
        
        # Should fallback to heuristic check
        assert result.is_safe is False
        assert 'http://bit.ly/test' in result.malicious_urls
    
    def test_log_blocked_attempt(self):
        """Test logging of blocked attempts."""
        validator = URLValidator()
        
        # Should not raise exception
        validator.log_blocked_attempt(
            content_type='story',
            content_id='test-123',
            malicious_urls=['http://malicious.com'],
            user_id='user-456'
        )
    
    def test_mixed_safe_and_malicious_urls(self):
        """Test content with both safe and malicious URLs."""
        validator = URLValidator(api_key=None)  # Force heuristic mode
        
        urls = [
            'https://github.com/user/repo',  # Safe (whitelisted)
            'http://192.168.1.1/malware',    # Malicious (IP address)
            'https://wikipedia.org/wiki/Test'  # Safe (whitelisted)
        ]
        
        result = validator.validate_urls(urls)
        
        assert result.is_safe is False
        assert len(result.malicious_urls) == 1
        assert 'http://192.168.1.1/malware' in result.malicious_urls
        assert result.total_urls == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
