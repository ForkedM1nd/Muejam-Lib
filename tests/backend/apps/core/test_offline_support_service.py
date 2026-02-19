"""
Unit tests for Offline Support Service.

Tests cache header generation, conditional request checking,
and 304 Not Modified response handling.
"""

import pytest
from datetime import datetime, timezone
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory
from apps.core.offline_support_service import OfflineSupportService


class TestOfflineSupportService:
    """Unit tests for OfflineSupportService."""
    
    @pytest.fixture
    def request_factory(self):
        """Provide Django request factory."""
        return RequestFactory()
    
    def test_generate_etag_consistent(self):
        """Test that ETag generation is consistent for same content."""
        content = "test content"
        etag1 = OfflineSupportService.generate_etag(content)
        etag2 = OfflineSupportService.generate_etag(content)
        
        assert etag1 == etag2
        assert etag1.startswith('"')
        assert etag1.endswith('"')
    
    def test_generate_etag_different_content(self):
        """Test that different content produces different ETags."""
        content1 = "test content 1"
        content2 = "test content 2"
        
        etag1 = OfflineSupportService.generate_etag(content1)
        etag2 = OfflineSupportService.generate_etag(content2)
        
        assert etag1 != etag2
    
    def test_add_cache_headers(self):
        """Test that cache headers are added correctly."""
        response = HttpResponse()
        last_modified = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        etag = '"abc123"'
        
        OfflineSupportService.add_cache_headers(response, last_modified, etag)
        
        assert 'Last-Modified' in response
        assert 'ETag' in response
        assert response['ETag'] == etag
        assert 'Cache-Control' in response
        assert 'must-revalidate' in response['Cache-Control']
    
    def test_check_conditional_request_if_none_match_fresh(self, request_factory):
        """Test conditional request with matching ETag returns fresh."""
        request = request_factory.get('/', HTTP_IF_NONE_MATCH='"abc123"')
        last_modified = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        etag = '"abc123"'
        
        is_fresh = OfflineSupportService.check_conditional_request(
            request, last_modified, etag
        )
        
        assert is_fresh is True
    
    def test_check_conditional_request_if_none_match_stale(self, request_factory):
        """Test conditional request with non-matching ETag returns stale."""
        request = request_factory.get('/', HTTP_IF_NONE_MATCH='"xyz789"')
        last_modified = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        etag = '"abc123"'
        
        is_fresh = OfflineSupportService.check_conditional_request(
            request, last_modified, etag
        )
        
        assert is_fresh is False
    
    def test_check_conditional_request_if_none_match_multiple_etags(
        self, request_factory
    ):
        """Test conditional request with multiple ETags."""
        request = request_factory.get(
            '/', HTTP_IF_NONE_MATCH='"xyz789", "abc123", "def456"'
        )
        last_modified = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        etag = '"abc123"'
        
        is_fresh = OfflineSupportService.check_conditional_request(
            request, last_modified, etag
        )
        
        assert is_fresh is True
    
    def test_check_conditional_request_if_none_match_wildcard(
        self, request_factory
    ):
        """Test conditional request with wildcard ETag."""
        request = request_factory.get('/', HTTP_IF_NONE_MATCH='*')
        last_modified = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        etag = '"abc123"'
        
        is_fresh = OfflineSupportService.check_conditional_request(
            request, last_modified, etag
        )
        
        assert is_fresh is True
    
    def test_check_conditional_request_if_modified_since_fresh(
        self, request_factory
    ):
        """Test conditional request with If-Modified-Since returns fresh."""
        # Client has content from Jan 2, server content modified Jan 1
        request = request_factory.get(
            '/', HTTP_IF_MODIFIED_SINCE='Mon, 02 Jan 2024 12:00:00 GMT'
        )
        last_modified = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        etag = '"abc123"'
        
        is_fresh = OfflineSupportService.check_conditional_request(
            request, last_modified, etag
        )
        
        assert is_fresh is True
    
    def test_check_conditional_request_if_modified_since_stale(
        self, request_factory
    ):
        """Test conditional request with If-Modified-Since returns stale."""
        # Client has content from Jan 1, server content modified Jan 2
        request = request_factory.get(
            '/', HTTP_IF_MODIFIED_SINCE='Mon, 01 Jan 2024 12:00:00 GMT'
        )
        last_modified = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        etag = '"abc123"'
        
        is_fresh = OfflineSupportService.check_conditional_request(
            request, last_modified, etag
        )
        
        assert is_fresh is False
    
    def test_check_conditional_request_if_modified_since_exact_match(
        self, request_factory
    ):
        """Test conditional request with exact timestamp match returns fresh."""
        request = request_factory.get(
            '/', HTTP_IF_MODIFIED_SINCE='Mon, 01 Jan 2024 12:00:00 GMT'
        )
        last_modified = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        etag = '"abc123"'
        
        is_fresh = OfflineSupportService.check_conditional_request(
            request, last_modified, etag
        )
        
        assert is_fresh is True
    
    def test_check_conditional_request_no_headers(self, request_factory):
        """Test conditional request without conditional headers returns stale."""
        request = request_factory.get('/')
        last_modified = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        etag = '"abc123"'
        
        is_fresh = OfflineSupportService.check_conditional_request(
            request, last_modified, etag
        )
        
        assert is_fresh is False
    
    def test_check_conditional_request_invalid_if_modified_since(
        self, request_factory
    ):
        """Test conditional request with invalid If-Modified-Since is ignored."""
        request = request_factory.get(
            '/', HTTP_IF_MODIFIED_SINCE='invalid-date'
        )
        last_modified = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        etag = '"abc123"'
        
        is_fresh = OfflineSupportService.check_conditional_request(
            request, last_modified, etag
        )
        
        assert is_fresh is False
    
    def test_check_conditional_request_etag_priority(self, request_factory):
        """Test that ETag check takes priority when both headers present."""
        # ETag matches (fresh), but timestamp doesn't (stale)
        request = request_factory.get(
            '/',
            HTTP_IF_NONE_MATCH='"abc123"',
            HTTP_IF_MODIFIED_SINCE='Mon, 01 Jan 2024 12:00:00 GMT'
        )
        last_modified = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        etag = '"abc123"'
        
        is_fresh = OfflineSupportService.check_conditional_request(
            request, last_modified, etag
        )
        
        # Should return fresh because ETag matches
        assert is_fresh is True
    
    def test_create_not_modified_response(self):
        """Test that 304 Not Modified response is created correctly."""
        response = OfflineSupportService.create_not_modified_response()
        
        assert response.status_code == 304
        assert not response.content
    
    def test_get_changes_since_not_implemented(self):
        """Test that get_changes_since raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            # This is async, but we're just testing it raises
            import asyncio
            asyncio.run(
                OfflineSupportService.get_changes_since(
                    'stories',
                    'user123',
                    datetime.now(timezone.utc)
                )
            )
