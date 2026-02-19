"""
Tests for Enhanced Token Expiration Handling

Validates that token expiration errors include clear messages and
refresh guidance for mobile clients.

Requirements: 17.3
"""

import pytest
from unittest.mock import Mock, patch
from django.test import RequestFactory
from rest_framework.response import Response
from apps.users.auth_error_responses import get_auth_error_response, require_authentication
from apps.users.middleware import ClerkAuthMiddleware


class TestTokenExpirationErrorResponses:
    """Test enhanced token expiration error responses."""
    
    def test_expired_token_error_response_includes_refresh_guidance(self):
        """
        Test that expired token errors include clear message and refresh guidance.
        
        Validates: Requirement 17.3
        """
        # Create a mock request with expired token error
        request = Mock()
        request.auth_error = 'expired_token'
        request.auth_error_details = {
            'code': 'TOKEN_EXPIRED',
            'message': 'Your authentication token has expired',
            'details': {
                'technical_message': 'JWT token has expired and needs to be refreshed',
                'refresh_guidance': 'Please use the /v1/sessions/refresh endpoint with your refresh token to obtain a new access token'
            }
        }
        
        # Get error response
        response = get_auth_error_response(request)
        
        # Verify response structure
        assert response is not None
        assert response.status_code == 401
        assert 'error' in response.data
        
        error = response.data['error']
        assert error['code'] == 'TOKEN_EXPIRED'
        assert 'expired' in error['message'].lower()
        assert 'details' in error
        assert 'refresh_guidance' in error['details']
        assert '/v1/sessions/refresh' in error['details']['refresh_guidance']
    
    def test_expired_token_fallback_response(self):
        """
        Test fallback error response when auth_error_details is not set.
        
        Validates: Requirement 17.3
        """
        # Create a mock request with only auth_error set
        request = Mock()
        request.auth_error = 'expired_token'
        request.auth_error_details = None
        
        # Get error response
        response = get_auth_error_response(request)
        
        # Verify response structure
        assert response is not None
        assert response.status_code == 401
        assert 'error' in response.data
        
        error = response.data['error']
        assert error['code'] == 'TOKEN_EXPIRED'
        assert 'expired' in error['message'].lower()
        assert 'details' in error
        assert 'refresh_guidance' in error['details']
    
    def test_invalid_token_error_response(self):
        """
        Test that invalid token errors have clear messages.
        
        Validates: Requirement 17.3
        """
        # Create a mock request with invalid token error
        request = Mock()
        request.auth_error = 'invalid_token'
        request.auth_error_details = None
        
        # Get error response
        response = get_auth_error_response(request)
        
        # Verify response structure
        assert response is not None
        assert response.status_code == 401
        assert 'error' in response.data
        
        error = response.data['error']
        assert error['code'] == 'TOKEN_INVALID'
        assert 'invalid' in error['message'].lower()
    
    def test_no_auth_error_returns_none(self):
        """
        Test that get_auth_error_response returns None when no error.
        """
        # Create a mock request with no auth error
        request = Mock()
        request.auth_error = None
        
        # Get error response
        response = get_auth_error_response(request)
        
        # Should return None
        assert response is None
    
    def test_require_authentication_decorator_with_expired_token(self):
        """
        Test that require_authentication decorator returns enhanced error for expired tokens.
        
        Validates: Requirement 17.3
        """
        # Create a mock view
        @require_authentication
        def test_view(request):
            return Response({'data': 'success'})
        
        # Create a mock request with expired token
        request = Mock()
        request.auth_error = 'expired_token'
        request.auth_error_details = {
            'code': 'TOKEN_EXPIRED',
            'message': 'Your authentication token has expired',
            'details': {
                'technical_message': 'JWT token has expired and needs to be refreshed',
                'refresh_guidance': 'Please use the /v1/sessions/refresh endpoint with your refresh token to obtain a new access token'
            }
        }
        request.clerk_user_id = None
        request.user_profile = None
        
        # Call the decorated view
        response = test_view(request)
        
        # Verify error response
        assert response.status_code == 401
        assert 'error' in response.data
        assert response.data['error']['code'] == 'TOKEN_EXPIRED'
        assert 'refresh_guidance' in response.data['error']['details']
    
    def test_require_authentication_decorator_with_valid_auth(self):
        """
        Test that require_authentication decorator allows valid requests through.
        """
        # Create a mock view
        @require_authentication
        def test_view(request):
            return Response({'data': 'success'})
        
        # Create a mock request with valid authentication
        request = Mock()
        request.auth_error = None
        request.auth_error_details = None
        request.clerk_user_id = 'user_123'
        request.user_profile = Mock(id='profile_123')
        
        # Call the decorated view
        response = test_view(request)
        
        # Verify success response
        assert response.status_code == 200
        assert response.data == {'data': 'success'}
    
    def test_middleware_sets_auth_error_details_on_expiration(self):
        """
        Test that ClerkAuthMiddleware sets auth_error_details for expired tokens.
        
        Validates: Requirement 17.3
        """
        from apps.users.jwt_service import TokenExpiredError
        
        # Create a mock request
        factory = RequestFactory()
        request = factory.get('/')
        request.headers = {'Authorization': 'Bearer expired_token'}
        
        # Create middleware
        get_response = Mock(return_value=Mock())
        middleware = ClerkAuthMiddleware(get_response)
        
        # Mock the JWT service to raise TokenExpiredError
        with patch.object(middleware.jwt_service, 'verify_token', side_effect=TokenExpiredError("Token expired")):
            # Process request
            middleware(request)
        
        # Verify auth_error_details is set
        assert hasattr(request, 'auth_error')
        assert request.auth_error == 'expired_token'
        assert hasattr(request, 'auth_error_details')
        assert request.auth_error_details is not None
        assert request.auth_error_details['code'] == 'TOKEN_EXPIRED'
        assert 'refresh_guidance' in request.auth_error_details['details']
        assert '/v1/sessions/refresh' in request.auth_error_details['details']['refresh_guidance']


class TestTokenExpirationIntegration:
    """Integration tests for token expiration handling in views."""
    
    def test_mobile_session_view_error_response_structure(self):
        """
        Test that the error response structure matches requirements.
        
        This test verifies the structure of error responses without
        actually calling the async view, which would require more complex setup.
        
        Validates: Requirement 17.3
        """
        from django.test import RequestFactory
        from apps.users.auth_error_responses import get_auth_error_response
        
        # Create a proper Django request
        factory = RequestFactory()
        request = factory.post('/v1/sessions/create', data={}, content_type='application/json')
        
        # Set authentication error attributes (as set by middleware)
        request.auth_error = 'expired_token'
        request.auth_error_details = {
            'code': 'TOKEN_EXPIRED',
            'message': 'Your authentication token has expired',
            'details': {
                'technical_message': 'JWT token has expired and needs to be refreshed',
                'refresh_guidance': 'Please use the /v1/sessions/refresh endpoint with your refresh token to obtain a new access token'
            }
        }
        
        # Get the error response
        response = get_auth_error_response(request)
        
        # Verify enhanced error response structure
        assert response is not None
        assert response.status_code == 401
        assert 'error' in response.data
        
        error = response.data['error']
        assert error['code'] == 'TOKEN_EXPIRED'
        assert 'expired' in error['message'].lower()
        assert 'details' in error
        assert 'refresh_guidance' in error['details']
        assert '/v1/sessions/refresh' in error['details']['refresh_guidance']
        assert 'technical_message' in error['details']
