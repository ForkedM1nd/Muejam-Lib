"""
Test Mode Views for Mobile Backend Integration

Provides test endpoints for QA and development testing.

Requirements: 18.1, 18.2, 18.3, 18.4
"""

import logging
from typing import Dict

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from apps.core.deep_link_service import DeepLinkService
from apps.notifications.push_service import PushNotificationService
from .test_mode_service import TestModeService

logger = logging.getLogger(__name__)


def _is_test_mode_enabled(request) -> bool:
    """
    Check if test mode is enabled for the request.
    
    Args:
        request: Django request object
        
    Returns:
        True if test mode is enabled
    """
    return TestModeService.is_test_mode(request)


def _test_mode_required(view_func):
    """
    Decorator to ensure test mode is enabled.
    
    Returns 403 if test mode is not enabled.
    """
    def wrapper(request, *args, **kwargs):
        if not _is_test_mode_enabled(request):
            return JsonResponse(
                {
                    'error': {
                        'code': 'TEST_MODE_REQUIRED',
                        'message': 'Test mode must be enabled to access this endpoint',
                        'details': {
                            'hint': 'Add X-Test-Mode: true header to your request'
                        }
                    }
                },
                status=403
            )
        
        # Mark request as test mode for logging
        request.is_test_mode = True
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


@csrf_exempt
@require_http_methods(["POST"])
@_test_mode_required
def test_push_notification(request):
    """
    Test endpoint for verifying push notification delivery.
    
    POST /v1/test/push-notification
    
    Request body:
    {
        "user_id": "user123",
        "title": "Test Notification",
        "body": "This is a test notification",
        "data": {"key": "value"}  // optional
    }
    
    Response:
    {
        "success": true,
        "message": "Test notification queued for delivery",
        "delivery_status": {
            "user_id": "user123",
            "total_devices": 2,
            "sent": 2,
            "failed": 0,
            "results": [...]
        }
    }
    
    Requirements: 18.1
    """
    try:
        import json
        
        # Parse request body
        try:
            body = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse(
                {
                    'error': {
                        'code': 'INVALID_JSON',
                        'message': 'Request body must be valid JSON'
                    }
                },
                status=400
            )
        
        # Validate required fields
        user_id = body.get('user_id')
        title = body.get('title')
        notification_body = body.get('body')
        
        if not all([user_id, title, notification_body]):
            return JsonResponse(
                {
                    'error': {
                        'code': 'MISSING_FIELDS',
                        'message': 'Missing required fields',
                        'details': {
                            'required_fields': ['user_id', 'title', 'body']
                        }
                    }
                },
                status=400
            )
        
        # Optional data payload
        data = body.get('data', {})
        
        # Send test notification
        import asyncio
        push_service = PushNotificationService()
        
        try:
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            delivery_status = loop.run_until_complete(
                push_service.send_notification(
                    user_id=user_id,
                    title=title,
                    body=notification_body,
                    data=data
                )
            )
            loop.run_until_complete(push_service.close())
            loop.close()
            
            logger.info(
                f"Test push notification sent to user {user_id}",
                extra={'test_mode': True, 'user_id': user_id}
            )
            
            return JsonResponse(
                {
                    'success': True,
                    'message': 'Test notification queued for delivery',
                    'delivery_status': delivery_status
                },
                status=200
            )
        
        except Exception as e:
            logger.error(
                f"Error sending test push notification: {str(e)}",
                extra={'test_mode': True, 'user_id': user_id}
            )
            return JsonResponse(
                {
                    'error': {
                        'code': 'NOTIFICATION_ERROR',
                        'message': 'Failed to send test notification',
                        'details': {
                            'error': str(e)
                        }
                    }
                },
                status=500
            )
    
    except Exception as e:
        logger.error(f"Unexpected error in test_push_notification: {str(e)}")
        return JsonResponse(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An unexpected error occurred',
                    'details': {
                        'error': str(e)
                    }
                }
            },
            status=500
        )


@require_http_methods(["GET"])
@_test_mode_required
def test_deep_link(request):
    """
    Test endpoint for verifying deep link generation.
    
    GET /v1/test/deep-link?type=story&id=story123&platform=ios
    
    Query parameters:
    - type: Resource type (story, chapter, whisper, profile)
    - id: Resource ID
    - platform: Target platform (ios, android) - optional
    
    Response:
    {
        "success": true,
        "deep_link": "muejam://story/story123",
        "resource_type": "story",
        "resource_id": "story123",
        "platform": "ios"
    }
    
    Requirements: 18.3
    """
    try:
        # Get query parameters
        resource_type = request.GET.get('type')
        resource_id = request.GET.get('id')
        platform = request.GET.get('platform')
        
        # Validate required parameters
        if not resource_type or not resource_id:
            return JsonResponse(
                {
                    'error': {
                        'code': 'MISSING_PARAMETERS',
                        'message': 'Missing required query parameters',
                        'details': {
                            'required_parameters': ['type', 'id'],
                            'optional_parameters': ['platform']
                        }
                    }
                },
                status=400
            )
        
        # Validate resource type
        valid_types = ['story', 'chapter', 'whisper', 'profile']
        if resource_type not in valid_types:
            return JsonResponse(
                {
                    'error': {
                        'code': 'INVALID_RESOURCE_TYPE',
                        'message': f'Invalid resource type: {resource_type}',
                        'details': {
                            'valid_types': valid_types
                        }
                    }
                },
                status=400
            )
        
        # Validate platform if provided
        if platform and platform not in ['ios', 'android']:
            return JsonResponse(
                {
                    'error': {
                        'code': 'INVALID_PLATFORM',
                        'message': f'Invalid platform: {platform}',
                        'details': {
                            'valid_platforms': ['ios', 'android']
                        }
                    }
                },
                status=400
            )
        
        # Generate deep link
        try:
            if resource_type == 'story':
                deep_link = DeepLinkService.generate_story_link(resource_id, platform)
            elif resource_type == 'chapter':
                deep_link = DeepLinkService.generate_chapter_link(resource_id, platform)
            elif resource_type == 'whisper':
                deep_link = DeepLinkService.generate_whisper_link(resource_id, platform)
            elif resource_type == 'profile':
                deep_link = DeepLinkService.generate_profile_link(resource_id, platform)
            
            logger.info(
                f"Test deep link generated: {resource_type}/{resource_id}",
                extra={'test_mode': True, 'resource_type': resource_type, 'resource_id': resource_id}
            )
            
            return JsonResponse(
                {
                    'success': True,
                    'deep_link': deep_link,
                    'resource_type': resource_type,
                    'resource_id': resource_id,
                    'platform': platform or 'universal'
                },
                status=200
            )
        
        except ValueError as e:
            return JsonResponse(
                {
                    'error': {
                        'code': 'DEEP_LINK_ERROR',
                        'message': 'Failed to generate deep link',
                        'details': {
                            'error': str(e)
                        }
                    }
                },
                status=400
            )
    
    except Exception as e:
        logger.error(f"Unexpected error in test_deep_link: {str(e)}")
        return JsonResponse(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An unexpected error occurred',
                    'details': {
                        'error': str(e)
                    }
                }
            },
            status=500
        )


@require_http_methods(["GET"])
@_test_mode_required
def test_mock_data(request):
    """
    Test endpoint for generating mock data.
    
    GET /v1/test/mock-data?type=stories&count=5
    
    Query parameters:
    - type: Data type (stories, chapters, whispers, users, all) - default: all
    - count: Number of items to generate - optional
    
    Response:
    {
        "success": true,
        "data": {
            "stories": [...],
            "chapters": [...],
            "whispers": [...],
            "users": [...]
        }
    }
    
    Requirements: 18.4
    """
    try:
        # Get query parameters
        data_type = request.GET.get('type', 'all')
        count_str = request.GET.get('count')
        
        # Parse count if provided
        count = None
        if count_str:
            try:
                count = int(count_str)
                if count < 1 or count > 100:
                    return JsonResponse(
                        {
                            'error': {
                                'code': 'INVALID_COUNT',
                                'message': 'Count must be between 1 and 100',
                                'details': {
                                    'provided_count': count_str
                                }
                            }
                        },
                        status=400
                    )
            except ValueError:
                return JsonResponse(
                    {
                        'error': {
                            'code': 'INVALID_COUNT',
                            'message': 'Count must be a valid integer',
                            'details': {
                                'provided_count': count_str
                            }
                        }
                    },
                    status=400
                )
        
        # Validate data type
        valid_types = ['stories', 'chapters', 'whispers', 'users', 'all']
        if data_type not in valid_types:
            return JsonResponse(
                {
                    'error': {
                        'code': 'INVALID_DATA_TYPE',
                        'message': f'Invalid data type: {data_type}',
                        'details': {
                            'valid_types': valid_types
                        }
                    }
                },
                status=400
            )
        
        # Generate mock data
        mock_data = TestModeService.generate_mock_data(data_type, count)
        
        logger.info(
            f"Test mock data generated: type={data_type}, count={count}",
            extra={'test_mode': True, 'data_type': data_type, 'count': count}
        )
        
        return JsonResponse(
            {
                'success': True,
                'data': mock_data,
                'metadata': {
                    'type': data_type,
                    'count': count,
                    'generated_at': datetime.now().isoformat()
                }
            },
            status=200
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in test_mock_data: {str(e)}")
        return JsonResponse(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An unexpected error occurred',
                    'details': {
                        'error': str(e)
                    }
                }
            },
            status=500
        )


# Import datetime for mock data endpoint
from datetime import datetime
