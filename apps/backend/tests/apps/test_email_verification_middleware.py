"""
Unit tests for email verification middleware.

Tests that the middleware correctly blocks content creation for unverified users
and allows it for verified users.

Requirements: 5.3
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from rest_framework import status
from apps.users.email_verification.middleware import EmailVerificationMiddleware


class TestEmailVerificationMiddleware:
    """Test email verification middleware functionality."""
    
    def test_allows_non_post_requests(self):
        """Test that GET requests are not blocked."""
        # Create mock request
        request = Mock()
        request.method = 'GET'
        request.path = '/api/v1/stories'
        
        # Create mock get_response
        mock_response = Mock()
        get_response = Mock(return_value=mock_response)
        
        # Create middleware
        middleware = EmailVerificationMiddleware(get_response)
        
        # Call middleware
        response = middleware(request)
        
        # Should call get_response and return its result
        get_response.assert_called_once_with(request)
        assert response == mock_response
    
    def test_allows_non_protected_endpoints(self):
        """Test that POST requests to non-protected endpoints are not blocked."""
        # Create mock request
        request = Mock()
        request.method = 'POST'
        request.path = '/api/v1/users/profile'
        
        # Create mock get_response
        mock_response = Mock()
        get_response = Mock(return_value=mock_response)
        
        # Create middleware
        middleware = EmailVerificationMiddleware(get_response)
        
        # Call middleware
        response = middleware(request)
        
        # Should call get_response and return its result
        get_response.assert_called_once_with(request)
        assert response == mock_response
    
    def test_allows_unauthenticated_requests(self):
        """Test that unauthenticated requests to protected endpoints are not blocked by this middleware."""
        # Create mock request without user_profile
        request = Mock()
        request.method = 'POST'
        request.path = '/api/v1/stories'
        request.user_profile = None
        
        # Create mock get_response
        mock_response = Mock()
        get_response = Mock(return_value=mock_response)
        
        # Create middleware
        middleware = EmailVerificationMiddleware(get_response)
        
        # Call middleware
        response = middleware(request)
        
        # Should call get_response (auth middleware will handle authentication)
        get_response.assert_called_once_with(request)
        assert response == mock_response
    
    @patch('apps.users.email_verification.middleware.EmailVerificationService')
    def test_blocks_unverified_user_story_creation(self, mock_service_class):
        """Test that unverified users are blocked from creating stories."""
        # Setup mock service
        mock_service = Mock()
        mock_service.is_email_verified_sync.return_value = False
        mock_service_class.return_value = mock_service
        
        # Create mock request
        request = Mock()
        request.method = 'POST'
        request.path = '/api/v1/stories'
        request.user_profile = Mock(id='user123')
        
        # Create mock get_response
        get_response = Mock()
        
        # Create middleware
        middleware = EmailVerificationMiddleware(get_response)
        
        # Call middleware
        response = middleware(request)
        
        # Should not call get_response
        get_response.assert_not_called()
        
        # Should return 403 error
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['error']['code'] == 'EMAIL_NOT_VERIFIED'
        assert 'email verification' in response.data['error']['message'].lower()
    
    @patch('apps.users.email_verification.middleware.EmailVerificationService')
    def test_blocks_unverified_user_whisper_creation(self, mock_service_class):
        """Test that unverified users are blocked from creating whispers."""
        # Setup mock service
        mock_service = Mock()
        mock_service.is_email_verified_sync.return_value = False
        mock_service_class.return_value = mock_service
        
        # Create mock request
        request = Mock()
        request.method = 'POST'
        request.path = '/api/v1/whispers'
        request.user_profile = Mock(id='user123')
        
        # Create mock get_response
        get_response = Mock()
        
        # Create middleware
        middleware = EmailVerificationMiddleware(get_response)
        
        # Call middleware
        response = middleware(request)
        
        # Should not call get_response
        get_response.assert_not_called()
        
        # Should return 403 error
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['error']['code'] == 'EMAIL_NOT_VERIFIED'
    
    @patch('apps.users.email_verification.middleware.EmailVerificationService')
    def test_blocks_unverified_user_chapter_creation(self, mock_service_class):
        """Test that unverified users are blocked from creating chapters."""
        # Setup mock service
        mock_service = Mock()
        mock_service.is_email_verified_sync.return_value = False
        mock_service_class.return_value = mock_service
        
        # Create mock request
        request = Mock()
        request.method = 'POST'
        request.path = '/api/v1/stories/123e4567-e89b-12d3-a456-426614174000/chapters'
        request.user_profile = Mock(id='user123')
        
        # Create mock get_response
        get_response = Mock()
        
        # Create middleware
        middleware = EmailVerificationMiddleware(get_response)
        
        # Call middleware
        response = middleware(request)
        
        # Should not call get_response
        get_response.assert_not_called()
        
        # Should return 403 error
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['error']['code'] == 'EMAIL_NOT_VERIFIED'
    
    @patch('apps.users.email_verification.middleware.EmailVerificationService')
    def test_allows_verified_user_story_creation(self, mock_service_class):
        """Test that verified users can create stories."""
        # Setup mock service
        mock_service = Mock()
        mock_service.is_email_verified_sync.return_value = True
        mock_service_class.return_value = mock_service
        
        # Create mock request
        request = Mock()
        request.method = 'POST'
        request.path = '/api/v1/stories'
        request.user_profile = Mock(id='user123')
        
        # Create mock get_response
        mock_response = Mock()
        get_response = Mock(return_value=mock_response)
        
        # Create middleware
        middleware = EmailVerificationMiddleware(get_response)
        
        # Call middleware
        response = middleware(request)
        
        # Should call get_response
        get_response.assert_called_once_with(request)
        assert response == mock_response
    
    @patch('apps.users.email_verification.middleware.EmailVerificationService')
    def test_allows_verified_user_whisper_creation(self, mock_service_class):
        """Test that verified users can create whispers."""
        # Setup mock service
        mock_service = Mock()
        mock_service.is_email_verified_sync.return_value = True
        mock_service_class.return_value = mock_service
        
        # Create mock request
        request = Mock()
        request.method = 'POST'
        request.path = '/api/v1/whispers'
        request.user_profile = Mock(id='user123')
        
        # Create mock get_response
        mock_response = Mock()
        get_response = Mock(return_value=mock_response)
        
        # Create middleware
        middleware = EmailVerificationMiddleware(get_response)
        
        # Call middleware
        response = middleware(request)
        
        # Should call get_response
        get_response.assert_called_once_with(request)
        assert response == mock_response
    
    @patch('apps.users.email_verification.middleware.EmailVerificationService')
    def test_allows_verified_user_chapter_creation(self, mock_service_class):
        """Test that verified users can create chapters."""
        # Setup mock service
        mock_service = Mock()
        mock_service.is_email_verified_sync.return_value = True
        mock_service_class.return_value = mock_service
        
        # Create mock request
        request = Mock()
        request.method = 'POST'
        request.path = '/api/v1/stories/123e4567-e89b-12d3-a456-426614174000/chapters'
        request.user_profile = Mock(id='user123')
        
        # Create mock get_response
        mock_response = Mock()
        get_response = Mock(return_value=mock_response)
        
        # Create middleware
        middleware = EmailVerificationMiddleware(get_response)
        
        # Call middleware
        response = middleware(request)
        
        # Should call get_response
        get_response.assert_called_once_with(request)
        assert response == mock_response
    
    @patch('apps.users.email_verification.middleware.EmailVerificationService')
    def test_fails_open_on_verification_check_error(self, mock_service_class):
        """Test that middleware allows request if verification check fails."""
        # Setup mock service to raise exception
        mock_service = Mock()
        mock_service.is_email_verified_sync.side_effect = Exception("Database error")
        mock_service_class.return_value = mock_service
        
        # Create mock request
        request = Mock()
        request.method = 'POST'
        request.path = '/api/v1/stories'
        request.user_profile = Mock(id='user123')
        
        # Create mock get_response
        mock_response = Mock()
        get_response = Mock(return_value=mock_response)
        
        # Create middleware
        middleware = EmailVerificationMiddleware(get_response)
        
        # Call middleware
        response = middleware(request)
        
        # Should call get_response (fail open)
        get_response.assert_called_once_with(request)
        assert response == mock_response
    
    def test_error_response_format(self):
        """Test that error response has correct format with helpful details."""
        # Setup mock service
        with patch('apps.users.email_verification.middleware.EmailVerificationService') as mock_service_class:
            mock_service = Mock()
            mock_service.is_email_verified_sync.return_value = False
            mock_service_class.return_value = mock_service
            
            # Create mock request
            request = Mock()
            request.method = 'POST'
            request.path = '/api/v1/stories'
            request.user_profile = Mock(id='user123')
            
            # Create mock get_response
            get_response = Mock()
            
            # Create middleware
            middleware = EmailVerificationMiddleware(get_response)
            
            # Call middleware
            response = middleware(request)
            
            # Check response structure
            assert 'error' in response.data
            assert 'code' in response.data['error']
            assert 'message' in response.data['error']
            assert 'details' in response.data['error']
            assert 'reason' in response.data['error']['details']
            assert 'action' in response.data['error']['details']
            
            # Check that details provide helpful information
            assert 'verify' in response.data['error']['details']['reason'].lower()
            assert 'email' in response.data['error']['details']['action'].lower()
