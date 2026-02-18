"""
Tests for RateLimitMiddleware admin bypass functionality.

This test verifies that users with ModeratorRole bypass rate limiting.
"""

import pytest
from django.test import RequestFactory
from django.http import JsonResponse
from infrastructure.rate_limit_middleware import RateLimitMiddleware
from unittest.mock import Mock, patch


class TestRateLimitMiddlewareAdminBypass:
    """Test admin bypass logic in RateLimitMiddleware"""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance"""
        get_response = Mock(return_value=JsonResponse({'status': 'ok'}))
        return RateLimitMiddleware(get_response)
    
    @pytest.fixture
    def request_factory(self):
        """Create request factory"""
        return RequestFactory()
    
    def test_is_admin_user_with_active_moderator_role(self, middleware, request_factory):
        """Test that user with active ModeratorRole is identified as admin"""
        request = request_factory.get('/api/test')
        
        # Mock user profile
        user_profile = Mock()
        user_profile.id = 'test-user-123'
        request.user_profile = user_profile
        
        # Mock database query to return 1 (user has active moderator role)
        with patch('django.db.connection.cursor') as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = [1]
            
            result = middleware._is_admin_user(request)
            
            assert result is True
    
    def test_is_admin_user_without_moderator_role(self, middleware, request_factory):
        """Test that user without ModeratorRole is not identified as admin"""
        request = request_factory.get('/api/test')
        
        # Mock user profile
        user_profile = Mock()
        user_profile.id = 'test-user-456'
        request.user_profile = user_profile
        
        # Mock database query to return 0 (user has no moderator role)
        with patch('django.db.connection.cursor') as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = [0]
            
            result = middleware._is_admin_user(request)
            
            assert result is False
    
    def test_is_admin_user_with_inactive_moderator_role(self, middleware, request_factory):
        """Test that user with inactive ModeratorRole is not identified as admin"""
        request = request_factory.get('/api/test')
        
        # Mock user profile
        user_profile = Mock()
        user_profile.id = 'test-user-789'
        request.user_profile = user_profile
        
        # Mock database query to return 0 (user has inactive moderator role)
        with patch('django.db.connection.cursor') as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.fetchone.return_value = [0]
            
            result = middleware._is_admin_user(request)
            
            assert result is False
    
    def test_is_admin_user_without_user_profile(self, middleware, request_factory):
        """Test that request without user_profile is not identified as admin"""
        request = request_factory.get('/api/test')
        # No user_profile attribute
        
        result = middleware._is_admin_user(request)
        
        assert result is False
    
    def test_is_admin_user_with_none_user_profile(self, middleware, request_factory):
        """Test that request with None user_profile is not identified as admin"""
        request = request_factory.get('/api/test')
        request.user_profile = None
        
        result = middleware._is_admin_user(request)
        
        assert result is False
    
    def test_is_admin_user_handles_database_error(self, middleware, request_factory):
        """Test that database errors are handled gracefully"""
        request = request_factory.get('/api/test')
        
        # Mock user profile
        user_profile = Mock()
        user_profile.id = 'test-user-error'
        request.user_profile = user_profile
        
        # Mock database query to raise exception
        with patch('django.db.connection.cursor') as mock_cursor:
            mock_cursor.return_value.__enter__.return_value.execute.side_effect = Exception("DB error")
            
            result = middleware._is_admin_user(request)
            
            # Should return False on error (fail closed)
            assert result is False
    
    def test_admin_bypass_in_allow_request(self, middleware, request_factory):
        """Test that admin users bypass rate limiting in allow_request call"""
        request = request_factory.get('/api/test')
        
        # Mock user profile
        user_profile = Mock()
        user_profile.id = 'admin-user-123'
        request.user_profile = user_profile
        
        # Mock admin check to return True
        with patch.object(middleware, '_is_admin_user', return_value=True):
            # Mock rate limiter to verify is_admin is passed correctly
            with patch.object(middleware.rate_limiter, 'allow_request', return_value=True) as mock_allow:
                middleware(request)
                
                # Verify allow_request was called with is_admin=True
                mock_allow.assert_called_once()
                call_args = mock_allow.call_args
                assert call_args[0][1] is True  # Second argument should be is_admin=True
    
    def test_non_admin_no_bypass_in_allow_request(self, middleware, request_factory):
        """Test that non-admin users don't bypass rate limiting"""
        request = request_factory.get('/api/test')
        
        # Mock user profile
        user_profile = Mock()
        user_profile.id = 'regular-user-123'
        request.user_profile = user_profile
        
        # Mock admin check to return False
        with patch.object(middleware, '_is_admin_user', return_value=False):
            # Mock rate limiter to verify is_admin is passed correctly
            with patch.object(middleware.rate_limiter, 'allow_request', return_value=True) as mock_allow:
                middleware(request)
                
                # Verify allow_request was called with is_admin=False
                mock_allow.assert_called_once()
                call_args = mock_allow.call_args
                assert call_args[0][1] is False  # Second argument should be is_admin=False
