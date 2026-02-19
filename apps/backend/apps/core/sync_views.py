"""
Data Synchronization Views for Mobile Backend Integration.

This module provides endpoints for mobile clients to synchronize data
efficiently, including incremental updates and batch operations.

Validates Requirements: 10.1, 10.3, 10.5
"""

from datetime import datetime, timezone
from typing import Dict, List, Any
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from prisma import Prisma
import asyncio
from .offline_support_service import OfflineSupportService
from .sync_conflict_service import SyncConflictService


@api_view(['GET'])
def sync_stories(request):
    """
    Get stories modified since a given timestamp for incremental sync.
    
    GET /v1/sync/stories?since=<ISO8601_timestamp>&limit=<int>
    
    Query parameters:
        - since: ISO 8601 timestamp (required) - Get stories modified after this time
        - limit: Maximum number of stories to return (optional, default: 100, max: 500)
        
    Returns:
        - 200: List of modified stories with sync metadata
        - 400: Invalid timestamp format or missing required parameter
        - 401: Not authenticated
        
    Validates: Requirement 10.1
    """
    # Check authentication
    user_id = getattr(request, 'clerk_user_id', None)
    if not user_id:
        return Response(
            {
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required',
                }
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Get and validate 'since' parameter
    since_param = request.GET.get('since')
    if not since_param:
        return Response(
            {
                'error': {
                    'code': 'MISSING_PARAMETER',
                    'message': 'Required parameter "since" is missing',
                    'details': {
                        'parameter': 'since',
                        'format': 'ISO 8601 timestamp (e.g., 2024-01-01T00:00:00Z)'
                    }
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Parse timestamp
    try:
        since_timestamp = datetime.fromisoformat(since_param.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return Response(
            {
                'error': {
                    'code': 'INVALID_TIMESTAMP',
                    'message': 'Invalid timestamp format',
                    'details': {
                        'parameter': 'since',
                        'provided': since_param,
                        'expected_format': 'ISO 8601 (e.g., 2024-01-01T00:00:00Z)'
                    }
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get and validate 'limit' parameter
    limit = request.GET.get('limit', '100')
    try:
        limit = int(limit)
        if limit < 1:
            limit = 100
        elif limit > 500:
            limit = 500
    except ValueError:
        limit = 100
    
    # Query database for modified stories
    db = Prisma()
    try:
        db.connect()
        
        # Get stories modified since timestamp
        # Include both created and updated stories
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            stories = loop.run_until_complete(
                db.story.find_many(
                    where={
                        'OR': [
                            {'updated_at': {'gte': since_timestamp}},
                            {'created_at': {'gte': since_timestamp}},
                        ],
                        'deleted_at': None,  # Exclude deleted stories
                    },
                    order={'updated_at': 'desc'},
                    take=limit,
                    include={
                        'author': True,
                        'tags': {
                            'include': {
                                'tag': True
                            }
                        }
                    }
                )
            )
        finally:
            loop.close()
        
        # Format response
        stories_data = []
        for story in stories:
            story_dict = {
                'id': story.id,
                'slug': story.slug,
                'title': story.title,
                'blurb': story.blurb,
                'cover_key': story.cover_key,
                'author_id': story.author_id,
                'author': {
                    'id': story.author.id,
                    'username': story.author.username,
                    'display_name': story.author.display_name,
                    'avatar_key': story.author.avatar_key,
                } if story.author else None,
                'published': story.published,
                'published_at': story.published_at.isoformat() if story.published_at else None,
                'created_at': story.created_at.isoformat(),
                'updated_at': story.updated_at.isoformat(),
                'tags': [
                    {
                        'id': story_tag.tag.id,
                        'name': story_tag.tag.name,
                        'slug': story_tag.tag.slug,
                    }
                    for story_tag in story.tags
                ] if story.tags else [],
            }
            stories_data.append(story_dict)
        
        # Get current server timestamp for next sync
        current_timestamp = datetime.now(timezone.utc)
        
        response_data = {
            'stories': stories_data,
            'sync_metadata': {
                'since': since_timestamp.isoformat(),
                'current_timestamp': current_timestamp.isoformat(),
                'count': len(stories_data),
                'has_more': len(stories_data) == limit,
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'error': {
                    'code': 'SYNC_ERROR',
                    'message': 'Failed to retrieve stories',
                    'details': str(e)
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if db.is_connected():
            db.disconnect()


@api_view(['GET'])
def sync_whispers(request):
    """
    Get whispers modified since a given timestamp for incremental sync.
    
    GET /v1/sync/whispers?since=<ISO8601_timestamp>&limit=<int>&scope=<scope>
    
    Query parameters:
        - since: ISO 8601 timestamp (required) - Get whispers modified after this time
        - limit: Maximum number of whispers to return (optional, default: 100, max: 500)
        - scope: Filter by scope (optional: GLOBAL, STORY, HIGHLIGHT)
        - story_id: Filter by story ID (optional, requires scope=STORY)
        
    Returns:
        - 200: List of modified whispers with sync metadata
        - 400: Invalid timestamp format or missing required parameter
        - 401: Not authenticated
        
    Validates: Requirement 10.1
    """
    # Check authentication
    user_id = getattr(request, 'clerk_user_id', None)
    if not user_id:
        return Response(
            {
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required',
                }
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Get and validate 'since' parameter
    since_param = request.GET.get('since')
    if not since_param:
        return Response(
            {
                'error': {
                    'code': 'MISSING_PARAMETER',
                    'message': 'Required parameter "since" is missing',
                    'details': {
                        'parameter': 'since',
                        'format': 'ISO 8601 timestamp (e.g., 2024-01-01T00:00:00Z)'
                    }
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Parse timestamp
    try:
        since_timestamp = datetime.fromisoformat(since_param.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return Response(
            {
                'error': {
                    'code': 'INVALID_TIMESTAMP',
                    'message': 'Invalid timestamp format',
                    'details': {
                        'parameter': 'since',
                        'provided': since_param,
                        'expected_format': 'ISO 8601 (e.g., 2024-01-01T00:00:00Z)'
                    }
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get and validate 'limit' parameter
    limit = request.GET.get('limit', '100')
    try:
        limit = int(limit)
        if limit < 1:
            limit = 100
        elif limit > 500:
            limit = 500
    except ValueError:
        limit = 100
    
    # Get optional filters
    scope = request.GET.get('scope')
    story_id = request.GET.get('story_id')
    
    # Build query filters
    where_clause = {
        'created_at': {'gte': since_timestamp},
        'deleted_at': None,  # Exclude deleted whispers
    }
    
    if scope:
        where_clause['scope'] = scope
    
    if story_id:
        where_clause['story_id'] = story_id
    
    # Query database for modified whispers
    db = Prisma()
    try:
        db.connect()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            whispers = loop.run_until_complete(
                db.whisper.find_many(
                    where=where_clause,
                    order={'created_at': 'desc'},
                    take=limit,
                    include={
                        'user': True,
                        'story': True,
                        'likes': True,
                    }
                )
            )
        finally:
            loop.close()
        
        # Format response
        whispers_data = []
        for whisper in whispers:
            whisper_dict = {
                'id': whisper.id,
                'user_id': whisper.user_id,
                'user': {
                    'id': whisper.user.id,
                    'username': whisper.user.username,
                    'display_name': whisper.user.display_name,
                    'avatar_key': whisper.user.avatar_key,
                } if whisper.user else None,
                'content': whisper.content,
                'media_key': whisper.media_key,
                'scope': whisper.scope,
                'story_id': whisper.story_id,
                'highlight_id': whisper.highlight_id,
                'parent_id': whisper.parent_id,
                'created_at': whisper.created_at.isoformat(),
                'likes_count': len(whisper.likes) if whisper.likes else 0,
            }
            whispers_data.append(whisper_dict)
        
        # Get current server timestamp for next sync
        current_timestamp = datetime.now(timezone.utc)
        
        response_data = {
            'whispers': whispers_data,
            'sync_metadata': {
                'since': since_timestamp.isoformat(),
                'current_timestamp': current_timestamp.isoformat(),
                'count': len(whispers_data),
                'has_more': len(whispers_data) == limit,
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'error': {
                    'code': 'SYNC_ERROR',
                    'message': 'Failed to retrieve whispers',
                    'details': str(e)
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if db.is_connected():
            db.disconnect()


@api_view(['POST'])
def sync_batch(request):
    """
    Submit batch operations for efficient synchronization.
    
    POST /v1/sync/batch
    
    Request body:
        {
            "operations": [
                {
                    "type": "create_whisper" | "update_reading_progress" | "create_bookmark",
                    "data": { ... operation-specific data ... }
                },
                ...
            ]
        }
        
    Returns:
        - 200: Batch operation results
        - 400: Invalid request format
        - 401: Not authenticated
        - 207: Multi-status (some operations succeeded, some failed)
        
    Validates: Requirement 10.3
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
    
    # Validate request body
    operations = request.data.get('operations', [])
    if not isinstance(operations, list):
        return Response(
            {
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Request body must contain "operations" array',
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(operations) == 0:
        return Response(
            {
                'error': {
                    'code': 'EMPTY_BATCH',
                    'message': 'Operations array cannot be empty',
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(operations) > 100:
        return Response(
            {
                'error': {
                    'code': 'BATCH_TOO_LARGE',
                    'message': 'Maximum 100 operations per batch',
                    'details': {
                        'provided': len(operations),
                        'maximum': 100
                    }
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Process each operation
    results = []
    db = Prisma()
    
    try:
        db.connect()
        
        for idx, operation in enumerate(operations):
            operation_type = operation.get('type')
            operation_data = operation.get('data', {})
            
            result = {
                'index': idx,
                'type': operation_type,
                'status': 'pending',
            }
            
            try:
                if operation_type == 'update_reading_progress':
                    result = _process_reading_progress_update(
                        db, user_id, operation_data, idx
                    )
                elif operation_type == 'create_bookmark':
                    result = _process_bookmark_creation(
                        db, user_id, operation_data, idx
                    )
                elif operation_type == 'create_whisper':
                    result = _process_whisper_creation(
                        db, user_id, user_profile, operation_data, idx
                    )
                else:
                    result = {
                        'index': idx,
                        'type': operation_type,
                        'status': 'error',
                        'error': {
                            'code': 'UNKNOWN_OPERATION',
                            'message': f'Unknown operation type: {operation_type}',
                        }
                    }
            except Exception as e:
                result = {
                    'index': idx,
                    'type': operation_type,
                    'status': 'error',
                    'error': {
                        'code': 'OPERATION_FAILED',
                        'message': str(e),
                    }
                }
            
            results.append(result)
        
        # Determine overall status
        success_count = sum(1 for r in results if r['status'] == 'success')
        error_count = sum(1 for r in results if r['status'] == 'error')
        conflict_count = sum(1 for r in results if r['status'] == 'conflict')
        
        response_data = {
            'results': results,
            'summary': {
                'total': len(operations),
                'success': success_count,
                'error': error_count,
                'conflict': conflict_count,
            }
        }
        
        # Return 409 Conflict if any conflicts detected
        if conflict_count > 0:
            return Response(response_data, status=status.HTTP_409_CONFLICT)
        # Return 207 Multi-Status if some operations failed
        elif error_count > 0 and success_count > 0:
            return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
        elif error_count == len(operations):
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'error': {
                    'code': 'BATCH_ERROR',
                    'message': 'Failed to process batch operations',
                    'details': str(e)
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if db.is_connected():
            db.disconnect()


def _process_reading_progress_update(
    db: Prisma,
    user_id: str,
    data: Dict[str, Any],
    index: int
) -> Dict[str, Any]:
    """Process a reading progress update operation with conflict detection."""
    chapter_id = data.get('chapter_id')
    offset = data.get('offset')
    last_sync = data.get('last_sync')
    
    if not chapter_id or offset is None:
        return {
            'index': index,
            'type': 'update_reading_progress',
            'status': 'error',
            'error': {
                'code': 'MISSING_FIELDS',
                'message': 'chapter_id and offset are required',
            }
        }
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Parse client timestamp if provided
        client_timestamp = None
        if last_sync:
            try:
                client_timestamp = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        
        # Check for existing progress
        existing_progress = loop.run_until_complete(
            db.readingprogress.find_unique(
                where={
                    'user_id_chapter_id': {
                        'user_id': user_id,
                        'chapter_id': chapter_id,
                    }
                }
            )
        )
        
        # Detect conflicts if existing progress exists
        if existing_progress:
            server_data = {
                'offset': existing_progress.offset,
                'updated_at': existing_progress.updated_at,
            }
            client_data = {
                'offset': offset,
            }
            
            conflict = SyncConflictService.detect_conflict(
                resource_type='reading_progress',
                resource_id=f'{user_id}_{chapter_id}',
                client_data=client_data,
                server_data=server_data,
                client_timestamp=client_timestamp
            )
            
            if conflict:
                return {
                    'index': index,
                    'type': 'update_reading_progress',
                    'status': 'conflict',
                    'conflict': conflict
                }
        
        # No conflict, proceed with upsert
        progress = loop.run_until_complete(
            db.readingprogress.upsert(
                where={
                    'user_id_chapter_id': {
                        'user_id': user_id,
                        'chapter_id': chapter_id,
                    }
                },
                data={
                    'create': {
                        'user_id': user_id,
                        'chapter_id': chapter_id,
                        'offset': offset,
                    },
                    'update': {
                        'offset': offset,
                    }
                }
            )
        )
        
        return {
            'index': index,
            'type': 'update_reading_progress',
            'status': 'success',
            'data': {
                'id': progress.id,
                'chapter_id': progress.chapter_id,
                'offset': progress.offset,
            }
        }
    finally:
        loop.close()


def _process_bookmark_creation(
    db: Prisma,
    user_id: str,
    data: Dict[str, Any],
    index: int
) -> Dict[str, Any]:
    """Process a bookmark creation operation."""
    chapter_id = data.get('chapter_id')
    offset = data.get('offset')
    
    if not chapter_id or offset is None:
        return {
            'index': index,
            'type': 'create_bookmark',
            'status': 'error',
            'error': {
                'code': 'MISSING_FIELDS',
                'message': 'chapter_id and offset are required',
            }
        }
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Create bookmark
        bookmark = loop.run_until_complete(
            db.bookmark.create(
                data={
                    'user_id': user_id,
                    'chapter_id': chapter_id,
                    'offset': offset,
                }
            )
        )
        
        return {
            'index': index,
            'type': 'create_bookmark',
            'status': 'success',
            'data': {
                'id': bookmark.id,
                'chapter_id': bookmark.chapter_id,
                'offset': bookmark.offset,
                'created_at': bookmark.created_at.isoformat(),
            }
        }
    finally:
        loop.close()


def _process_whisper_creation(
    db: Prisma,
    user_id: str,
    user_profile: Any,
    data: Dict[str, Any],
    index: int
) -> Dict[str, Any]:
    """Process a whisper creation operation."""
    content = data.get('content')
    scope = data.get('scope', 'GLOBAL')
    story_id = data.get('story_id')
    highlight_id = data.get('highlight_id')
    parent_id = data.get('parent_id')
    
    if not content:
        return {
            'index': index,
            'type': 'create_whisper',
            'status': 'error',
            'error': {
                'code': 'MISSING_FIELDS',
                'message': 'content is required',
            }
        }
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Create whisper
        whisper = loop.run_until_complete(
            db.whisper.create(
                data={
                    'user_id': user_id,
                    'content': content,
                    'scope': scope,
                    'story_id': story_id,
                    'highlight_id': highlight_id,
                    'parent_id': parent_id,
                }
            )
        )
        
        return {
            'index': index,
            'type': 'create_whisper',
            'status': 'success',
            'data': {
                'id': whisper.id,
                'content': whisper.content,
                'scope': whisper.scope,
                'created_at': whisper.created_at.isoformat(),
            }
        }
    finally:
        loop.close()


@api_view(['GET'])
def sync_status(request):
    """
    Get synchronization status and verify data consistency.
    
    GET /v1/sync/status?resource_type=<type>&last_sync=<ISO8601_timestamp>
    
    Query parameters:
        - resource_type: Type of resource to check (optional: stories, whispers, all)
        - last_sync: Last successful sync timestamp (optional)
        
    Returns:
        - 200: Sync status information
        - 401: Not authenticated
        
    Validates: Requirement 10.5
    """
    # Check authentication
    user_id = getattr(request, 'clerk_user_id', None)
    if not user_id:
        return Response(
            {
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required',
                }
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    resource_type = request.GET.get('resource_type', 'all')
    last_sync_param = request.GET.get('last_sync')
    
    # Parse last_sync timestamp if provided
    last_sync = None
    if last_sync_param:
        try:
            last_sync = datetime.fromisoformat(last_sync_param.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return Response(
                {
                    'error': {
                        'code': 'INVALID_TIMESTAMP',
                        'message': 'Invalid last_sync timestamp format',
                        'details': {
                            'parameter': 'last_sync',
                            'provided': last_sync_param,
                            'expected_format': 'ISO 8601 (e.g., 2024-01-01T00:00:00Z)'
                        }
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Query database for sync status
    db = Prisma()
    try:
        db.connect()
        
        status_data = {
            'current_timestamp': datetime.now(timezone.utc).isoformat(),
            'last_sync': last_sync.isoformat() if last_sync else None,
        }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Get counts for different resource types
            if resource_type in ['stories', 'all']:
                where_clause = {'deleted_at': None}
                if last_sync:
                    where_clause['OR'] = [
                        {'updated_at': {'gte': last_sync}},
                        {'created_at': {'gte': last_sync}},
                    ]
                
                stories_count = loop.run_until_complete(
                    db.story.count(where=where_clause)
                )
                status_data['stories'] = {
                    'pending_updates': stories_count if last_sync else 0,
                    'total_count': loop.run_until_complete(
                        db.story.count(where={'deleted_at': None})
                    )
                }
            
            if resource_type in ['whispers', 'all']:
                where_clause = {'deleted_at': None}
                if last_sync:
                    where_clause['created_at'] = {'gte': last_sync}
                
                whispers_count = loop.run_until_complete(
                    db.whisper.count(where=where_clause)
                )
                status_data['whispers'] = {
                    'pending_updates': whispers_count if last_sync else 0,
                    'total_count': loop.run_until_complete(
                        db.whisper.count(where={'deleted_at': None})
                    )
                }
        finally:
            loop.close()
        
        return Response(status_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'error': {
                    'code': 'STATUS_ERROR',
                    'message': 'Failed to retrieve sync status',
                    'details': str(e)
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if db.is_connected():
            db.disconnect()


@api_view(['POST'])
def resolve_conflict(request):
    """
    Resolve a sync conflict with explicit resolution strategy.
    
    POST /v1/sync/resolve-conflict
    
    Request body:
        {
            "resource_type": "reading_progress" | "bookmark" | "whisper",
            "resource_id": "resource_identifier",
            "resolution": "client_wins" | "server_wins" | "merge",
            "data": { ... resource data ... },
            "last_sync": "ISO8601_timestamp"
        }
        
    Returns:
        - 200: Conflict resolved successfully
        - 400: Invalid request or resolution strategy
        - 401: Not authenticated
        - 404: Resource not found
        
    Validates: Requirement 10.4
    """
    # Check authentication
    user_id = getattr(request, 'clerk_user_id', None)
    if not user_id:
        return Response(
            {
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Authentication required',
                }
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Validate request body
    resource_type = request.data.get('resource_type')
    resource_id = request.data.get('resource_id')
    resolution = request.data.get('resolution')
    data = request.data.get('data', {})
    last_sync = request.data.get('last_sync')
    
    if not all([resource_type, resource_id, resolution]):
        return Response(
            {
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': 'resource_type, resource_id, and resolution are required',
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate resolution strategy
    valid_resolutions = ['client_wins', 'server_wins', 'merge']
    if resolution not in valid_resolutions:
        return Response(
            {
                'error': {
                    'code': 'INVALID_RESOLUTION',
                    'message': f'Invalid resolution strategy. Must be one of: {", ".join(valid_resolutions)}',
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Parse timestamp if provided
    client_timestamp = None
    if last_sync:
        try:
            client_timestamp = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return Response(
                {
                    'error': {
                        'code': 'INVALID_TIMESTAMP',
                        'message': 'Invalid last_sync timestamp format',
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Process resolution based on resource type
    db = Prisma()
    try:
        db.connect()
        
        if resource_type == 'reading_progress':
            result = _resolve_reading_progress_conflict(
                db, user_id, resource_id, resolution, data
            )
        else:
            return Response(
                {
                    'error': {
                        'code': 'UNSUPPORTED_RESOURCE_TYPE',
                        'message': f'Conflict resolution not yet supported for resource type: {resource_type}',
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'error': {
                    'code': 'RESOLUTION_ERROR',
                    'message': 'Failed to resolve conflict',
                    'details': str(e)
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if db.is_connected():
            db.disconnect()


def _resolve_reading_progress_conflict(
    db: Prisma,
    user_id: str,
    resource_id: str,
    resolution: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """Resolve a reading progress conflict."""
    # Parse resource_id (format: user_id_chapter_id)
    parts = resource_id.split('_', 1)
    if len(parts) != 2:
        raise ValueError('Invalid resource_id format for reading_progress')
    
    _, chapter_id = parts
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Get current server data
        existing_progress = loop.run_until_complete(
            db.readingprogress.find_unique(
                where={
                    'user_id_chapter_id': {
                        'user_id': user_id,
                        'chapter_id': chapter_id,
                    }
                }
            )
        )
        
        if not existing_progress:
            raise ValueError('Reading progress not found')
        
        # Apply resolution strategy
        if resolution == 'server_wins':
            # Return current server data without changes
            return {
                'resolved': True,
                'strategy': 'server_wins',
                'data': {
                    'id': existing_progress.id,
                    'chapter_id': existing_progress.chapter_id,
                    'offset': existing_progress.offset,
                    'updated_at': existing_progress.updated_at.isoformat(),
                }
            }
        elif resolution == 'client_wins':
            # Update with client data
            offset = data.get('offset')
            if offset is None:
                raise ValueError('offset is required for client_wins resolution')
            
            updated_progress = loop.run_until_complete(
                db.readingprogress.update(
                    where={
                        'user_id_chapter_id': {
                            'user_id': user_id,
                            'chapter_id': chapter_id,
                        }
                    },
                    data={'offset': offset}
                )
            )
            
            return {
                'resolved': True,
                'strategy': 'client_wins',
                'data': {
                    'id': updated_progress.id,
                    'chapter_id': updated_progress.chapter_id,
                    'offset': updated_progress.offset,
                    'updated_at': updated_progress.updated_at.isoformat(),
                }
            }
        elif resolution == 'merge':
            # For reading progress, merge means taking the maximum offset
            client_offset = data.get('offset', 0)
            server_offset = existing_progress.offset
            merged_offset = max(client_offset, server_offset)
            
            updated_progress = loop.run_until_complete(
                db.readingprogress.update(
                    where={
                        'user_id_chapter_id': {
                            'user_id': user_id,
                            'chapter_id': chapter_id,
                        }
                    },
                    data={'offset': merged_offset}
                )
            )
            
            return {
                'resolved': True,
                'strategy': 'merge',
                'data': {
                    'id': updated_progress.id,
                    'chapter_id': updated_progress.chapter_id,
                    'offset': updated_progress.offset,
                    'updated_at': updated_progress.updated_at.isoformat(),
                },
                'merge_details': {
                    'client_offset': client_offset,
                    'server_offset': server_offset,
                    'merged_offset': merged_offset,
                }
            }
    finally:
        loop.close()
