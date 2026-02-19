"""
Mobile Configuration API Views

Endpoints for mobile clients to retrieve app configuration and for admins
to manage mobile configuration settings.

Requirements:
- 16.1: Provide endpoints for mobile clients to retrieve feature flags
- 16.2: Provide endpoints for mobile clients to retrieve app configuration settings
- 16.5: Allow different configurations per platform (iOS vs Android)
"""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from .mobile_config_service import MobileConfigService
from apps.admin.permissions import IsAdministrator

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_mobile_config(request):
    """
    Get mobile configuration for a specific platform and version.
    
    GET /v1/config/mobile?platform=<ios|android>&version=<version>
    
    Query parameters:
        - platform: 'ios' or 'android' (required)
        - version: App version string (e.g., '1.2.3') (required)
        
    Returns:
        200: Mobile configuration with feature flags and settings
        400: Invalid or missing parameters
        403: App version not supported
        
    Requirements: 16.1, 16.2, 16.5
    """
    # Get and validate query parameters
    platform = request.GET.get('platform')
    app_version = request.GET.get('version')
    
    if not platform:
        return Response(
            {
                'error': {
                    'code': 'MISSING_PARAMETER',
                    'message': 'Required parameter "platform" is missing',
                    'details': {
                        'parameter': 'platform',
                        'allowed_values': ['ios', 'android']
                    }
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not app_version:
        return Response(
            {
                'error': {
                    'code': 'MISSING_PARAMETER',
                    'message': 'Required parameter "version" is missing',
                    'details': {
                        'parameter': 'version',
                        'format': 'Semantic version (e.g., 1.2.3)'
                    }
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate platform
    if platform not in ['ios', 'android']:
        return Response(
            {
                'error': {
                    'code': 'INVALID_PLATFORM',
                    'message': f'Invalid platform: {platform}',
                    'details': {
                        'parameter': 'platform',
                        'provided': platform,
                        'allowed_values': ['ios', 'android']
                    }
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        service = MobileConfigService()
        
        # Run async service method in event loop
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            config = loop.run_until_complete(
                service.get_config(platform, app_version)
            )
        finally:
            loop.close()
        
        # Add cache headers for client-side caching (Requirement 16.4)
        response = Response(config, status=status.HTTP_200_OK)
        response['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
        response['ETag'] = f'"{config["id"]}-{config["updated_at"]}"' if config.get('id') else None
        
        return response
    
    except ValueError as e:
        # Handle version not supported or invalid platform
        error_message = str(e)
        if 'not supported' in error_message:
            return Response(
                {
                    'error': {
                        'code': 'VERSION_NOT_SUPPORTED',
                        'message': error_message,
                        'details': {
                            'platform': platform,
                            'version': app_version
                        }
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )
        else:
            return Response(
                {
                    'error': {
                        'code': 'INVALID_REQUEST',
                        'message': error_message,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        logger.error(
            f"Error fetching mobile config: {str(e)}",
            extra={
                'platform': platform,
                'app_version': app_version
            }
        )
        return Response(
            {
                'error': {
                    'code': 'CONFIG_ERROR',
                    'message': 'Failed to retrieve mobile configuration',
                    'details': str(e)
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsAdministrator])
def update_mobile_config(request):
    """
    Update mobile configuration for a specific platform (admin only).
    
    PUT /v1/config/mobile?platform=<ios|android>
    
    Query parameters:
        - platform: 'ios' or 'android' (required)
        
    Request body:
        {
            "min_version": "1.0.0",  // optional
            "config": {
                "features": {
                    "push_notifications": true,
                    "offline_mode": true,
                    ...
                },
                "settings": {
                    "max_upload_size_mb": 50,
                    ...
                },
                ...
            }
        }
        
    Returns:
        200: Updated mobile configuration
        400: Invalid request data or missing parameters
        403: User is not an administrator
        
    Requirements: 16.2, 16.5
    """
    # Get and validate query parameter
    platform = request.GET.get('platform')
    
    if not platform:
        return Response(
            {
                'error': {
                    'code': 'MISSING_PARAMETER',
                    'message': 'Required parameter "platform" is missing',
                    'details': {
                        'parameter': 'platform',
                        'allowed_values': ['ios', 'android']
                    }
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate platform
    if platform not in ['ios', 'android']:
        return Response(
            {
                'error': {
                    'code': 'INVALID_PLATFORM',
                    'message': f'Invalid platform: {platform}',
                    'details': {
                        'parameter': 'platform',
                        'provided': platform,
                        'allowed_values': ['ios', 'android']
                    }
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Extract request data
    config_data = request.data.get('config')
    min_version = request.data.get('min_version')
    
    if not config_data:
        return Response(
            {
                'error': {
                    'code': 'MISSING_FIELD',
                    'message': 'Required field "config" is missing',
                    'details': {
                        'field': 'config',
                        'description': 'Configuration object with features and settings'
                    }
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate config is a dictionary
    if not isinstance(config_data, dict):
        return Response(
            {
                'error': {
                    'code': 'INVALID_FIELD_TYPE',
                    'message': 'Field "config" must be an object',
                    'details': {
                        'field': 'config',
                        'expected_type': 'object',
                        'provided_type': type(config_data).__name__
                    }
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        service = MobileConfigService()
        
        # Run async service method in event loop
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            config = loop.run_until_complete(
                service.update_config(
                    platform=platform,
                    config_data=config_data,
                    min_version=min_version
                )
            )
        finally:
            loop.close()
        
        logger.info(
            f"Mobile configuration updated by admin",
            extra={
                'platform': platform,
                'admin_user_id': request.clerk_user_id,
                'min_version': min_version
            }
        )
        
        return Response(config, status=status.HTTP_200_OK)
    
    except ValueError as e:
        return Response(
            {
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': str(e),
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        logger.error(
            f"Error updating mobile config: {str(e)}",
            extra={
                'platform': platform,
                'admin_user_id': request.clerk_user_id
            }
        )
        return Response(
            {
                'error': {
                    'code': 'UPDATE_ERROR',
                    'message': 'Failed to update mobile configuration',
                    'details': str(e)
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
