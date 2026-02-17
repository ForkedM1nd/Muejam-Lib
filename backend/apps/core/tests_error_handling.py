"""Tests for error handling and validation."""
import pytest
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied, NotFound
from rest_framework import status
from apps.core.exceptions import (
    custom_exception_handler,
    RateLimitExceeded,
    InvalidCursor,
    ContentDeleted,
    UserBlocked,
    DuplicateResource,
    InvalidOffset,
    AuthenticationRequired,
    InvalidToken,
    InsufficientPermissions,
    validate_serializer
)
from rest_framework import serializers


class TestCustomExceptionHandler:
    """
    Test custom exception handler for consistent error responses.
    
    Requirements:
        - 17.2: Return JSON with error code, message, and details
        - 17.3: Map Django/DRF exceptions to appropriate HTTP status codes
    """
    
    def test_validation_error_format(self):
        """Test that validation errors are formatted consistently."""
        exc = ValidationError({'field': 'This field is required.'})
        factory = APIRequestFactory()
        request = factory.get('/')
        context = {'request': request}
        
        response = custom_exception_handler(exc, context)
        
        assert response is not None
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert 'code' in response.data['error']
        assert 'message' in response.data['error']
        assert 'details' in response.data['error']
        assert response.data['error']['code'] == 'VALIDATION_ERROR'
    
    def test_authentication_error_format(self):
        """Test that authentication errors return HTTP 401."""
        exc = NotAuthenticated()
        factory = APIRequestFactory()
        request = factory.get('/')
        context = {'request': request}
        
        response = custom_exception_handler(exc, context)
        
        assert response is not None
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in response.data
        assert response.data['error']['code'] == 'AUTHENTICATION_FAILED'
    
    def test_permission_error_format(self):
        """Test that permission errors return HTTP 403."""
        exc = PermissionDenied()
        factory = APIRequestFactory()
        request = factory.get('/')
        context = {'request': request}
        
        response = custom_exception_handler(exc, context)
        
        assert response is not None
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'error' in response.data
        assert response.data['error']['code'] == 'PERMISSION_DENIED'
    
    def test_not_found_error_format(self):
        """Test that not found errors return HTTP 404."""
        exc = NotFound()
        factory = APIRequestFactory()
        request = factory.get('/')
        context = {'request': request}
        
        response = custom_exception_handler(exc, context)
        
        assert response is not None
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'error' in response.data
        assert response.data['error']['code'] == 'NOT_FOUND'
    
    def test_rate_limit_error_format(self):
        """Test that rate limit errors return HTTP 429."""
        exc = RateLimitExceeded()
        factory = APIRequestFactory()
        request = factory.get('/')
        context = {'request': request}
        
        response = custom_exception_handler(exc, context)
        
        assert response is not None
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert 'error' in response.data
        assert response.data['error']['code'] == 'RATE_LIMIT_EXCEEDED'


class TestCustomExceptions:
    """
    Test custom exception classes.
    
    Requirements:
        - 17.2: Custom exceptions with appropriate status codes
    """
    
    def test_authentication_required_exception(self):
        """Test AuthenticationRequired exception."""
        exc = AuthenticationRequired()
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.default_code == 'authentication_required'
    
    def test_invalid_token_exception(self):
        """Test InvalidToken exception."""
        exc = InvalidToken()
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.default_code == 'invalid_token'
    
    def test_insufficient_permissions_exception(self):
        """Test InsufficientPermissions exception."""
        exc = InsufficientPermissions()
        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert exc.default_code == 'insufficient_permissions'
    
    def test_content_deleted_exception(self):
        """Test ContentDeleted exception."""
        exc = ContentDeleted()
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.default_code == 'content_deleted'
    
    def test_duplicate_resource_exception(self):
        """Test DuplicateResource exception."""
        exc = DuplicateResource()
        assert exc.status_code == status.HTTP_409_CONFLICT
        assert exc.default_code == 'duplicate_resource'


class TestValidationHelper:
    """
    Test validation helper function.
    
    Requirements:
        - 17.5: Add DRF serializer validation for all endpoints
        - 17.6: Return HTTP 400 with detailed validation errors
    """
    
    def test_validate_serializer_with_valid_data(self):
        """Test that validate_serializer returns True for valid data."""
        class TestSerializer(serializers.Serializer):
            name = serializers.CharField(max_length=100)
        
        serializer = TestSerializer(data={'name': 'Test'})
        result = validate_serializer(serializer, raise_exception=False)
        
        assert result is True
    
    def test_validate_serializer_with_invalid_data_no_exception(self):
        """Test that validate_serializer returns False for invalid data when raise_exception=False."""
        class TestSerializer(serializers.Serializer):
            name = serializers.CharField(max_length=100, required=True)
        
        serializer = TestSerializer(data={})
        result = validate_serializer(serializer, raise_exception=False)
        
        assert result is False
        assert 'name' in serializer.errors
    
    def test_validate_serializer_with_invalid_data_raises_exception(self):
        """Test that validate_serializer raises ValidationError for invalid data when raise_exception=True."""
        class TestSerializer(serializers.Serializer):
            name = serializers.CharField(max_length=100, required=True)
        
        serializer = TestSerializer(data={})
        
        with pytest.raises(ValidationError):
            validate_serializer(serializer, raise_exception=True)


class TestErrorResponseStructure:
    """
    Test that all error responses follow the consistent structure.
    
    Requirements:
        - 17.2: Return JSON with error code, message, and details
    """
    
    def test_error_response_has_required_fields(self):
        """Test that error responses have code, message, and details fields."""
        exc = ValidationError({'field': 'Error message'})
        factory = APIRequestFactory()
        request = factory.get('/')
        context = {'request': request}
        
        response = custom_exception_handler(exc, context)
        
        assert 'error' in response.data
        assert 'code' in response.data['error']
        assert 'message' in response.data['error']
        assert 'details' in response.data['error']
        
        # Verify types
        assert isinstance(response.data['error']['code'], str)
        assert isinstance(response.data['error']['message'], str)
        assert isinstance(response.data['error']['details'], dict)
    
    def test_error_code_is_uppercase(self):
        """Test that error codes are uppercase."""
        exc = ValidationError('Test error')
        factory = APIRequestFactory()
        request = factory.get('/')
        context = {'request': request}
        
        response = custom_exception_handler(exc, context)
        
        error_code = response.data['error']['code']
        assert error_code == error_code.upper()
