"""
API Key Management Views

This module provides REST API endpoints for managing API keys.

Requirements: 6.10
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .api_key_auth import APIKeyService
import asyncio


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_api_key(request):
    """
    Create a new API key for the authenticated user.
    
    Request body:
        - name (str, required): A descriptive name for the API key
        - expires_in_days (int, optional): Number of days until expiration (default: 365)
        - permissions (dict, optional): Scoped permissions for the key
    
    Response:
        - id (str): The API key ID
        - name (str): The API key name
        - api_key (str): The plain text API key (only shown once!)
        - created_at (str): Creation timestamp
        - expires_at (str): Expiration timestamp
        
    Status codes:
        - 201: API key created successfully
        - 400: Invalid request data
        - 401: User not authenticated
    """
    name = request.data.get('name')
    expires_in_days = request.data.get('expires_in_days', 365)
    permissions = request.data.get('permissions', {})
    
    if not name:
        return Response(
            {'error': 'Name is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get user ID from request
        user_id = request.user.get('id') if isinstance(request.user, dict) else str(request.user.id)
        
        # Create API key
        api_key_obj, plain_key = asyncio.run(
            APIKeyService.create_api_key(
                user_id=user_id,
                name=name,
                expires_in_days=expires_in_days,
                permissions=permissions
            )
        )
        
        return Response({
            'id': api_key_obj.id,
            'name': api_key_obj.name,
            'api_key': plain_key,  # Only shown once!
            'created_at': api_key_obj.created_at.isoformat(),
            'expires_at': api_key_obj.expires_at.isoformat(),
            'permissions': api_key_obj.permissions,
            'warning': 'Store this API key securely. It will not be shown again.'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to create API key: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_api_keys(request):
    """
    List all API keys for the authenticated user.
    
    Query parameters:
        - include_inactive (bool, optional): Include inactive keys (default: false)
    
    Response:
        List of API key objects (without the actual key values):
        - id (str): The API key ID
        - name (str): The API key name
        - created_at (str): Creation timestamp
        - last_used_at (str): Last usage timestamp
        - expires_at (str): Expiration timestamp
        - is_active (bool): Whether the key is active
        - permissions (dict): Scoped permissions
        
    Status codes:
        - 200: Success
        - 401: User not authenticated
    """
    include_inactive = request.query_params.get('include_inactive', 'false').lower() == 'true'
    
    try:
        # Get user ID from request
        user_id = request.user.get('id') if isinstance(request.user, dict) else str(request.user.id)
        
        # List API keys
        api_keys = asyncio.run(
            APIKeyService.list_user_api_keys(
                user_id=user_id,
                include_inactive=include_inactive
            )
        )
        
        # Format response
        keys_data = []
        for key in api_keys:
            keys_data.append({
                'id': key.id,
                'name': key.name,
                'created_at': key.created_at.isoformat(),
                'last_used_at': key.last_used_at.isoformat() if key.last_used_at else None,
                'expires_at': key.expires_at.isoformat(),
                'is_active': key.is_active,
                'is_expired': key.expires_at < timezone.now(),
                'permissions': key.permissions
            })
        
        return Response(keys_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to list API keys: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rotate_api_key(request, key_id):
    """
    Rotate an existing API key by generating a new key value.
    
    Path parameters:
        - key_id (str): The ID of the API key to rotate
    
    Response:
        - id (str): The API key ID
        - name (str): The API key name
        - api_key (str): The new plain text API key (only shown once!)
        - created_at (str): Original creation timestamp
        - expires_at (str): Expiration timestamp
        
    Status codes:
        - 200: API key rotated successfully
        - 401: User not authenticated
        - 403: User doesn't own this API key
        - 404: API key not found
    """
    try:
        # Get user ID from request
        user_id = request.user.get('id') if isinstance(request.user, dict) else str(request.user.id)
        
        # Verify ownership
        api_keys = asyncio.run(APIKeyService.list_user_api_keys(user_id, include_inactive=True))
        if not any(key.id == key_id for key in api_keys):
            return Response(
                {'error': 'API key not found or access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Rotate API key
        api_key_obj, plain_key = asyncio.run(APIKeyService.rotate_api_key(key_id))
        
        return Response({
            'id': api_key_obj.id,
            'name': api_key_obj.name,
            'api_key': plain_key,  # Only shown once!
            'created_at': api_key_obj.created_at.isoformat(),
            'expires_at': api_key_obj.expires_at.isoformat(),
            'permissions': api_key_obj.permissions,
            'warning': 'Store this API key securely. It will not be shown again.'
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to rotate API key: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def revoke_api_key(request, key_id):
    """
    Revoke an API key by marking it as inactive.
    
    Path parameters:
        - key_id (str): The ID of the API key to revoke
    
    Response:
        - message (str): Success message
        
    Status codes:
        - 200: API key revoked successfully
        - 401: User not authenticated
        - 403: User doesn't own this API key
        - 404: API key not found
    """
    try:
        # Get user ID from request
        user_id = request.user.get('id') if isinstance(request.user, dict) else str(request.user.id)
        
        # Verify ownership
        api_keys = asyncio.run(APIKeyService.list_user_api_keys(user_id, include_inactive=True))
        if not any(key.id == key_id for key in api_keys):
            return Response(
                {'error': 'API key not found or access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Revoke API key
        asyncio.run(APIKeyService.revoke_api_key(key_id))
        
        return Response({
            'message': 'API key revoked successfully'
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to revoke API key: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
