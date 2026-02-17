"""Views for text highlighting system."""
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from prisma import Prisma

from .serializers import (
    HighlightSerializer,
    HighlightCreateSerializer,
)

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
def highlights(request, chapter_id):
    """
    List highlights or create a new highlight for a chapter.
    
    GET /v1/chapters/{id}/highlights - List highlights
    POST /v1/chapters/{id}/highlights - Create highlight
    """
    if request.method == 'POST':
        return _create_highlight(request, chapter_id)
    else:
        return _list_highlights(request, chapter_id)


def _create_highlight(request, chapter_id):
    """
    Create a highlight in a chapter.
    
    POST /v1/chapters/{id}/highlights
    
    Request body:
        - start_offset: Starting character offset (required)
        - end_offset: Ending character offset (required)
        
    Returns:
        - 201: Highlight created successfully
        - 400: Invalid input (offsets invalid or out of bounds)
        - 401: Not authenticated
        - 404: Chapter not found
        
    Requirements:
        - 8.1: Capture start and end offsets
        - 8.2: Save highlight with offsets
        - 8.7: Validate start_offset < end_offset
        - 8.8: Validate offsets within chapter content length
    """
    # Check authentication
    user_id = getattr(request, 'clerk_user_id', None)
    user_profile = getattr(request, 'user_profile', None)
    
    if not user_id or not user_profile:
        return Response(
            {
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required',
                }
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Validate input
    serializer = HighlightCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid input',
                    'details': serializer.errors
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Check if chapter exists and get content length
        chapter = db.chapter.find_unique(where={'id': chapter_id})
        
        if not chapter or chapter.deleted_at:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Chapter not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate offsets are within chapter content length
        content_length = len(chapter.content)
        if validated_data['end_offset'] > content_length:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': f'Offsets must be within chapter content length (0-{content_length})',
                        'details': {
                            'end_offset': f'Must be <= {content_length}'
                        }
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create highlight
        highlight = db.highlight.create(
            data={
                'user_id': user_profile.id,
                'chapter_id': chapter_id,
                'start_offset': validated_data['start_offset'],
                'end_offset': validated_data['end_offset']
            }
        )
        
        db.disconnect()
        
        # Serialize response
        response_serializer = HighlightSerializer(highlight)
        
        return Response(
            {'data': response_serializer.data},
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Error creating highlight: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to create highlight',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _list_highlights(request, chapter_id):
    """
    List all highlights for a chapter.
    
    GET /v1/chapters/{id}/highlights
    
    Returns:
        - 200: List of highlights
        - 401: Not authenticated
        - 404: Chapter not found
        
    Requirements:
        - 8.5: List highlights for a chapter
    """
    # Check authentication
    user_id = getattr(request, 'clerk_user_id', None)
    user_profile = getattr(request, 'user_profile', None)
    
    if not user_id or not user_profile:
        return Response(
            {
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required',
                }
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Check if chapter exists
        chapter = db.chapter.find_unique(where={'id': chapter_id})
        
        if not chapter or chapter.deleted_at:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Chapter not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get highlights for this user and chapter
        highlights = db.highlight.find_many(
            where={
                'user_id': user_profile.id,
                'chapter_id': chapter_id
            },
            order={'created_at': 'asc'}  # Order by creation time
        )
        
        db.disconnect()
        
        # Serialize response
        serializer = HighlightSerializer(highlights, many=True)
        
        return Response({'data': serializer.data})
        
    except Exception as e:
        logger.error(f"Error listing highlights: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to list highlights',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def delete_highlight(request, highlight_id):
    """
    Delete a highlight.
    
    DELETE /v1/highlights/{id}
    
    Returns:
        - 204: Highlight deleted successfully
        - 401: Not authenticated
        - 403: Not authorized (not the highlight owner)
        - 404: Highlight not found
        
    Requirements:
        - 8.5: Delete highlight
    """
    # Check authentication
    user_id = getattr(request, 'clerk_user_id', None)
    user_profile = getattr(request, 'user_profile', None)
    
    if not user_id or not user_profile:
        return Response(
            {
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required',
                }
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Get highlight
        highlight = db.highlight.find_unique(where={'id': highlight_id})
        
        if not highlight:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Highlight not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization
        if highlight.user_id != user_profile.id:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'You are not authorized to delete this highlight',
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Delete highlight
        db.highlight.delete(where={'id': highlight_id})
        
        db.disconnect()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    except Exception as e:
        logger.error(f"Error deleting highlight: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to delete highlight',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
