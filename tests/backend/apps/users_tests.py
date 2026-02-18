"""Tests for user authentication middleware."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from django.test import RequestFactory
from apps.users.middleware import ClerkAuthMiddleware
from apps.users.utils import get_or_create_profile


@pytest.mark.django_db
class TestClerkAuthMiddleware:
    """Test cases for ClerkAuthMiddleware."""
    
    def test_middleware_without_auth_header(self):
        """Test middleware with no Authorization header."""
        factory = RequestFactory()
        request = factory.get('/')
        
        get_response = Mock(return_value=Mock())
        middleware = ClerkAuthMiddleware(get_response)
        
        response = middleware(request)
        
        assert request.clerk_user_id is None
        assert request.user_profile is None
        assert get_response.called
    
    def test_middleware_with_invalid_auth_header(self):
        """Test middleware with invalid Authorization header."""
        factory = RequestFactory()
        request = factory.get('/', HTTP_AUTHORIZATION='InvalidToken')
        
        get_response = Mock(return_value=Mock())
        middleware = ClerkAuthMiddleware(get_response)
        
        response = middleware(request)
        
        assert request.clerk_user_id is None
        assert request.user_profile is None
    
    @patch('apps.users.middleware.jwt.decode')
    @patch('apps.users.middleware.get_or_create_profile')
    def test_middleware_with_valid_token(self, mock_get_profile, mock_jwt_decode):
        """Test middleware with valid JWT token."""
        factory = RequestFactory()
        request = factory.get('/', HTTP_AUTHORIZATION='Bearer valid_token')
        
        # Mock JWT decode
        mock_jwt_decode.return_value = {'sub': 'user_123'}
        
        # Mock profile creation
        mock_profile = Mock()
        mock_profile.clerk_user_id = 'user_123'
        mock_profile.handle = 'user_user_123'
        
        # Create async mock
        async def async_get_profile(clerk_user_id):
            return mock_profile
        
        mock_get_profile.return_value = async_get_profile('user_123')
        
        get_response = Mock(return_value=Mock())
        middleware = ClerkAuthMiddleware(get_response)
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_until_complete.return_value = mock_profile
            response = middleware(request)
        
        assert request.clerk_user_id == 'user_123'
        assert request.user_profile == mock_profile


@pytest.mark.asyncio
@pytest.mark.django_db
class TestGetOrCreateProfile:
    """Test cases for get_or_create_profile utility function."""
    
    async def test_get_existing_profile(self):
        """Test retrieving an existing profile."""
        from prisma import Prisma
        
        db = Prisma()
        await db.connect()
        
        # Create a test profile
        test_profile = await db.userprofile.create(
            data={
                'clerk_user_id': 'test_clerk_123',
                'handle': 'test_user',
                'display_name': 'Test User',
            }
        )
        
        # Test retrieval
        profile = await get_or_create_profile('test_clerk_123')
        
        assert profile is not None
        assert profile.clerk_user_id == 'test_clerk_123'
        assert profile.handle == 'test_user'
        
        # Cleanup
        await db.userprofile.delete(where={'id': test_profile.id})
        await db.disconnect()
    
    async def test_create_new_profile(self):
        """Test creating a new profile."""
        from prisma import Prisma
        
        clerk_user_id = 'new_clerk_456'
        
        # Test creation
        profile = await get_or_create_profile(clerk_user_id)
        
        assert profile is not None
        assert profile.clerk_user_id == clerk_user_id
        assert profile.handle.startswith('user_')
        assert profile.display_name is not None
        
        # Cleanup
        db = Prisma()
        await db.connect()
        await db.userprofile.delete(where={'id': profile.id})
        await db.disconnect()
    
    async def test_handle_uniqueness(self):
        """Test that handles are unique when creating multiple profiles."""
        from prisma import Prisma
        
        db = Prisma()
        await db.connect()
        
        # Create first profile with a specific clerk_user_id
        clerk_id_1 = 'unique_test_789'
        profile1 = await get_or_create_profile(clerk_id_1)
        
        # Create second profile with different clerk_user_id but similar pattern
        clerk_id_2 = 'unique_test_790'
        profile2 = await get_or_create_profile(clerk_id_2)
        
        assert profile1.handle != profile2.handle
        
        # Cleanup
        await db.userprofile.delete(where={'id': profile1.id})
        await db.userprofile.delete(where={'id': profile2.id})
        await db.disconnect()



@pytest.mark.asyncio
@pytest.mark.django_db
class TestUserProfileEndpoints:
    """Test cases for user profile API endpoints."""
    
    async def cleanup_test_profiles(self):
        """Helper to clean up test profiles."""
        from prisma import Prisma
        db = Prisma()
        await db.connect()
        # Delete all test profiles
        await db.userprofile.delete_many(
            where={'clerk_user_id': {'startswith': 'test_'}}
        )
        await db.disconnect()
    
    async def test_get_me_authenticated(self):
        """Test GET /v1/users/me with authenticated user."""
        from django.test import Client
        from prisma import Prisma
        import jwt
        import uuid
        
        await self.cleanup_test_profiles()
        
        # Use unique clerk_user_id
        clerk_id = f"test_me_{uuid.uuid4().hex[:8]}"
        
        db = Prisma()
        await db.connect()
        
        # Create test profile
        test_profile = await db.userprofile.create(
            data={
                'clerk_user_id': clerk_id,
                'handle': f'test_me_user_{uuid.uuid4().hex[:6]}',
                'display_name': 'Test Me User',
                'bio': 'Test bio',
            }
        )
        
        # Create JWT token
        token = jwt.encode({'sub': clerk_id}, 'secret', algorithm='HS256')
        
        # Make request
        client = Client()
        response = client.get(
            '/v1/users/me/',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['display_name'] == 'Test Me User'
        assert data['bio'] == 'Test bio'
        assert 'clerk_user_id' in data
        
        # Cleanup
        await db.userprofile.delete(where={'id': test_profile.id})
        await db.disconnect()
    
    async def test_get_me_unauthenticated(self):
        """Test GET /v1/users/me without authentication."""
        from django.test import Client
        
        client = Client()
        response = client.get('/v1/users/me/')
        
        assert response.status_code == 401
        data = response.json()
        assert 'error' in data
    
    async def test_update_me_valid_data(self):
        """Test PUT /v1/users/me with valid data."""
        from django.test import Client
        from prisma import Prisma
        import jwt
        import uuid
        
        await self.cleanup_test_profiles()
        
        clerk_id = f"test_update_{uuid.uuid4().hex[:8]}"
        
        db = Prisma()
        await db.connect()
        
        # Create test profile
        test_profile = await db.userprofile.create(
            data={
                'clerk_user_id': clerk_id,
                'handle': f'test_update_user_{uuid.uuid4().hex[:6]}',
                'display_name': 'Test Update User',
            }
        )
        
        # Create JWT token
        token = jwt.encode({'sub': clerk_id}, 'secret', algorithm='HS256')
        
        # Make update request
        client = Client()
        response = client.put(
            '/v1/users/me/',
            data={
                'display_name': 'Updated Name',
                'bio': 'Updated bio',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['display_name'] == 'Updated Name'
        assert data['bio'] == 'Updated bio'
        
        # Cleanup
        await db.userprofile.delete(where={'id': test_profile.id})
        await db.disconnect()
    
    async def test_update_me_invalid_handle(self):
        """Test PUT /v1/users/me with invalid handle format."""
        from django.test import Client
        from prisma import Prisma
        import jwt
        import uuid
        
        await self.cleanup_test_profiles()
        
        clerk_id = f"test_invalid_{uuid.uuid4().hex[:8]}"
        
        db = Prisma()
        await db.connect()
        
        # Create test profile
        test_profile = await db.userprofile.create(
            data={
                'clerk_user_id': clerk_id,
                'handle': f'test_invalid_user_{uuid.uuid4().hex[:6]}',
                'display_name': 'Test Invalid User',
            }
        )
        
        # Create JWT token
        token = jwt.encode({'sub': clerk_id}, 'secret', algorithm='HS256')
        
        # Make update request with invalid handle
        client = Client()
        response = client.put(
            '/v1/users/me/',
            data={
                'handle': 'ab',  # Too short
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        
        # Cleanup
        await db.userprofile.delete(where={'id': test_profile.id})
        await db.disconnect()
    
    async def test_update_me_duplicate_handle(self):
        """Test PUT /v1/users/me with handle already taken by another user."""
        from django.test import Client
        from prisma import Prisma
        import jwt
        import uuid
        
        await self.cleanup_test_profiles()
        
        db = Prisma()
        await db.connect()
        
        unique_suffix = uuid.uuid4().hex[:6]
        
        # Create two test profiles
        profile1 = await db.userprofile.create(
            data={
                'clerk_user_id': f'test_dup1_{unique_suffix}',
                'handle': f'existing_handle_{unique_suffix}',
                'display_name': 'User 1',
            }
        )
        
        profile2 = await db.userprofile.create(
            data={
                'clerk_user_id': f'test_dup2_{unique_suffix}',
                'handle': f'another_handle_{unique_suffix}',
                'display_name': 'User 2',
            }
        )
        
        # Create JWT token for profile2
        token = jwt.encode({'sub': f'test_dup2_{unique_suffix}'}, 'secret', algorithm='HS256')
        
        # Try to update profile2 with profile1's handle
        client = Client()
        response = client.put(
            '/v1/users/me/',
            data={
                'handle': f'existing_handle_{unique_suffix}',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 409
        data = response.json()
        assert 'error' in data
        assert 'DUPLICATE_HANDLE' in data['error']['code']
        
        # Cleanup
        await db.userprofile.delete(where={'id': profile1.id})
        await db.userprofile.delete(where={'id': profile2.id})
        await db.disconnect()
    
    async def test_get_user_by_handle(self):
        """Test GET /v1/users/{handle} endpoint."""
        from django.test import Client
        from prisma import Prisma
        import uuid
        
        await self.cleanup_test_profiles()
        
        db = Prisma()
        await db.connect()
        
        unique_handle = f'public_user_{uuid.uuid4().hex[:6]}'
        
        # Create test profile
        test_profile = await db.userprofile.create(
            data={
                'clerk_user_id': f'test_public_{uuid.uuid4().hex[:8]}',
                'handle': unique_handle,
                'display_name': 'Public User',
                'bio': 'Public bio',
            }
        )
        
        # Make request
        client = Client()
        response = client.get(f'/v1/users/{unique_handle}/')
        
        assert response.status_code == 200
        data = response.json()
        assert data['handle'] == unique_handle
        assert data['display_name'] == 'Public User'
        assert data['bio'] == 'Public bio'
        assert 'clerk_user_id' not in data  # Should not expose clerk_user_id in public profile
        
        # Cleanup
        await db.userprofile.delete(where={'id': test_profile.id})
        await db.disconnect()
    
    async def test_get_user_by_handle_not_found(self):
        """Test GET /v1/users/{handle} with non-existent handle."""
        from django.test import Client
        
        client = Client()
        response = client.get('/v1/users/nonexistent_user/')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
    
    async def test_handle_format_validation(self):
        """Test handle format validation with various invalid formats."""
        from django.test import Client
        from prisma import Prisma
        import jwt
        import uuid
        
        await self.cleanup_test_profiles()
        
        clerk_id = f"test_format_{uuid.uuid4().hex[:8]}"
        
        db = Prisma()
        await db.connect()
        
        # Create test profile
        test_profile = await db.userprofile.create(
            data={
                'clerk_user_id': clerk_id,
                'handle': f'test_format_user_{uuid.uuid4().hex[:6]}',
                'display_name': 'Test Format User',
            }
        )
        
        # Create JWT token
        token = jwt.encode({'sub': clerk_id}, 'secret', algorithm='HS256')
        
        client = Client()
        
        # Test various invalid handles
        invalid_handles = [
            'ab',  # Too short
            'a' * 31,  # Too long
            'user-name',  # Contains hyphen
            'user.name',  # Contains dot
            'user name',  # Contains space
            'user@name',  # Contains special char
        ]
        
        for invalid_handle in invalid_handles:
            response = client.put(
                '/v1/users/me/',
                data={'handle': invalid_handle},
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {token}'
            )
            assert response.status_code == 400, f"Handle '{invalid_handle}' should be rejected"
        
        # Test valid handles
        valid_handles = [
            'abc',  # Minimum length
            'a' * 30,  # Maximum length
            'user_name',  # With underscore
            'user123',  # With numbers
            'User_Name_123',  # Mixed case with underscore and numbers
        ]
        
        for valid_handle in valid_handles:
            response = client.put(
                '/v1/users/me/',
                data={'handle': valid_handle},
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer {token}'
            )
            assert response.status_code == 200, f"Handle '{valid_handle}' should be accepted"
        
        # Cleanup
        await db.userprofile.delete(where={'id': test_profile.id})
        await db.disconnect()
