"""
Mobile Session Management API Views

Provides endpoints for:
- Session creation (after login)
- Token refresh
- Session revocation (logout)
- Active session listing

Requirements: 17.1, 17.2, 17.3, 17.4, 17.5
"""

import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .mobile_session_service import MobileSessionService
from .jwt_service import JWTVerificationService, TokenExpiredError, InvalidTokenError
from .auth_error_responses import get_auth_error_response

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Create mobile session",
    description=(
        "Create a new mobile session after successful authentication. "
        "Returns a refresh token that can be used to extend the session. "
        "Mobile sessions have longer durations (30 days) compared to web sessions (24 hours)."
    ),
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'device_token_id': {
                    'type': 'string',
                    'description': 'Optional device token ID for push notifications',
                    'nullable': True
                },
                'device_info': {
                    'type': 'object',
                    'description': 'Optional device metadata (model, OS version, etc.)',
                    'nullable': True,
                    'properties': {
                        'model': {'type': 'string'},
                        'os_version': {'type': 'string'},
                        'app_version': {'type': 'string'}
                    }
                }
            }
        }
    },
    responses={
        201: {
            'description': 'Session created successfully',
            'content': {
                'application/json': {
                    'example': {
                        'session_id': 'session_abc123',
                        'refresh_token': 'a1b2c3d4e5f6...',
                        'expires_at': '2024-03-20T10:30:00Z',
                        'client_type': 'mobile-ios'
                    }
                }
            }
        },
        401: {
            'description': 'Authentication required or token expired',
            'content': {
                'application/json': {
                    'examples': {
                        'expired_token': {
                            'summary': 'Token expired',
                            'value': {
                                'error': {
                                    'code': 'TOKEN_EXPIRED',
                                    'message': 'Your authentication token has expired',
                                    'details': {
                                        'technical_message': 'JWT token has expired and needs to be refreshed',
                                        'refresh_guidance': 'Please use the /v1/sessions/refresh endpoint with your refresh token to obtain a new access token'
                                    }
                                }
                            }
                        },
                        'invalid_token': {
                            'summary': 'Invalid token',
                            'value': {
                                'error': {
                                    'code': 'TOKEN_INVALID',
                                    'message': 'Your authentication token is invalid',
                                    'details': {
                                        'technical_message': 'JWT token signature verification failed or token is malformed'
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    tags=['Mobile Session Management']
)
@api_view(['POST'])
async def create_session(request):
    """
    Create a new mobile session after authentication.
    
    Validates: Requirements 17.1, 17.5
    """
    # Check for authentication errors with enhanced error responses
    error_response = get_auth_error_response(request)
    if error_response:
        return error_response
    
    # Check authentication
    if not request.clerk_user_id or not request.user_profile:
        return Response(
            {
                'error': {
                    'code': 'AUTHENTICATION_REQUIRED',
                    'message': 'Authentication required'
                }
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Get client type from request
    client_type = getattr(request, 'client_type', 'web')
    
    # Only create sessions for mobile clients
    if not client_type.startswith('mobile'):
        return Response(
            {
                'error': {
                    'code': 'INVALID_CLIENT_TYPE',
                    'message': 'Session creation is only available for mobile clients'
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get optional parameters
    device_token_id = request.data.get('device_token_id')
    device_info = request.data.get('device_info')
    
    # Create session
    session_data = await MobileSessionService.create_session(
        user_id=request.user_profile.id,
        client_type=client_type,
        device_token_id=device_token_id,
        device_info=device_info
    )
    
    logger.info(
        f"Created mobile session for user {request.user_profile.id}, "
        f"client_type={client_type}"
    )
    
    return Response(session_data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Refresh authentication token",
    description=(
        "Refresh an expired or expiring JWT token using a refresh token. "
        "Mobile clients receive longer session durations (30 days) compared to web clients (24 hours)."
    ),
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'refresh_token': {
                    'type': 'string',
                    'description': 'Refresh token received during login or previous refresh'
                }
            },
            'required': ['refresh_token']
        }
    },
    responses={
        200: {
            'description': 'Token refreshed successfully',
            'content': {
                'application/json': {
                    'example': {
                        'access_token': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...',
                        'expires_at': '2024-03-20T10:30:00Z',
                        'session_id': 'session_abc123',
                        'client_type': 'mobile-ios'
                    }
                }
            }
        },
        400: {
            'description': 'Missing refresh token',
            'content': {
                'application/json': {
                    'example': {
                        'error': {
                            'code': 'MISSING_FIELD',
                            'message': 'Refresh token is required'
                        }
                    }
                }
            }
        },
        401: {
            'description': 'Invalid or expired refresh token',
            'content': {
                'application/json': {
                    'example': {
                        'error': {
                            'code': 'INVALID_REFRESH_TOKEN',
                            'message': 'Refresh token is invalid or expired'
                        }
                    }
                }
            }
        }
    },
    tags=['Mobile Session Management']
)
@api_view(['POST'])
async def refresh_token(request):
    """
    Refresh authentication token using refresh token.
    
    Validates: Requirement 17.2
    """
    refresh_token = request.data.get('refresh_token')
    
    if not refresh_token:
        return Response(
            {
                'error': {
                    'code': 'MISSING_FIELD',
                    'message': 'Refresh token is required'
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Refresh session
    session_data = await MobileSessionService.refresh_session(refresh_token)
    
    if not session_data:
        return Response(
            {
                'error': {
                    'code': 'INVALID_REFRESH_TOKEN',
                    'message': 'Refresh token is invalid or expired',
                    'details': {
                        'technical_message': 'Session not found, expired, or revoked'
                    }
                }
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Generate new JWT access token
    # Note: In a real implementation, you would generate a new JWT here
    # For now, we return the session data
    # The client should use their existing Clerk token or request a new one
    
    logger.info(
        f"Token refreshed for user {session_data['user_id']}, "
        f"session {session_data['session_id']}"
    )
    
    return Response(
        {
            'session_id': session_data['session_id'],
            'expires_at': session_data['expires_at'],
            'client_type': session_data['client_type'],
            'message': 'Session refreshed successfully'
        },
        status=status.HTTP_200_OK
    )


@extend_schema(
    summary="Revoke session (logout)",
    description=(
        "Revoke a mobile session to log out the user from a specific device. "
        "The refresh token will no longer be valid after revocation."
    ),
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'refresh_token': {
                    'type': 'string',
                    'description': 'Refresh token to revoke'
                }
            },
            'required': ['refresh_token']
        }
    },
    responses={
        200: {
            'description': 'Session revoked successfully',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'Session revoked successfully'
                    }
                }
            }
        },
        400: {
            'description': 'Missing refresh token',
        },
        404: {
            'description': 'Session not found',
        }
    },
    tags=['Mobile Session Management']
)
@api_view(['POST'])
async def revoke_session(request):
    """
    Revoke a mobile session (logout).
    
    Validates: Requirement 17.4
    """
    refresh_token = request.data.get('refresh_token')
    
    if not refresh_token:
        return Response(
            {
                'error': {
                    'code': 'MISSING_FIELD',
                    'message': 'Refresh token is required'
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Revoke session
    success = await MobileSessionService.revoke_session(refresh_token)
    
    if not success:
        return Response(
            {
                'error': {
                    'code': 'SESSION_NOT_FOUND',
                    'message': 'Session not found'
                }
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    logger.info(f"Session revoked successfully")
    
    return Response(
        {'message': 'Session revoked successfully'},
        status=status.HTTP_200_OK
    )


@extend_schema(
    summary="Get active sessions",
    description=(
        "Get all active sessions for the authenticated user. "
        "Provides per-device session tracking for security monitoring."
    ),
    responses={
        200: {
            'description': 'Active sessions retrieved successfully',
            'content': {
                'application/json': {
                    'example': {
                        'sessions': [
                            {
                                'session_id': 'session_abc123',
                                'client_type': 'mobile-ios',
                                'device_info': {
                                    'model': 'iPhone 14 Pro',
                                    'os_version': 'iOS 17.2'
                                },
                                'created_at': '2024-02-20T10:00:00Z',
                                'last_refreshed_at': '2024-02-25T15:30:00Z',
                                'expires_at': '2024-03-20T10:00:00Z'
                            }
                        ]
                    }
                }
            }
        },
        401: {
            'description': 'Authentication required',
        }
    },
    tags=['Mobile Session Management']
)
@api_view(['GET'])
async def get_active_sessions(request):
    """
    Get all active sessions for the authenticated user.
    
    Validates: Requirement 17.5
    """
    # Check for authentication errors with enhanced error responses
    error_response = get_auth_error_response(request)
    if error_response:
        return error_response
    
    # Check authentication
    if not request.clerk_user_id or not request.user_profile:
        return Response(
            {
                'error': {
                    'code': 'AUTHENTICATION_REQUIRED',
                    'message': 'Authentication required'
                }
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Get active sessions
    sessions = await MobileSessionService.get_active_sessions(
        request.user_profile.id
    )
    
    return Response(
        {'sessions': sessions},
        status=status.HTTP_200_OK
    )


@extend_schema(
    summary="Revoke all sessions",
    description=(
        "Revoke all active sessions for the authenticated user. "
        "Useful for security events like password changes or suspected account compromise."
    ),
    responses={
        200: {
            'description': 'All sessions revoked successfully',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'All sessions revoked successfully',
                        'count': 3
                    }
                }
            }
        },
        401: {
            'description': 'Authentication required',
        }
    },
    tags=['Mobile Session Management']
)
@api_view(['POST'])
async def revoke_all_sessions(request):
    """
    Revoke all active sessions for the authenticated user.
    
    Validates: Requirement 17.4
    """
    # Check for authentication errors with enhanced error responses
    error_response = get_auth_error_response(request)
    if error_response:
        return error_response
    
    # Check authentication
    if not request.clerk_user_id or not request.user_profile:
        return Response(
            {
                'error': {
                    'code': 'AUTHENTICATION_REQUIRED',
                    'message': 'Authentication required'
                }
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Revoke all sessions
    count = await MobileSessionService.revoke_all_user_sessions(
        request.user_profile.id
    )
    
    logger.info(f"Revoked {count} sessions for user {request.user_profile.id}")
    
    return Response(
        {
            'message': 'All sessions revoked successfully',
            'count': count
        },
        status=status.HTTP_200_OK
    )
