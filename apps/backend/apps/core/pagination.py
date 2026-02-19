"""Cursor-based pagination implementation."""
import base64
import json
from rest_framework.pagination import BasePagination
from rest_framework.response import Response


class CursorPagination(BasePagination):
    """
    Cursor-based pagination for stable, efficient pagination.
    
    Encodes cursor as base64 string containing sort key and offset.
    Maintains stable ordering within pagination session.
    
    Supports mobile-specific page sizes via query parameters.
    """
    page_size = 20
    max_page_size = 100
    mobile_page_size = 10  # Default page size for mobile clients
    mobile_max_page_size = 50  # Max page size for mobile clients
    ordering = '-id'  # Default ordering field
    
    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate queryset using cursor-based pagination.
        
        Supports mobile-specific page sizes and configurable page sizes
        via query parameters.
        
        Args:
            queryset: Django queryset to paginate
            request: DRF request object
            view: DRF view object (optional)
            
        Returns:
            List of results for current page
        """
        # Get query params (handle both DRF and Django requests)
        query_params = getattr(request, 'query_params', request.GET)
        
        # Determine if this is a mobile client
        client_type = getattr(request, 'client_type', 'web')
        is_mobile = client_type.startswith('mobile-')
        
        # Set default page size and max based on client type
        default_page_size = self.mobile_page_size if is_mobile else self.page_size
        max_page_size = self.mobile_max_page_size if is_mobile else self.max_page_size
        
        # Get page size from request, enforce max
        requested_page_size = int(query_params.get('page_size', default_page_size))
        self.current_page_size = min(requested_page_size, max_page_size)
        
        # Store request for use in get_paginated_response
        self.request = request
        
        # Apply ordering
        if hasattr(view, 'ordering'):
            self.ordering = view.ordering
        queryset = queryset.order_by(self.ordering)
        
        # Store total count for metadata (before cursor filtering)
        # Note: This can be expensive for large datasets, consider caching
        self.total_count = queryset.count()
        
        # Apply cursor filter if provided
        cursor = query_params.get('cursor')
        if cursor:
            try:
                decoded = json.loads(base64.b64decode(cursor).decode('utf-8'))
                cursor_id = decoded.get('id')
                
                # Apply filter based on ordering direction
                if self.ordering.startswith('-'):
                    # Descending order
                    queryset = queryset.filter(id__lt=cursor_id)
                else:
                    # Ascending order
                    queryset = queryset.filter(id__gt=cursor_id)
            except (ValueError, KeyError, json.JSONDecodeError):
                # Invalid cursor, ignore and start from beginning
                pass
        
        # Fetch one extra item to check if there are more results
        results = list(queryset[:self.current_page_size + 1])
        has_next = len(results) > self.current_page_size
        
        if has_next:
            results = results[:-1]
            last_item = results[-1]
            # Generate next cursor
            next_cursor_data = {'id': last_item.id}
            self.next_cursor = base64.b64encode(
                json.dumps(next_cursor_data).encode('utf-8')
            ).decode('utf-8')
        else:
            self.next_cursor = None
        
        # Store results count for metadata
        self.results_count = len(results)
        
        return results
    
    def get_paginated_response(self, data):
        """
        Return paginated response with data and pagination metadata.
        
        Includes mobile-specific pagination metadata such as page size,
        total count, and has_next indicator.
        
        Args:
            data: Serialized data for current page
            
        Returns:
            Response object with data, next_cursor, and pagination metadata
        """
        # Determine if this is a mobile client
        client_type = getattr(self.request, 'client_type', 'web')
        is_mobile = client_type.startswith('mobile-')
        
        # Build response with pagination metadata
        response_data = {
            'data': data,
            'next_cursor': self.next_cursor,
        }
        
        # Add pagination metadata for mobile clients
        if is_mobile:
            response_data['pagination'] = {
                'page_size': self.current_page_size,
                'results_count': self.results_count,
                'total_count': self.total_count,
                'has_next': self.next_cursor is not None,
            }
        
        return Response(response_data)
