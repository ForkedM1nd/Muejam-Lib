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
    """
    page_size = 20
    max_page_size = 100
    ordering = '-id'  # Default ordering field
    
    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate queryset using cursor-based pagination.
        
        Args:
            queryset: Django queryset to paginate
            request: DRF request object
            view: DRF view object (optional)
            
        Returns:
            List of results for current page
        """
        # Get query params (handle both DRF and Django requests)
        query_params = getattr(request, 'query_params', request.GET)
        
        # Get page size from request, enforce max
        self.page_size = min(
            int(query_params.get('page_size', self.page_size)),
            self.max_page_size
        )
        
        # Apply ordering
        if hasattr(view, 'ordering'):
            self.ordering = view.ordering
        queryset = queryset.order_by(self.ordering)
        
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
        results = list(queryset[:self.page_size + 1])
        has_next = len(results) > self.page_size
        
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
        
        return results
    
    def get_paginated_response(self, data):
        """
        Return paginated response with data and next_cursor.
        
        Args:
            data: Serialized data for current page
            
        Returns:
            Response object with data and next_cursor fields
        """
        return Response({
            'data': data,
            'next_cursor': self.next_cursor
        })
