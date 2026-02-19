"""
Response Optimizer Service for Mobile Backend Integration.

This service optimizes API responses for mobile clients by filtering fields,
calculating response size metadata, and providing helper methods for mobile
response optimization.

Requirements: 3.1, 3.3, 3.5
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from django.http import HttpResponse

logger = logging.getLogger(__name__)


class ResponseOptimizer:
    """
    Service for optimizing API responses for mobile clients.
    
    Provides field filtering, pagination optimization, and response compression
    support for mobile clients with bandwidth constraints.
    """
    
    @staticmethod
    def optimize_response(data: Union[Dict, List], request) -> Union[Dict, List]:
        """
        Optimize response data based on client type and request parameters.
        
        Applies field filtering if requested via query parameters.
        Supports both single objects and lists of objects.
        
        Args:
            data: Response data dictionary or list
            request: Django request object with client_type attribute
            
        Returns:
            Optimized response data
        """
        # Check if field filtering is requested via query parameters
        fields_param = request.GET.get('fields', '').strip()
        
        if not fields_param:
            # No filtering requested, return data as-is
            return data
        
        # Parse comma-separated field list
        fields = [f.strip() for f in fields_param.split(',') if f.strip()]
        
        if not fields:
            # Empty field list, return data as-is
            return data
        
        # Apply field filtering
        if isinstance(data, list):
            # Filter each item in the list
            return [ResponseOptimizer.filter_fields(item, fields) for item in data]
        elif isinstance(data, dict):
            # Filter single object
            return ResponseOptimizer.filter_fields(data, fields)
        else:
            # Unsupported data type, return as-is
            return data
    
    @staticmethod
    def filter_fields(data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """
        Filter response data to include only specified fields.
        
        Supports nested field access using dot notation (e.g., 'user.name').
        Only top-level filtering is implemented for simplicity.
        
        Args:
            data: Response data dictionary
            fields: List of field names to include
            
        Returns:
            Filtered data dictionary containing only specified fields
        """
        if not isinstance(data, dict):
            return data
        
        # Create filtered dictionary with only requested fields
        filtered = {}
        
        for field in fields:
            # Support nested field access with dot notation
            if '.' in field:
                # Nested field access (e.g., 'user.name')
                parts = field.split('.', 1)
                parent_field = parts[0]
                nested_field = parts[1]
                
                if parent_field in data:
                    parent_value = data[parent_field]
                    
                    if isinstance(parent_value, dict):
                        # Extract nested field from parent object
                        if parent_field not in filtered:
                            filtered[parent_field] = {}
                        
                        if nested_field in parent_value:
                            filtered[parent_field][nested_field] = parent_value[nested_field]
                    elif isinstance(parent_value, list):
                        # Extract nested field from each item in list
                        if parent_field not in filtered:
                            filtered[parent_field] = []
                        
                        for item in parent_value:
                            if isinstance(item, dict) and nested_field in item:
                                filtered[parent_field].append({nested_field: item[nested_field]})
            else:
                # Top-level field access
                if field in data:
                    filtered[field] = data[field]
        
        return filtered
    
    @staticmethod
    def add_response_metadata(response: HttpResponse, data: Union[Dict, List, str, bytes]) -> None:
        """
        Add response size and optimization metadata to headers.
        
        Calculates the size of the response data and adds it to headers
        for monitoring and optimization purposes.
        
        Args:
            response: Django response object
            data: Response data (dict, list, string, or bytes)
        """
        # Calculate response size
        data_size = ResponseOptimizer.calculate_response_size(data)
        
        # Add size metadata to response headers
        response['X-Response-Size'] = str(data_size)
        response['X-Response-Size-KB'] = f"{data_size / 1024:.2f}"
        
        # Log response size for monitoring
        logger.debug(
            f"Response size: {data_size} bytes ({data_size / 1024:.2f} KB)",
            extra={
                'response_size_bytes': data_size,
                'response_size_kb': data_size / 1024
            }
        )
    
    @staticmethod
    def calculate_response_size(data: Union[Dict, List, str, bytes]) -> int:
        """
        Calculate the size of response data in bytes.
        
        Converts data to JSON string and calculates byte size.
        
        Args:
            data: Response data (dict, list, string, or bytes)
            
        Returns:
            Size in bytes
        """
        if isinstance(data, bytes):
            return len(data)
        elif isinstance(data, str):
            return len(data.encode('utf-8'))
        else:
            # Convert to JSON and calculate size
            try:
                json_str = json.dumps(data, ensure_ascii=False)
                return len(json_str.encode('utf-8'))
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to calculate response size: {e}")
                return 0
    
    @staticmethod
    def create_lightweight_response(data: Union[Dict, List], lightweight_fields: Optional[List[str]] = None) -> Union[Dict, List]:
        """
        Create a lightweight version of the response for mobile clients.
        
        Removes heavy fields and includes only essential data for list views.
        Useful for list endpoints where full details are not needed.
        
        Args:
            data: Response data dictionary or list
            lightweight_fields: Optional list of fields to include in lightweight mode.
                               If None, uses default lightweight fields.
            
        Returns:
            Lightweight response data
        """
        # Default lightweight fields for common resources
        default_lightweight_fields = ['id', 'title', 'created_at', 'updated_at']
        
        fields_to_include = lightweight_fields or default_lightweight_fields
        
        if isinstance(data, list):
            # Create lightweight version for each item
            return [ResponseOptimizer.filter_fields(item, fields_to_include) for item in data]
        elif isinstance(data, dict):
            # Create lightweight version for single object
            return ResponseOptimizer.filter_fields(data, fields_to_include)
        else:
            return data
    
    @staticmethod
    def is_mobile_client(request) -> bool:
        """
        Check if the request is from a mobile client.
        
        Args:
            request: Django request object with client_type attribute
            
        Returns:
            True if client is mobile (iOS or Android), False otherwise
        """
        client_type = getattr(request, 'client_type', 'web')
        return client_type.startswith('mobile-')
    
    @staticmethod
    def should_optimize(request) -> bool:
        """
        Determine if response optimization should be applied.
        
        Checks if the request is from a mobile client or if optimization
        is explicitly requested via query parameters.
        
        Args:
            request: Django request object
            
        Returns:
            True if optimization should be applied, False otherwise
        """
        # Check if mobile client
        if ResponseOptimizer.is_mobile_client(request):
            return True
        
        # Check if optimization is explicitly requested
        optimize_param = request.GET.get('optimize', '').lower()
        return optimize_param in ['true', '1', 'yes']
