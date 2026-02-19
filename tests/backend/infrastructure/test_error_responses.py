"""
Tests for error response utilities.

This test suite validates the structured error response creation,
error code mapping, request ID tracking, mobile-friendly messages,
and retry guidance functionality.

Requirements: 15.1, 15.2, 15.3, 15.4
"""

import pytest
import json
import django
from django.conf import settings

# Configure Django settings if not already configured
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-secret-key',
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
        MIDDLEWARE=[],
        ROOT_URLCONF='',
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        DEFAULT_CHARSET='utf-8',
    )
    django.setup()

from django.test import RequestFactory
from django.http import JsonResponse

from infrastructure.error_responses import (
    ErrorCode,
    ErrorCategory,
    ErrorResponseBuilder,
    create_error_response,
    create_mobile_error_response,
    create_validation_error_response,
    create_missing_field_error_response,
    create_file_too_large_error_response,
    create_rate_limit_error_response,
    create_sync_conflict_error_response,
    create_external_service_error_response,
    ERROR_CODE_TO_STATUS,
    ERROR_CODE_TO_CATEGORY,
)
from infrastructure.error_messages import ErrorMessages, RetryGuidance, TechnicalDetails


class TestErrorCode:
    """Test error code enum."""
    
    def test_error_code_values_are_strings(self):
        """Test that all error codes are strings."""
        for code in ErrorCode:
            assert isinstance(code.value, str)
    
    def test_client_error_codes_exist(self):
        """Test that client error codes exist."""
        assert ErrorCode.INVALID_REQUEST
        assert ErrorCode.MISSING_FIELD
        assert ErrorCode.TOKEN_EXPIRED
        assert ErrorCode.RESOURCE_NOT_FOUND
    
    def test_server_error_codes_exist(self):
        """Test that server error codes exist."""
        assert ErrorCode.INTERNAL_ERROR
        assert ErrorCode.DATABASE_ERROR
        assert ErrorCode.SERVICE_UNAVAILABLE


class TestErrorCodeMapping:
    """Test error code to status code mapping."""
    
    def test_all_error_codes_have_status_mapping(self):
        """Test that all error codes have HTTP status mappings."""
        for code in ErrorCode:
            assert code in ERROR_CODE_TO_STATUS
            assert isinstance(ERROR_CODE_TO_STATUS[code], int)
    
    def test_client_errors_map_to_4xx(self):
        """Test that client errors map to 4xx status codes."""
        client_errors = [
            ErrorCode.INVALID_REQUEST,
            ErrorCode.MISSING_FIELD,
            ErrorCode.TOKEN_EXPIRED,
            ErrorCode.RESOURCE_NOT_FOUND,
        ]
        for code in client_errors:
            status = ERROR_CODE_TO_STATUS[code]
            assert 400 <= status < 500
    
    def test_server_errors_map_to_5xx(self):
        """Test that server errors map to 5xx status codes."""
        server_errors = [
            ErrorCode.INTERNAL_ERROR,
            ErrorCode.DATABASE_ERROR,
            ErrorCode.SERVICE_UNAVAILABLE,
        ]
        for code in server_errors:
            status = ERROR_CODE_TO_STATUS[code]
            assert 500 <= status < 600
    
    def test_all_error_codes_have_category_mapping(self):
        """Test that all error codes have category mappings."""
        for code in ErrorCode:
            assert code in ERROR_CODE_TO_CATEGORY
            assert isinstance(ERROR_CODE_TO_CATEGORY[code], ErrorCategory)


class TestErrorResponseBuilder:
    """Test error response builder."""
    
    def test_builder_creates_basic_error_response(self):
        """Test that builder creates basic error response."""
        builder = ErrorResponseBuilder(
            ErrorCode.INVALID_REQUEST,
            "Invalid request"
        )
        
        response = builder.build()
        
        assert "error" in response
        assert response["error"]["code"] == "INVALID_REQUEST"
        assert response["error"]["message"] == "Invalid request"
    
    def test_builder_with_technical_details(self):
        """Test builder with technical details."""
        builder = ErrorResponseBuilder(
            ErrorCode.INVALID_FIELD_VALUE,
            "Invalid field"
        )
        builder.with_technical_details(field="email", reason="Invalid format")
        
        response = builder.build()
        
        assert "details" in response["error"]
        assert response["error"]["details"]["field"] == "email"
        assert response["error"]["details"]["reason"] == "Invalid format"
    
    def test_builder_with_retry_after(self):
        """Test builder with retry after."""
        builder = ErrorResponseBuilder(
            ErrorCode.RATE_LIMIT_EXCEEDED,
            "Rate limit exceeded"
        )
        builder.with_retry_after(30)
        
        response = builder.build()
        
        assert response["error"]["retry_after"] == 30
    
    def test_builder_with_retry_guidance(self):
        """Test builder with retry guidance."""
        builder = ErrorResponseBuilder(
            ErrorCode.SERVICE_UNAVAILABLE,
            "Service unavailable"
        )
        builder.with_retry_guidance("Please wait a few minutes and try again.")
        
        response = builder.build()
        
        assert "retry_guidance" in response["error"]
        assert "wait a few minutes" in response["error"]["retry_guidance"]
    
    def test_builder_with_request_id(self):
        """Test builder with request ID."""
        builder = ErrorResponseBuilder(
            ErrorCode.INTERNAL_ERROR,
            "Internal error"
        )
        builder.with_request_id("req_123456")
        
        response = builder.build()
        
        assert response["error"]["request_id"] == "req_123456"
    
    def test_builder_with_custom_status_code(self):
        """Test builder with custom status code."""
        builder = ErrorResponseBuilder(
            ErrorCode.INTERNAL_ERROR,
            "Internal error"
        )
        builder.with_status_code(503)
        
        assert builder.status_code == 503
    
    def test_builder_chaining(self):
        """Test that builder methods can be chained."""
        builder = ErrorResponseBuilder(
            ErrorCode.RATE_LIMIT_EXCEEDED,
            "Rate limit exceeded"
        )
        
        response = (builder
                   .with_request_id("req_123")
                   .with_retry_after(30)
                   .with_retry_guidance("Wait and retry")
                   .with_technical_details(limit=100, window="per minute")
                   .build())
        
        assert response["error"]["request_id"] == "req_123"
        assert response["error"]["retry_after"] == 30
        assert response["error"]["retry_guidance"] == "Wait and retry"
        assert response["error"]["details"]["limit"] == 100
    
    def test_builder_build_response_returns_json_response(self):
        """Test that build_response returns JsonResponse."""
        builder = ErrorResponseBuilder(
            ErrorCode.INVALID_REQUEST,
            "Invalid request"
        )
        
        response = builder.build_response()
        
        assert isinstance(response, JsonResponse)
        assert response.status_code == 400
    
    def test_builder_build_response_includes_retry_after_header(self):
        """Test that build_response includes Retry-After header."""
        builder = ErrorResponseBuilder(
            ErrorCode.RATE_LIMIT_EXCEEDED,
            "Rate limit exceeded"
        )
        builder.with_retry_after(30)
        
        response = builder.build_response()
        
        assert "Retry-After" in response
        assert response["Retry-After"] == "30"
    
    def test_builder_build_response_includes_request_id_header(self):
        """Test that build_response includes X-Request-ID header."""
        builder = ErrorResponseBuilder(
            ErrorCode.INTERNAL_ERROR,
            "Internal error"
        )
        builder.with_request_id("req_123456")
        
        response = builder.build_response()
        
        assert "X-Request-ID" in response
        assert response["X-Request-ID"] == "req_123456"


class TestCreateErrorResponse:
    """Test create_error_response convenience function."""
    
    @pytest.fixture
    def factory(self):
        """Create request factory."""
        return RequestFactory()
    
    def test_creates_error_response_without_request(self):
        """Test creating error response without request object."""
        response = create_error_response(
            ErrorCode.INVALID_REQUEST,
            "Invalid request"
        )
        
        assert isinstance(response, JsonResponse)
        assert response.status_code == 400
        
        data = json.loads(response.content)
        assert data["error"]["code"] == "INVALID_REQUEST"
        assert data["error"]["message"] == "Invalid request"
    
    def test_creates_error_response_with_request(self, factory):
        """Test creating error response with request object."""
        request = factory.get('/v1/stories/')
        request.request_id = "req_test_123"
        
        response = create_error_response(
            ErrorCode.RESOURCE_NOT_FOUND,
            "Resource not found",
            request=request
        )
        
        data = json.loads(response.content)
        assert data["error"]["request_id"] == "req_test_123"
    
    def test_creates_error_response_with_technical_details(self):
        """Test creating error response with technical details."""
        response = create_error_response(
            ErrorCode.INVALID_FIELD_VALUE,
            "Invalid field",
            technical_details={"field": "email", "reason": "Invalid format"}
        )
        
        data = json.loads(response.content)
        assert "details" in data["error"]
        assert data["error"]["details"]["field"] == "email"
    
    def test_creates_error_response_with_retry_guidance(self):
        """Test creating error response with retry guidance."""
        response = create_error_response(
            ErrorCode.SERVICE_UNAVAILABLE,
            "Service unavailable",
            retry_after=300,
            retry_guidance="Please wait 5 minutes and try again."
        )
        
        data = json.loads(response.content)
        assert data["error"]["retry_after"] == 300
        assert data["error"]["retry_guidance"] == "Please wait 5 minutes and try again."
        assert response["Retry-After"] == "300"


class TestCreateMobileErrorResponse:
    """Test create_mobile_error_response convenience function."""
    
    @pytest.fixture
    def factory(self):
        """Create request factory."""
        return RequestFactory()
    
    def test_creates_mobile_error_with_default_message(self):
        """Test creating mobile error with default user-friendly message."""
        response = create_mobile_error_response(
            ErrorCode.RATE_LIMIT_EXCEEDED
        )
        
        data = json.loads(response.content)
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        # Should have user-friendly message
        assert "too quickly" in data["error"]["message"].lower()
    
    def test_creates_mobile_error_with_custom_message(self):
        """Test creating mobile error with custom message."""
        response = create_mobile_error_response(
            ErrorCode.RATE_LIMIT_EXCEEDED,
            custom_message="Custom rate limit message"
        )
        
        data = json.loads(response.content)
        assert data["error"]["message"] == "Custom rate limit message"
    
    def test_creates_mobile_error_with_automatic_retry_guidance(self):
        """Test that mobile error includes automatic retry guidance."""
        response = create_mobile_error_response(
            ErrorCode.RATE_LIMIT_EXCEEDED
        )
        
        data = json.loads(response.content)
        assert "retry_guidance" in data["error"]
        assert "retry_after" in data["error"]
    
    def test_creates_mobile_error_without_retry_for_non_retryable(self):
        """Test that non-retryable errors don't include retry guidance."""
        response = create_mobile_error_response(
            ErrorCode.RESOURCE_NOT_FOUND
        )
        
        data = json.loads(response.content)
        assert "retry_guidance" not in data["error"]
        assert "retry_after" not in data["error"]


class TestValidationErrorResponse:
    """Test validation error response helpers."""
    
    @pytest.fixture
    def factory(self):
        """Create request factory."""
        return RequestFactory()
    
    def test_creates_validation_error_response(self):
        """Test creating validation error response."""
        response = create_validation_error_response(
            field_name="email",
            reason="Invalid email format"
        )
        
        assert response.status_code == 422
        data = json.loads(response.content)
        assert data["error"]["code"] == "INVALID_FIELD_VALUE"
        assert data["error"]["details"]["field"] == "email"
        assert "Invalid email format" in data["error"]["details"]["technical_message"]
    
    def test_creates_missing_field_error_response(self):
        """Test creating missing field error response."""
        response = create_missing_field_error_response(
            field_name="title"
        )
        
        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["error"]["code"] == "MISSING_FIELD"
        assert data["error"]["details"]["field"] == "title"


class TestFileErrorResponse:
    """Test file error response helpers."""
    
    def test_creates_file_too_large_error_response(self):
        """Test creating file too large error response."""
        file_size = 60 * 1024 * 1024  # 60MB
        max_size = 50 * 1024 * 1024   # 50MB
        
        response = create_file_too_large_error_response(
            file_size=file_size,
            max_size=max_size
        )
        
        assert response.status_code == 413
        data = json.loads(response.content)
        assert data["error"]["code"] == "FILE_TOO_LARGE"
        assert data["error"]["details"]["file_size_bytes"] == file_size
        assert data["error"]["details"]["max_size_bytes"] == max_size
        assert data["error"]["details"]["file_size_mb"] == 60.0
        assert data["error"]["details"]["max_size_mb"] == 50.0


class TestRateLimitErrorResponse:
    """Test rate limit error response helpers."""
    
    def test_creates_rate_limit_error_response(self):
        """Test creating rate limit error response."""
        response = create_rate_limit_error_response(
            limit=100,
            window="per minute",
            reset_time="2024-01-01T12:00:00Z"
        )
        
        assert response.status_code == 429
        data = json.loads(response.content)
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert data["error"]["details"]["rate_limit"] == 100
        assert data["error"]["details"]["window"] == "per minute"
        assert data["error"]["details"]["reset_time"] == "2024-01-01T12:00:00Z"
        assert "Retry-After" in response


class TestSyncConflictErrorResponse:
    """Test sync conflict error response helpers."""
    
    def test_creates_sync_conflict_error_response(self):
        """Test creating sync conflict error response."""
        response = create_sync_conflict_error_response(
            client_version="v1",
            server_version="v2",
            conflicting_fields=["title", "content"]
        )
        
        assert response.status_code == 409
        data = json.loads(response.content)
        assert data["error"]["code"] == "SYNC_CONFLICT"
        assert data["error"]["details"]["client_version"] == "v1"
        assert data["error"]["details"]["server_version"] == "v2"
        assert "title" in data["error"]["details"]["conflicting_fields"]
        assert "content" in data["error"]["details"]["conflicting_fields"]


class TestExternalServiceErrorResponse:
    """Test external service error response helpers."""
    
    def test_creates_external_service_error_response(self):
        """Test creating external service error response."""
        response = create_external_service_error_response(
            service_name="FCM",
            error_message="Connection timeout",
            status_code=504
        )
        
        data = json.loads(response.content)
        assert data["error"]["details"]["service"] == "FCM"
        assert data["error"]["details"]["service_error"] == "Connection timeout"
        assert data["error"]["details"]["service_status_code"] == 504
    
    def test_creates_external_service_error_with_custom_code(self):
        """Test creating external service error with custom error code."""
        response = create_external_service_error_response(
            service_name="S3",
            error_message="Upload failed",
            error_code=ErrorCode.STORAGE_SERVICE_ERROR
        )
        
        assert response.status_code == 502
        data = json.loads(response.content)
        assert data["error"]["code"] == "STORAGE_SERVICE_ERROR"


class TestErrorMessages:
    """Test error message templates."""
    
    def test_get_message_returns_user_friendly_text(self):
        """Test that get_message returns user-friendly text."""
        message = ErrorMessages.get_message(ErrorCode.RATE_LIMIT_EXCEEDED)
        
        assert isinstance(message, str)
        assert len(message) > 0
        # Should be user-friendly, not technical
        assert "too quickly" in message.lower() or "wait" in message.lower()
    
    def test_all_error_codes_have_messages(self):
        """Test that all error codes have user-friendly messages."""
        for code in ErrorCode:
            message = ErrorMessages.get_message(code)
            assert isinstance(message, str)
            assert len(message) > 0


class TestRetryGuidance:
    """Test retry guidance."""
    
    def test_get_guidance_returns_string_or_none(self):
        """Test that get_guidance returns string or None."""
        for code in ErrorCode:
            guidance = RetryGuidance.get_guidance(code)
            assert guidance is None or isinstance(guidance, str)
    
    def test_retryable_errors_have_guidance(self):
        """Test that retryable errors have guidance."""
        retryable_errors = [
            ErrorCode.RATE_LIMIT_EXCEEDED,
            ErrorCode.SERVICE_UNAVAILABLE,
            ErrorCode.INTERNAL_ERROR,
        ]
        for code in retryable_errors:
            guidance = RetryGuidance.get_guidance(code)
            assert guidance is not None
            assert isinstance(guidance, str)
    
    def test_non_retryable_errors_have_no_guidance(self):
        """Test that non-retryable errors have no guidance."""
        non_retryable_errors = [
            ErrorCode.RESOURCE_NOT_FOUND,
            ErrorCode.INSUFFICIENT_PERMISSIONS,
        ]
        for code in non_retryable_errors:
            guidance = RetryGuidance.get_guidance(code)
            assert guidance is None
    
    def test_get_retry_delay_returns_int_or_none(self):
        """Test that get_retry_delay returns int or None."""
        for code in ErrorCode:
            delay = RetryGuidance.get_retry_delay(code)
            assert delay is None or isinstance(delay, int)
    
    def test_retryable_errors_have_delay(self):
        """Test that retryable errors have delay."""
        retryable_errors = [
            ErrorCode.RATE_LIMIT_EXCEEDED,
            ErrorCode.SERVICE_UNAVAILABLE,
        ]
        for code in retryable_errors:
            delay = RetryGuidance.get_retry_delay(code)
            assert delay is not None
            assert delay > 0


class TestTechnicalDetails:
    """Test technical details helpers."""
    
    def test_for_missing_field_creates_details(self):
        """Test creating technical details for missing field."""
        details = TechnicalDetails.for_missing_field("email")
        
        assert details["field"] == "email"
        assert "technical_message" in details
        assert "email" in details["technical_message"]
    
    def test_for_invalid_field_creates_details(self):
        """Test creating technical details for invalid field."""
        details = TechnicalDetails.for_invalid_field("email", "Invalid format")
        
        assert details["field"] == "email"
        assert "Invalid format" in details["technical_message"]
    
    def test_for_file_too_large_creates_details(self):
        """Test creating technical details for file too large."""
        details = TechnicalDetails.for_file_too_large(60000000, 50000000)
        
        assert details["file_size_bytes"] == 60000000
        assert details["max_size_bytes"] == 50000000
        assert "file_size_mb" in details
        assert "max_size_mb" in details
    
    def test_for_rate_limit_creates_details(self):
        """Test creating technical details for rate limit."""
        details = TechnicalDetails.for_rate_limit(100, "per minute")
        
        assert details["rate_limit"] == 100
        assert details["window"] == "per minute"
        assert "technical_message" in details
    
    def test_for_sync_conflict_creates_details(self):
        """Test creating technical details for sync conflict."""
        details = TechnicalDetails.for_sync_conflict("v1", "v2", ["title"])
        
        assert details["client_version"] == "v1"
        assert details["server_version"] == "v2"
        assert "title" in details["conflicting_fields"]
    
    def test_for_external_service_error_creates_details(self):
        """Test creating technical details for external service error."""
        details = TechnicalDetails.for_external_service_error(
            "FCM", "Connection timeout", 504
        )
        
        assert details["service"] == "FCM"
        assert details["service_error"] == "Connection timeout"
        assert details["service_status_code"] == 504


class TestErrorResponseStructure:
    """Test that error responses follow the required structure."""
    
    def test_error_response_has_required_fields(self):
        """Test that error response has all required fields."""
        response = create_mobile_error_response(ErrorCode.INVALID_REQUEST)
        data = json.loads(response.content)
        
        # Must have error object
        assert "error" in data
        # Must have code and message
        assert "code" in data["error"]
        assert "message" in data["error"]
        # Must have request_id
        assert "request_id" in data["error"]
    
    def test_error_response_code_is_string(self):
        """Test that error code is a string."""
        response = create_mobile_error_response(ErrorCode.INVALID_REQUEST)
        data = json.loads(response.content)
        
        assert isinstance(data["error"]["code"], str)
    
    def test_error_response_message_is_string(self):
        """Test that error message is a string."""
        response = create_mobile_error_response(ErrorCode.INVALID_REQUEST)
        data = json.loads(response.content)
        
        assert isinstance(data["error"]["message"], str)
        assert len(data["error"]["message"]) > 0
    
    def test_error_response_follows_json_structure(self):
        """Test that error response is valid JSON."""
        response = create_mobile_error_response(ErrorCode.INVALID_REQUEST)
        
        # Should not raise exception
        data = json.loads(response.content)
        assert isinstance(data, dict)
