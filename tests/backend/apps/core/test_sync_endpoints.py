"""
Unit tests for data synchronization endpoints.

Tests the sync endpoints for stories, whispers, batch operations, and status.
"""

import pytest
from datetime import datetime, timedelta, timezone
from django.test import RequestFactory
from unittest.mock import Mock, patch, MagicMock
from apps.core.sync_views import (
    sync_stories,
    sync_whispers,
    sync_batch,
    sync_status,
    resolve_conflict
)


@pytest.fixture
def request_factory():
    """Create a request factory for testing."""
    return RequestFactory()


@pytest.fixture
def authenticated_request(request_factory):
    """Create an authenticated request."""
    request = request_factory.get('/v1/sync/stories')
    request.clerk_user_id = 'test_user_123'
    request.user_profile = Mock(id='test_user_123', username='testuser')
    return request


@pytest.fixture
def mock_db():
    """Create a mock Prisma database."""
    with patch('apps.core.sync_views.Prisma') as mock_prisma:
        db_instance = MagicMock()
        mock_prisma.return_value = db_instance
        db_instance.is_connected.return_value = True
        yield db_instance


class TestSyncStories:
    """Test sync_stories endpoint."""
    
    def test_sync_stories_requires_authentication(self, request_factory):
        """Test that sync_stories requires authentication."""
        request = request_factory.get('/v1/sync/stories?since=2024-01-01T00:00:00Z')
        
        response = sync_stories(request)
        
        assert response.status_code == 401
        assert response.data['error']['code'] == 'UNAUTHORIZED'
    
    def test_sync_stories_requires_since_parameter(self, authenticated_request):
        """Test that sync_stories requires 'since' parameter."""
        response = sync_stories(authenticated_request)
        
        assert response.status_code == 400
        assert response.data['error']['code'] == 'MISSING_PARAMETER'
    
    def test_sync_stories_validates_timestamp_format(self, request_factory):
        """Test that sync_stories validates timestamp format."""
        request = request_factory.get('/v1/sync/stories?since=invalid-timestamp')
        request.clerk_user_id = 'test_user_123'
        
        response = sync_stories(request)
        
        assert response.status_code == 400
        assert response.data['error']['code'] == 'INVALID_TIMESTAMP'
    
    def test_sync_stories_returns_modified_stories(
        self, request_factory, mock_db
    ):
        """Test that sync_stories returns stories modified since timestamp."""
        # Create request with valid timestamp
        since_time = datetime.now(timezone.utc) - timedelta(days=1)
        request = request_factory.get(
            f'/v1/sync/stories?since={since_time.isoformat()}Z'
        )
        request.clerk_user_id = 'test_user_123'
        
        # Mock story data
        mock_story = Mock(
            id='story_123',
            slug='test-story',
            title='Test Story',
            blurb='Test blurb',
            cover_key='cover.jpg',
            author_id='author_123',
            published=True,
            published_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tags=[],
            author=Mock(
                id='author_123',
                username='author',
                display_name='Author',
                avatar_key='avatar.jpg'
            )
        )
        
        # Mock database response
        async def mock_find_many(*args, **kwargs):
            return [mock_story]
        
        mock_db.story.find_many = mock_find_many
        
        response = sync_stories(request)
        
        assert response.status_code == 200
        assert 'stories' in response.data
        assert 'sync_metadata' in response.data


class TestSyncWhispers:
    """Test sync_whispers endpoint."""
    
    def test_sync_whispers_requires_authentication(self, request_factory):
        """Test that sync_whispers requires authentication."""
        request = request_factory.get('/v1/sync/whispers?since=2024-01-01T00:00:00Z')
        
        response = sync_whispers(request)
        
        assert response.status_code == 401
        assert response.data['error']['code'] == 'UNAUTHORIZED'
    
    def test_sync_whispers_requires_since_parameter(self, authenticated_request):
        """Test that sync_whispers requires 'since' parameter."""
        response = sync_whispers(authenticated_request)
        
        assert response.status_code == 400
        assert response.data['error']['code'] == 'MISSING_PARAMETER'
    
    def test_sync_whispers_validates_timestamp_format(self, request_factory):
        """Test that sync_whispers validates timestamp format."""
        request = request_factory.get('/v1/sync/whispers?since=invalid-timestamp')
        request.clerk_user_id = 'test_user_123'
        
        response = sync_whispers(request)
        
        assert response.status_code == 400
        assert response.data['error']['code'] == 'INVALID_TIMESTAMP'


class TestSyncBatch:
    """Test sync_batch endpoint."""
    
    def test_sync_batch_requires_authentication(self, request_factory):
        """Test that sync_batch requires authentication."""
        request = request_factory.post(
            '/v1/sync/batch',
            data={'operations': []},
            content_type='application/json'
        )
        
        response = sync_batch(request)
        
        assert response.status_code == 401
        assert response.data['error']['code'] == 'UNAUTHORIZED'
    
    def test_sync_batch_requires_operations_array(self, request_factory):
        """Test that sync_batch requires operations array."""
        request = request_factory.post(
            '/v1/sync/batch',
            data={},
            content_type='application/json'
        )
        request.clerk_user_id = 'test_user_123'
        request.user_profile = Mock(id='test_user_123')
        
        response = sync_batch(request)
        
        assert response.status_code == 400
        # When operations key is missing, it defaults to empty list, so we get EMPTY_BATCH
        assert response.data['error']['code'] == 'EMPTY_BATCH'
    
    def test_sync_batch_rejects_empty_operations(self, request_factory):
        """Test that sync_batch rejects empty operations array."""
        request = request_factory.post(
            '/v1/sync/batch',
            data={'operations': []},
            content_type='application/json'
        )
        request.clerk_user_id = 'test_user_123'
        request.user_profile = Mock(id='test_user_123')
        
        response = sync_batch(request)
        
        assert response.status_code == 400
        assert response.data['error']['code'] == 'EMPTY_BATCH'
    
    def test_sync_batch_limits_operations_count(self, request_factory):
        """Test that sync_batch limits operations to 100."""
        operations = [{'type': 'test', 'data': {}} for _ in range(101)]
        request = request_factory.post(
            '/v1/sync/batch',
            data={'operations': operations},
            content_type='application/json'
        )
        request.clerk_user_id = 'test_user_123'
        request.user_profile = Mock(id='test_user_123')
        
        response = sync_batch(request)
        
        assert response.status_code == 400
        assert response.data['error']['code'] == 'BATCH_TOO_LARGE'


class TestSyncStatus:
    """Test sync_status endpoint."""
    
    def test_sync_status_requires_authentication(self, request_factory):
        """Test that sync_status requires authentication."""
        request = request_factory.get('/v1/sync/status')
        
        response = sync_status(request)
        
        assert response.status_code == 401
        assert response.data['error']['code'] == 'UNAUTHORIZED'
    
    def test_sync_status_validates_timestamp_format(self, request_factory):
        """Test that sync_status validates last_sync timestamp format."""
        request = request_factory.get('/v1/sync/status?last_sync=invalid-timestamp')
        request.clerk_user_id = 'test_user_123'
        
        response = sync_status(request)
        
        assert response.status_code == 400
        assert response.data['error']['code'] == 'INVALID_TIMESTAMP'
    
    def test_sync_status_returns_current_timestamp(
        self, request_factory, mock_db
    ):
        """Test that sync_status returns current timestamp."""
        request = request_factory.get('/v1/sync/status')
        request.clerk_user_id = 'test_user_123'
        
        # Mock database count methods
        async def mock_count(*args, **kwargs):
            return 0
        
        mock_db.story.count = mock_count
        mock_db.whisper.count = mock_count
        
        response = sync_status(request)
        
        assert response.status_code == 200
        assert 'current_timestamp' in response.data


class TestSyncEndpointsIntegration:
    """Integration tests for sync endpoints."""
    
    def test_sync_endpoints_handle_database_errors_gracefully(
        self, request_factory
    ):
        """Test that sync endpoints handle database errors gracefully."""
        request = request_factory.get(
            '/v1/sync/stories?since=2024-01-01T00:00:00Z'
        )
        request.clerk_user_id = 'test_user_123'
        
        with patch('apps.core.sync_views.Prisma') as mock_prisma:
            # Simulate database connection error
            mock_prisma.return_value.connect.side_effect = Exception('DB Error')
            
            response = sync_stories(request)
            
            assert response.status_code == 500
            assert response.data['error']['code'] == 'SYNC_ERROR'



class TestSyncBatchConflictDetection:
    """Test conflict detection in batch operations."""
    
    def test_batch_detects_reading_progress_conflict(self, request_factory):
        """Test that batch operations detect conflicts in reading progress updates."""
        # Create request with conflicting data
        now = datetime.now(timezone.utc)
        operations = [
            {
                'type': 'update_reading_progress',
                'data': {
                    'chapter_id': 'chapter_123',
                    'offset': 100,
                    'last_sync': (now - timedelta(hours=2)).isoformat()
                }
            }
        ]
        
        request = request_factory.post(
            '/v1/sync/batch',
            data={'operations': operations},
            content_type='application/json'
        )
        request.clerk_user_id = 'test_user_123'
        request.user_profile = Mock(id='test_user_123')
        
        with patch('apps.core.sync_views.Prisma') as mock_prisma:
            db_instance = MagicMock()
            mock_prisma.return_value = db_instance
            db_instance.is_connected.return_value = True
            
            # Mock existing progress with newer timestamp
            mock_progress = Mock(
                id='progress_123',
                user_id='test_user_123',
                chapter_id='chapter_123',
                offset=150,
                updated_at=now - timedelta(hours=1)
            )
            
            async def mock_find_unique(*args, **kwargs):
                return mock_progress
            
            db_instance.readingprogress.find_unique = mock_find_unique
            
            response = sync_batch(request)
            
            # Should return 409 Conflict
            assert response.status_code == 409
            assert response.data['summary']['conflict'] == 1
            assert response.data['results'][0]['status'] == 'conflict'
    
    def test_batch_proceeds_without_conflict_when_no_existing_data(
        self, request_factory
    ):
        """Test that batch operations proceed when no existing data exists."""
        now = datetime.now(timezone.utc)
        operations = [
            {
                'type': 'update_reading_progress',
                'data': {
                    'chapter_id': 'chapter_123',
                    'offset': 100,
                    'last_sync': now.isoformat()
                }
            }
        ]
        
        request = request_factory.post(
            '/v1/sync/batch',
            data={'operations': operations},
            content_type='application/json'
        )
        request.clerk_user_id = 'test_user_123'
        request.user_profile = Mock(id='test_user_123')
        
        with patch('apps.core.sync_views.Prisma') as mock_prisma:
            db_instance = MagicMock()
            mock_prisma.return_value = db_instance
            db_instance.is_connected.return_value = True
            
            # Mock no existing progress
            async def mock_find_unique(*args, **kwargs):
                return None
            
            mock_progress = Mock(
                id='progress_123',
                chapter_id='chapter_123',
                offset=100
            )
            
            async def mock_upsert(*args, **kwargs):
                return mock_progress
            
            db_instance.readingprogress.find_unique = mock_find_unique
            db_instance.readingprogress.upsert = mock_upsert
            
            response = sync_batch(request)
            
            # Should succeed without conflict
            assert response.status_code == 200
            assert response.data['summary']['success'] == 1
            assert response.data['summary']['conflict'] == 0


class TestResolveConflict:
    """Test conflict resolution endpoint."""
    
    def test_resolve_conflict_requires_authentication(self, request_factory):
        """Test that resolve_conflict requires authentication."""
        request = request_factory.post(
            '/v1/sync/resolve-conflict',
            data={},
            content_type='application/json'
        )
        
        response = resolve_conflict(request)
        
        assert response.status_code == 401
        assert response.data['error']['code'] == 'UNAUTHORIZED'
    
    def test_resolve_conflict_requires_fields(self, request_factory):
        """Test that resolve_conflict requires required fields."""
        request = request_factory.post(
            '/v1/sync/resolve-conflict',
            data={},
            content_type='application/json'
        )
        request.clerk_user_id = 'test_user_123'
        
        response = resolve_conflict(request)
        
        assert response.status_code == 400
        assert response.data['error']['code'] == 'MISSING_FIELDS'
    
    def test_resolve_conflict_validates_resolution_strategy(self, request_factory):
        """Test that resolve_conflict validates resolution strategy."""
        request = request_factory.post(
            '/v1/sync/resolve-conflict',
            data={
                'resource_type': 'reading_progress',
                'resource_id': 'user_123_chapter_123',
                'resolution': 'invalid_strategy',
                'data': {}
            },
            content_type='application/json'
        )
        request.clerk_user_id = 'test_user_123'
        
        response = resolve_conflict(request)
        
        assert response.status_code == 400
        assert response.data['error']['code'] == 'INVALID_RESOLUTION'
    
    def test_resolve_conflict_server_wins(self, request_factory):
        """Test conflict resolution with server_wins strategy."""
        request = request_factory.post(
            '/v1/sync/resolve-conflict',
            data={
                'resource_type': 'reading_progress',
                'resource_id': 'test_user_123_chapter_123',
                'resolution': 'server_wins',
                'data': {'offset': 100}
            },
            content_type='application/json'
        )
        request.clerk_user_id = 'test_user_123'
        
        with patch('apps.core.sync_views.Prisma') as mock_prisma:
            db_instance = MagicMock()
            mock_prisma.return_value = db_instance
            db_instance.is_connected.return_value = True
            
            # Mock existing progress
            mock_progress = Mock(
                id='progress_123',
                chapter_id='chapter_123',
                offset=150,
                updated_at=datetime.now(timezone.utc)
            )
            
            async def mock_find_unique(*args, **kwargs):
                return mock_progress
            
            db_instance.readingprogress.find_unique = mock_find_unique
            
            response = resolve_conflict(request)
            
            assert response.status_code == 200
            assert response.data['resolved'] is True
            assert response.data['strategy'] == 'server_wins'
            assert response.data['data']['offset'] == 150  # Server value
    
    def test_resolve_conflict_client_wins(self, request_factory):
        """Test conflict resolution with client_wins strategy."""
        request = request_factory.post(
            '/v1/sync/resolve-conflict',
            data={
                'resource_type': 'reading_progress',
                'resource_id': 'test_user_123_chapter_123',
                'resolution': 'client_wins',
                'data': {'offset': 200}
            },
            content_type='application/json'
        )
        request.clerk_user_id = 'test_user_123'
        
        with patch('apps.core.sync_views.Prisma') as mock_prisma:
            db_instance = MagicMock()
            mock_prisma.return_value = db_instance
            db_instance.is_connected.return_value = True
            
            # Mock existing and updated progress
            mock_existing = Mock(
                id='progress_123',
                chapter_id='chapter_123',
                offset=150,
                updated_at=datetime.now(timezone.utc)
            )
            
            mock_updated = Mock(
                id='progress_123',
                chapter_id='chapter_123',
                offset=200,
                updated_at=datetime.now(timezone.utc)
            )
            
            async def mock_find_unique(*args, **kwargs):
                return mock_existing
            
            async def mock_update(*args, **kwargs):
                return mock_updated
            
            db_instance.readingprogress.find_unique = mock_find_unique
            db_instance.readingprogress.update = mock_update
            
            response = resolve_conflict(request)
            
            assert response.status_code == 200
            assert response.data['resolved'] is True
            assert response.data['strategy'] == 'client_wins'
            assert response.data['data']['offset'] == 200  # Client value
    
    def test_resolve_conflict_merge(self, request_factory):
        """Test conflict resolution with merge strategy."""
        request = request_factory.post(
            '/v1/sync/resolve-conflict',
            data={
                'resource_type': 'reading_progress',
                'resource_id': 'test_user_123_chapter_123',
                'resolution': 'merge',
                'data': {'offset': 100}
            },
            content_type='application/json'
        )
        request.clerk_user_id = 'test_user_123'
        
        with patch('apps.core.sync_views.Prisma') as mock_prisma:
            db_instance = MagicMock()
            mock_prisma.return_value = db_instance
            db_instance.is_connected.return_value = True
            
            # Mock existing progress with higher offset
            mock_existing = Mock(
                id='progress_123',
                chapter_id='chapter_123',
                offset=150,
                updated_at=datetime.now(timezone.utc)
            )
            
            mock_merged = Mock(
                id='progress_123',
                chapter_id='chapter_123',
                offset=150,  # Max of 100 and 150
                updated_at=datetime.now(timezone.utc)
            )
            
            async def mock_find_unique(*args, **kwargs):
                return mock_existing
            
            async def mock_update(*args, **kwargs):
                return mock_merged
            
            db_instance.readingprogress.find_unique = mock_find_unique
            db_instance.readingprogress.update = mock_update
            
            response = resolve_conflict(request)
            
            assert response.status_code == 200
            assert response.data['resolved'] is True
            assert response.data['strategy'] == 'merge'
            assert response.data['data']['offset'] == 150  # Max value
            assert 'merge_details' in response.data
