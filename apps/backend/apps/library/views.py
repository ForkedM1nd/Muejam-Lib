"""Views for library and shelf management."""
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from prisma import Prisma

from .serializers import (
    ShelfSerializer,
    ShelfCreateSerializer,
    ShelfUpdateSerializer,
    ShelfItemSerializer,
    ShelfItemCreateSerializer,
    ShelfWithStoriesSerializer,
)

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
def shelves_list_create(request):
    """
    List user's shelves or create a new shelf.
    
    GET /v1/library/shelves - List user's shelves
    POST /v1/library/shelves - Create new shelf
    """
    if request.method == 'POST':
        return _create_shelf(request)
    else:
        return _list_shelves(request)


def _list_shelves(request):
    """
    List all shelves for the authenticated user.
    
    GET /v1/library/shelves
    
    Returns:
        - 200: List of shelves
        - 401: Not authenticated
        
    Requirements:
        - 4.1: List user shelves
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
        
        shelves = db.shelf.find_many(
            where={'user_id': user_profile.id},
            order={'created_at': 'desc'}
        )
        
        db.disconnect()
        
        # Serialize response
        serializer = ShelfSerializer(shelves, many=True)
        
        return Response({'data': serializer.data})
        
    except Exception as e:
        logger.error(f"Error listing shelves: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to list shelves',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _create_shelf(request):
    """
    Create a new shelf.
    
    POST /v1/library/shelves
    
    Request body:
        - name: Shelf name (required)
        
    Returns:
        - 201: Shelf created successfully
        - 400: Invalid input
        - 401: Not authenticated
        
    Requirements:
        - 4.1: Create shelf
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
    serializer = ShelfCreateSerializer(data=request.data)
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
    
    # Create shelf in database
    db = Prisma()
    
    try:
        db.connect()
        
        shelf = db.shelf.create(
            data={
                'user_id': user_profile.id,
                'name': validated_data['name'],
            }
        )
        
        db.disconnect()
        
        # Serialize response
        response_serializer = ShelfSerializer(shelf)
        
        return Response(
            {'data': response_serializer.data},
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Error creating shelf: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to create shelf',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
def update_shelf(request, shelf_id):
    """
    Update a shelf (rename).
    
    PUT /v1/library/shelves/{id}
    
    Request body:
        - name: New shelf name (required)
        
    Returns:
        - 200: Shelf updated successfully
        - 400: Invalid input
        - 401: Not authenticated
        - 403: Not authorized (not the shelf owner)
        - 404: Shelf not found
        
    Requirements:
        - 4.7: Rename shelf
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
    serializer = ShelfUpdateSerializer(data=request.data)
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
        
        # Get shelf
        shelf = db.shelf.find_unique(where={'id': shelf_id})
        
        if not shelf:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Shelf not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization
        if shelf.user_id != user_profile.id:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'You are not authorized to update this shelf',
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update shelf
        updated_shelf = db.shelf.update(
            where={'id': shelf_id},
            data={'name': validated_data['name']}
        )
        
        db.disconnect()
        
        # Serialize response
        response_serializer = ShelfSerializer(updated_shelf)
        
        return Response({'data': response_serializer.data})
        
    except Exception as e:
        logger.error(f"Error updating shelf: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to update shelf',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def delete_shelf(request, shelf_id):
    """
    Delete a shelf and all its items.
    
    DELETE /v1/library/shelves/{id}
    
    Returns:
        - 204: Shelf deleted successfully
        - 401: Not authenticated
        - 403: Not authorized (not the shelf owner)
        - 404: Shelf not found
        
    Requirements:
        - 4.5: Delete shelf removes ShelfItems
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
        
        # Get shelf
        shelf = db.shelf.find_unique(where={'id': shelf_id})
        
        if not shelf:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Shelf not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization
        if shelf.user_id != user_profile.id:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'You are not authorized to delete this shelf',
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Delete shelf (cascade will delete ShelfItems)
        db.shelf.delete(where={'id': shelf_id})
        
        db.disconnect()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    except Exception as e:
        logger.error(f"Error deleting shelf: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to delete shelf',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_library(request):
    """
    Get all shelves with their stories.
    
    GET /v1/library
    
    Returns:
        - 200: List of shelves with stories
        - 401: Not authenticated
        
    Requirements:
        - 4.4: Get all shelves with stories
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
        
        # Get all shelves with items
        shelves = db.shelf.find_many(
            where={'user_id': user_profile.id},
            include={
                'items': {
                    'include': {
                        'story': True
                    }
                }
            },
            order={'created_at': 'desc'}
        )
        
        db.disconnect()
        
        # Format response with story counts and stories
        shelves_data = []
        for shelf in shelves:
            shelf_dict = {
                'id': shelf.id,
                'user_id': shelf.user_id,
                'name': shelf.name,
                'created_at': shelf.created_at,
                'updated_at': shelf.updated_at,
                'story_count': len(shelf.items),
                'stories': [
                    {
                        'id': item.story.id,
                        'slug': item.story.slug,
                        'title': item.story.title,
                        'blurb': item.story.blurb,
                        'cover_key': item.story.cover_key,
                        'author_id': item.story.author_id,
                        'published': item.story.published,
                        'added_at': item.added_at,
                    }
                    for item in shelf.items
                    if item.story and not item.story.deleted_at
                ]
            }
            shelves_data.append(shelf_dict)
        
        return Response({'data': shelves_data})
        
    except Exception as e:
        logger.error(f"Error getting library: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to get library',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(['POST'])
def add_story_to_shelf(request, shelf_id):
    """
    Add a story to a shelf.
    
    POST /v1/library/shelves/{id}/items
    
    Request body:
        - story_id: ID of the story to add (required)
        
    Returns:
        - 201: Story added to shelf successfully
        - 400: Invalid input
        - 401: Not authenticated
        - 403: Not authorized (not the shelf owner)
        - 404: Shelf or story not found
        - 409: Story already in shelf
        
    Requirements:
        - 4.2: Add story to shelf
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
    serializer = ShelfItemCreateSerializer(data=request.data)
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
    story_id = validated_data['story_id']
    
    # Query database
    db = Prisma()
    
    try:
        db.connect()
        
        # Get shelf
        shelf = db.shelf.find_unique(where={'id': shelf_id})
        
        if not shelf:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Shelf not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization
        if shelf.user_id != user_profile.id:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'You are not authorized to modify this shelf',
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if story exists
        story = db.story.find_unique(where={'id': story_id})
        
        if not story or story.deleted_at:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Story not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if story is already in shelf
        existing_item = db.shelfitem.find_first(
            where={
                'shelf_id': shelf_id,
                'story_id': story_id
            }
        )
        
        if existing_item:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'CONFLICT',
                        'message': 'Story is already in this shelf',
                    }
                },
                status=status.HTTP_409_CONFLICT
            )
        
        # Add story to shelf
        shelf_item = db.shelfitem.create(
            data={
                'shelf_id': shelf_id,
                'story_id': story_id,
            }
        )
        
        db.disconnect()
        
        # Serialize response
        response_serializer = ShelfItemSerializer(shelf_item)
        
        return Response(
            {'data': response_serializer.data},
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Error adding story to shelf: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to add story to shelf',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def remove_story_from_shelf(request, shelf_id, story_id):
    """
    Remove a story from a shelf.
    
    DELETE /v1/library/shelves/{id}/items/{story_id}
    
    Returns:
        - 204: Story removed from shelf successfully
        - 401: Not authenticated
        - 403: Not authorized (not the shelf owner)
        - 404: Shelf or story not found in shelf
        
    Requirements:
        - 4.3: Remove story from shelf
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
        
        # Get shelf
        shelf = db.shelf.find_unique(where={'id': shelf_id})
        
        if not shelf:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Shelf not found',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization
        if shelf.user_id != user_profile.id:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': 'You are not authorized to modify this shelf',
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Find shelf item
        shelf_item = db.shelfitem.find_first(
            where={
                'shelf_id': shelf_id,
                'story_id': story_id
            }
        )
        
        if not shelf_item:
            db.disconnect()
            return Response(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Story not found in this shelf',
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Remove story from shelf
        db.shelfitem.delete(where={'id': shelf_item.id})
        
        db.disconnect()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    except Exception as e:
        logger.error(f"Error removing story from shelf: {e}")
        db.disconnect()
        return Response(
            {
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to remove story from shelf',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
