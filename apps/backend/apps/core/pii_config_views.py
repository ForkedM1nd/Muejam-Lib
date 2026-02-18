"""
PII Detection Configuration API Views

Admin endpoints for managing PII detection configuration.

Requirements:
- 9.8: Allow administrators to configure PII detection sensitivity
- 9.9: Manage whitelist for false positive patterns
"""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from prisma.enums import PIIType, PIISensitivity

from .pii_config_service import PIIConfigService
from apps.admin.permissions import IsAdministrator

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdministrator])
async def get_pii_configs(request):
    """
    Get all PII detection configurations.
    
    GET /api/admin/pii-config
    
    Returns:
        200: List of PII detection configurations
        403: User is not an administrator
    
    Requirements: 9.8
    """
    try:
        service = PIIConfigService()
        configs = await service.get_all_configs()
        
        return Response({
            'configs': configs
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error fetching PII configs: {str(e)}")
        return Response(
            {'error': 'Failed to fetch PII configurations'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdministrator])
async def get_pii_config(request, pii_type):
    """
    Get configuration for a specific PII type.
    
    GET /api/admin/pii-config/{pii_type}
    
    Args:
        pii_type: One of EMAIL, PHONE, SSN, CREDIT_CARD
    
    Returns:
        200: PII detection configuration
        404: Configuration not found
        403: User is not an administrator
    
    Requirements: 9.8
    """
    try:
        # Validate PII type
        try:
            pii_type_enum = PIIType[pii_type.upper()]
        except KeyError:
            return Response(
                {'error': f'Invalid PII type: {pii_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = PIIConfigService()
        config = await service.get_config(pii_type_enum)
        
        if not config:
            return Response(
                {'error': 'Configuration not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(config, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error fetching PII config: {str(e)}")
        return Response(
            {'error': 'Failed to fetch PII configuration'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsAdministrator])
async def update_pii_config(request, pii_type):
    """
    Update configuration for a specific PII type.
    
    PUT /api/admin/pii-config/{pii_type}
    
    Request body:
        {
            "sensitivity": "STRICT" | "MODERATE" | "PERMISSIVE",  // optional
            "enabled": true | false,  // optional
            "whitelist": ["pattern1", "pattern2"],  // optional
            "pattern": "custom regex pattern"  // optional
        }
    
    Args:
        pii_type: One of EMAIL, PHONE, SSN, CREDIT_CARD
    
    Returns:
        200: Updated configuration
        400: Invalid request data
        403: User is not an administrator
    
    Requirements: 9.8, 9.9
    """
    try:
        # Validate PII type
        try:
            pii_type_enum = PIIType[pii_type.upper()]
        except KeyError:
            return Response(
                {'error': f'Invalid PII type: {pii_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract and validate request data
        sensitivity = request.data.get('sensitivity')
        enabled = request.data.get('enabled')
        whitelist = request.data.get('whitelist')
        pattern = request.data.get('pattern')
        
        # Validate sensitivity if provided
        if sensitivity:
            try:
                sensitivity = PIISensitivity[sensitivity.upper()]
            except KeyError:
                return Response(
                    {'error': f'Invalid sensitivity: {sensitivity}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validate whitelist if provided
        if whitelist is not None:
            if not isinstance(whitelist, list):
                return Response(
                    {'error': 'Whitelist must be an array'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not all(isinstance(p, str) for p in whitelist):
                return Response(
                    {'error': 'All whitelist patterns must be strings'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Update configuration
        service = PIIConfigService()
        user_id = request.clerk_user_id
        
        config = await service.update_config(
            pii_type=pii_type_enum,
            user_id=user_id,
            sensitivity=sensitivity,
            enabled=enabled,
            whitelist=whitelist,
            pattern=pattern
        )
        
        return Response(config, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error updating PII config: {str(e)}")
        return Response(
            {'error': 'Failed to update PII configuration'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdministrator])
async def add_to_whitelist(request, pii_type):
    """
    Add patterns to the whitelist for a PII type.
    
    POST /api/admin/pii-config/{pii_type}/whitelist
    
    Request body:
        {
            "patterns": ["pattern1", "pattern2"]
        }
    
    Args:
        pii_type: One of EMAIL, PHONE, SSN, CREDIT_CARD
    
    Returns:
        200: Updated configuration
        400: Invalid request data
        403: User is not an administrator
    
    Requirements: 9.9
    """
    try:
        # Validate PII type
        try:
            pii_type_enum = PIIType[pii_type.upper()]
        except KeyError:
            return Response(
                {'error': f'Invalid PII type: {pii_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate patterns
        patterns = request.data.get('patterns', [])
        if not isinstance(patterns, list):
            return Response(
                {'error': 'Patterns must be an array'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not patterns:
            return Response(
                {'error': 'At least one pattern is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not all(isinstance(p, str) for p in patterns):
            return Response(
                {'error': 'All patterns must be strings'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add to whitelist
        service = PIIConfigService()
        user_id = request.clerk_user_id
        
        config = await service.add_to_whitelist(
            pii_type=pii_type_enum,
            user_id=user_id,
            patterns=patterns
        )
        
        return Response(config, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error adding to whitelist: {str(e)}")
        return Response(
            {'error': 'Failed to add patterns to whitelist'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdministrator])
async def remove_from_whitelist(request, pii_type):
    """
    Remove patterns from the whitelist for a PII type.
    
    DELETE /api/admin/pii-config/{pii_type}/whitelist
    
    Request body:
        {
            "patterns": ["pattern1", "pattern2"]
        }
    
    Args:
        pii_type: One of EMAIL, PHONE, SSN, CREDIT_CARD
    
    Returns:
        200: Updated configuration
        400: Invalid request data
        403: User is not an administrator
    
    Requirements: 9.9
    """
    try:
        # Validate PII type
        try:
            pii_type_enum = PIIType[pii_type.upper()]
        except KeyError:
            return Response(
                {'error': f'Invalid PII type: {pii_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate patterns
        patterns = request.data.get('patterns', [])
        if not isinstance(patterns, list):
            return Response(
                {'error': 'Patterns must be an array'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not patterns:
            return Response(
                {'error': 'At least one pattern is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not all(isinstance(p, str) for p in patterns):
            return Response(
                {'error': 'All patterns must be strings'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove from whitelist
        service = PIIConfigService()
        user_id = request.clerk_user_id
        
        config = await service.remove_from_whitelist(
            pii_type=pii_type_enum,
            user_id=user_id,
            patterns=patterns
        )
        
        return Response(config, status=status.HTTP_200_OK)
    
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error removing from whitelist: {str(e)}")
        return Response(
            {'error': 'Failed to remove patterns from whitelist'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdministrator])
async def initialize_pii_configs(request):
    """
    Initialize default PII detection configurations.
    
    POST /api/admin/pii-config/initialize
    
    Returns:
        200: Configurations initialized
        403: User is not an administrator
    
    Requirements: 9.8
    """
    try:
        service = PIIConfigService()
        user_id = request.clerk_user_id
        
        await service.initialize_default_configs(user_id)
        
        # Return all configs
        configs = await service.get_all_configs()
        
        return Response({
            'message': 'PII detection configurations initialized',
            'configs': configs
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error initializing PII configs: {str(e)}")
        return Response(
            {'error': 'Failed to initialize PII configurations'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
