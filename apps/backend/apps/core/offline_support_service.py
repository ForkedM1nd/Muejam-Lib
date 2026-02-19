"""
Offline Support Service for Mobile Backend Integration.

This service provides metadata and endpoints for mobile offline support
and data synchronization, including cache header generation and conditional
request handling.

Validates Requirements: 9.1, 9.2, 9.3, 9.4
"""

from datetime import datetime
from typing import Optional
from django.http import HttpRequest, HttpResponse
from django.utils.http import http_date, parse_http_date_safe
import hashlib


class OfflineSupportService:
    """
    Service for supporting mobile offline capabilities.
    
    Provides conditional request handling and cache header management
    for efficient mobile data synchronization.
    """
    
    @staticmethod
    def generate_etag(content: str) -> str:
        """
        Generate an ETag for content.
        
        Args:
            content: Content string to generate ETag for
            
        Returns:
            ETag string (MD5 hash of content)
        """
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        return f'"{content_hash}"'
    
    @staticmethod
    def add_cache_headers(
        response: HttpResponse,
        last_modified: datetime,
        etag: str
    ) -> None:
        """
        Add cache control headers to response.
        
        Adds Last-Modified, ETag, and Cache-Control headers to enable
        mobile client caching and conditional requests.
        
        Args:
            response: Django response object to add headers to
            last_modified: Last modification timestamp
            etag: Entity tag for content
            
        Validates: Requirement 9.1, 9.4
        """
        # Add Last-Modified header
        response['Last-Modified'] = http_date(last_modified.timestamp())
        
        # Add ETag header
        response['ETag'] = etag
        
        # Add Cache-Control header with appropriate directives for mobile caching
        response['Cache-Control'] = 'private, must-revalidate, max-age=300'
    
    @staticmethod
    def check_conditional_request(
        request: HttpRequest,
        last_modified: datetime,
        etag: str
    ) -> bool:
        """
        Check if conditional request headers indicate cached content is fresh.
        
        Checks If-Modified-Since and If-None-Match headers to determine
        if the client's cached content is still valid.
        
        Args:
            request: Django request object
            last_modified: Content last modification time
            etag: Content entity tag
            
        Returns:
            True if content is fresh (should return 304), False if stale
            
        Validates: Requirement 9.2, 9.3
        """
        # Check If-None-Match header (ETag comparison)
        if_none_match = request.headers.get('If-None-Match')
        if if_none_match:
            # Handle multiple ETags (comma-separated)
            client_etags = [tag.strip() for tag in if_none_match.split(',')]
            if etag in client_etags or '*' in client_etags:
                return True
        
        # Check If-Modified-Since header (timestamp comparison)
        if_modified_since = request.headers.get('If-Modified-Since')
        if if_modified_since:
            client_timestamp = parse_http_date_safe(if_modified_since)
            if client_timestamp is not None:
                # Convert last_modified to timestamp for comparison
                last_modified_timestamp = int(last_modified.timestamp())
                # Content is fresh if not modified since client's timestamp
                if last_modified_timestamp <= client_timestamp:
                    return True
        
        return False
    
    @staticmethod
    def create_not_modified_response() -> HttpResponse:
        """
        Create HTTP 304 Not Modified response.
        
        Returns:
            HttpResponse with 304 status and no body
            
        Validates: Requirement 9.3
        """
        response = HttpResponse(status=304)
        return response
    
    @staticmethod
    async def get_changes_since(
        resource_type: str,
        user_id: str,
        since_timestamp: datetime
    ) -> list:
        """
        Get resources modified since timestamp for sync.
        
        This method provides incremental sync support by returning only
        resources that have been modified since the provided timestamp.
        
        Args:
            resource_type: Type of resource ('stories', 'whispers', etc.)
            user_id: User ID for filtering
            since_timestamp: Timestamp to get changes since
            
        Returns:
            List of modified resources
            
        Note:
            This is a placeholder for future implementation. Actual
            implementation will depend on specific resource models.
        """
        # Placeholder for future implementation
        # This will be implemented when sync endpoints are created
        raise NotImplementedError(
            "get_changes_since will be implemented in sync endpoint tasks"
        )
