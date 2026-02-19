"""
Property-based tests for Offline Support Service.

Tests universal properties that should hold across all valid inputs.

Feature: mobile-backend-integration
"""

import pytest
from hypothesis import given, strategies as st, assume
from datetime import datetime, timezone, timedelta
from django.test import RequestFactory
from django.http import HttpResponse
from apps.core.offline_support_service import OfflineSupportService
import hashlib


# Hypothesis strategies
@st.composite
def datetime_strategy(draw):
    """Generate valid datetime objects."""
    year = draw(st.integers(min_value=2020, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Safe for all months
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


@st.composite
def content_strategy(draw):
    """Generate content strings."""
    return draw(st.text(min_size=1, max_size=1000))


@st.composite
def etag_strategy(draw):
    """Generate valid ETag strings."""
    content = draw(st.text(min_size=1, max_size=100))
    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
    return f'"{content_hash}"'


class TestOfflineSupportProperties:
    """Property-based tests for OfflineSupportService."""
    
    @given(content=content_strategy())
    def test_property_etag_consistency(self, content):
        """
        Feature: mobile-backend-integration, Property: ETag Consistency
        
        For any content, generating an ETag multiple times should produce
        the same result (idempotent).
        
        **Validates: Requirements 9.1**
        """
        etag1 = OfflineSupportService.generate_etag(content)
        etag2 = OfflineSupportService.generate_etag(content)
        
        assert etag1 == etag2
        assert etag1.startswith('"')
        assert etag1.endswith('"')
    
    @given(
        last_modified=datetime_strategy(),
        etag=etag_strategy()
    )
    def test_property_cache_headers_present(self, last_modified, etag):
        """
        Feature: mobile-backend-integration, Property: Cache Headers Present
        
        For any response with cache headers added, the response SHALL include
        Last-Modified, ETag, and Cache-Control headers.
        
        **Validates: Requirements 9.1, 9.4**
        """
        response = HttpResponse()
        
        OfflineSupportService.add_cache_headers(response, last_modified, etag)
        
        assert 'Last-Modified' in response
        assert 'ETag' in response
        assert 'Cache-Control' in response
        assert response['ETag'] == etag
    
    @given(
        last_modified=datetime_strategy(),
        etag=etag_strategy()
    )
    def test_property_20_conditional_request_304_matching_etag(
        self, last_modified, etag
    ):
        """
        Feature: mobile-backend-integration, Property 20: Conditional Request 304 Response
        
        For any request with If-None-Match header matching the current ETag,
        the backend SHALL indicate content is fresh (return True for 304).
        
        **Validates: Requirements 9.2, 9.3**
        """
        request_factory = RequestFactory()
        request = request_factory.get('/', HTTP_IF_NONE_MATCH=etag)
        
        is_fresh = OfflineSupportService.check_conditional_request(
            request, last_modified, etag
        )
        
        assert is_fresh is True
    
    @given(
        last_modified=datetime_strategy(),
        etag=etag_strategy(),
        different_etag=etag_strategy()
    )
    def test_property_20_conditional_request_stale_different_etag(
        self, last_modified, etag, different_etag
    ):
        """
        Feature: mobile-backend-integration, Property 20: Conditional Request 304 Response
        
        For any request with If-None-Match header NOT matching the current ETag,
        the backend SHALL indicate content is stale (return False).
        
        **Validates: Requirements 9.2, 9.3**
        """
        assume(etag != different_etag)
        
        request_factory = RequestFactory()
        request = request_factory.get('/', HTTP_IF_NONE_MATCH=different_etag)
        
        is_fresh = OfflineSupportService.check_conditional_request(
            request, last_modified, etag
        )
        
        assert is_fresh is False
    
    @given(
        last_modified=datetime_strategy(),
        etag=etag_strategy(),
        time_offset_hours=st.integers(min_value=1, max_value=1000)
    )
    def test_property_20_conditional_request_304_if_modified_since_fresh(
        self, last_modified, etag, time_offset_hours
    ):
        """
        Feature: mobile-backend-integration, Property 20: Conditional Request 304 Response
        
        For any request with If-Modified-Since header indicating a time AFTER
        the last modification, the backend SHALL indicate content is fresh.
        
        **Validates: Requirements 9.2, 9.3**
        """
        # Client timestamp is after last_modified
        client_time = last_modified + timedelta(hours=time_offset_hours)
        
        # Format as HTTP date
        from django.utils.http import http_date
        if_modified_since = http_date(client_time.timestamp())
        
        request_factory = RequestFactory()
        request = request_factory.get(
            '/', HTTP_IF_MODIFIED_SINCE=if_modified_since
        )
        
        is_fresh = OfflineSupportService.check_conditional_request(
            request, last_modified, etag
        )
        
        assert is_fresh is True
    
    @given(
        last_modified=datetime_strategy(),
        etag=etag_strategy(),
        time_offset_hours=st.integers(min_value=1, max_value=1000)
    )
    def test_property_20_conditional_request_stale_if_modified_since(
        self, last_modified, etag, time_offset_hours
    ):
        """
        Feature: mobile-backend-integration, Property 20: Conditional Request 304 Response
        
        For any request with If-Modified-Since header indicating a time BEFORE
        the last modification, the backend SHALL indicate content is stale.
        
        **Validates: Requirements 9.2, 9.3**
        """
        # Client timestamp is before last_modified
        client_time = last_modified - timedelta(hours=time_offset_hours)
        
        # Format as HTTP date
        from django.utils.http import http_date
        if_modified_since = http_date(client_time.timestamp())
        
        request_factory = RequestFactory()
        request = request_factory.get(
            '/', HTTP_IF_MODIFIED_SINCE=if_modified_since
        )
        
        is_fresh = OfflineSupportService.check_conditional_request(
            request, last_modified, etag
        )
        
        assert is_fresh is False
    
    @given(
        last_modified=datetime_strategy(),
        etag=etag_strategy()
    )
    def test_property_20_conditional_request_no_headers_stale(
        self, last_modified, etag
    ):
        """
        Feature: mobile-backend-integration, Property 20: Conditional Request 304 Response
        
        For any request without conditional headers (If-None-Match or
        If-Modified-Since), the backend SHALL indicate content is stale.
        
        **Validates: Requirements 9.2, 9.3**
        """
        request_factory = RequestFactory()
        request = request_factory.get('/')
        
        is_fresh = OfflineSupportService.check_conditional_request(
            request, last_modified, etag
        )
        
        assert is_fresh is False
    
    def test_property_20_not_modified_response_format(self):
        """
        Feature: mobile-backend-integration, Property 20: Conditional Request 304 Response
        
        For any 304 Not Modified response, the response SHALL have status 304
        and no response body.
        
        **Validates: Requirements 9.3**
        """
        response = OfflineSupportService.create_not_modified_response()
        
        assert response.status_code == 304
        assert not response.content or len(response.content) == 0
    
    @given(
        last_modified=datetime_strategy(),
        etag=etag_strategy()
    )
    def test_property_wildcard_etag_always_fresh(
        self, last_modified, etag
    ):
        """
        Feature: mobile-backend-integration, Property: Wildcard ETag Matching
        
        For any request with If-None-Match: *, the backend SHALL always
        indicate content is fresh regardless of actual ETag.
        
        **Validates: Requirements 9.2**
        """
        request_factory = RequestFactory()
        request = request_factory.get('/', HTTP_IF_NONE_MATCH='*')
        
        is_fresh = OfflineSupportService.check_conditional_request(
            request, last_modified, etag
        )
        
        assert is_fresh is True
    
    @given(
        last_modified=datetime_strategy(),
        etag=etag_strategy(),
        num_etags=st.integers(min_value=2, max_value=5)
    )
    def test_property_multiple_etags_matching(
        self, last_modified, etag, num_etags
    ):
        """
        Feature: mobile-backend-integration, Property: Multiple ETag Matching
        
        For any request with multiple ETags in If-None-Match header, if any
        ETag matches the current ETag, the backend SHALL indicate fresh.
        
        **Validates: Requirements 9.2**
        """
        # Generate multiple ETags including the correct one
        etags = [etag]
        for i in range(num_etags - 1):
            fake_etag = f'"fake{i}"'
            etags.append(fake_etag)
        
        # Shuffle to ensure position doesn't matter
        import random
        random.shuffle(etags)
        
        if_none_match = ', '.join(etags)
        request_factory = RequestFactory()
        request = request_factory.get('/', HTTP_IF_NONE_MATCH=if_none_match)
        
        is_fresh = OfflineSupportService.check_conditional_request(
            request, last_modified, etag
        )
        
        assert is_fresh is True
