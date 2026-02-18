"""Tests for timeout middleware."""
import pytest
import time
import sys
import os
import json
import signal
from pathlib import Path
from unittest.mock import Mock, patch
from django.http import HttpRequest, JsonResponse
from django.test import RequestFactory
import django

# Add apps/backend to path
backend_path = Path(__file__).parent.parent.parent.parent / 'apps' / 'backend'
sys.path.insert(0, str(backend_path))

# Configure Django settings before importing middleware
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('SKIP_CONFIG_VALIDATION', 'True')
django.setup()

from infrastructure.timeout_middleware import TimeoutMiddleware


class TestTimeoutMiddleware:
    """Tests for TimeoutMiddleware."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        get_response = Mock(return_value=JsonResponse({'status': 'ok'}))
        return TimeoutMiddleware(get_response)
    
    @pytest.fixture
    def request_factory(self):
        """Create request factory."""
        return RequestFactory()
    
    def test_middleware_initialization(self, middleware):
        """Test middleware initializes with correct timeout."""
        assert middleware.timeout == 30  # Default timeout
        assert middleware.get_response is not None
    
    @pytest.mark.skipif(not hasattr(signal, 'SIGALRM'), reason="SIGALRM not available on Windows")
    def test_normal_request_completes(self, middleware, request_factory):
        """Test that normal requests complete successfully."""
        request = request_factory.get('/api/test')
        response = middleware(request)
        
        assert response.status_code == 200
        middleware.get_response.assert_called_once_with(request)
    
    def test_admin_path_skips_timeout(self, middleware, request_factory):
        """Test that admin paths skip timeout."""
        request = request_factory.get('/django-admin/users/')
        
        assert middleware.should_skip_timeout(request) is True
    
    def test_api_path_does_not_skip_timeout(self, middleware, request_factory):
        """Test that API paths do not skip timeout."""
        request = request_factory.get('/api/stories')
        
        assert middleware.should_skip_timeout(request) is False
    
    def test_timeout_handler_raises_error(self, middleware):
        """Test that timeout handler raises TimeoutError."""
        with pytest.raises(TimeoutError) as exc_info:
            middleware.timeout_handler(None, None)
        
        assert "exceeded" in str(exc_info.value).lower()
        assert "30s" in str(exc_info.value)
    
    def test_handle_timeout_returns_504(self, middleware, request_factory):
        """Test that timeout handling returns 504 status."""
        request = request_factory.get('/api/slow-endpoint')
        error = TimeoutError("Request exceeded 30s timeout")
        
        response = middleware.handle_timeout(request, error)
        
        assert response.status_code == 504
        data = json.loads(response.content)
        assert 'error' in data
        assert 'timeout' in data['error'].lower()
    
    def test_timeout_response_includes_details(self, middleware, request_factory):
        """Test that timeout response includes helpful details."""
        request = request_factory.get('/api/slow-endpoint')
        error = TimeoutError("Request exceeded 30s timeout")
        
        response = middleware.handle_timeout(request, error)
        data = json.loads(response.content)
        
        assert 'error' in data
        assert 'message' in data
        assert 'timeout' in data
        assert data['timeout'] == 30
    
    @patch('infrastructure.timeout_middleware.signal')
    def test_alarm_is_set_and_cancelled(self, mock_signal, middleware, request_factory):
        """Test that alarm is properly set and cancelled."""
        request = request_factory.get('/api/test')
        
        # Mock signal functions
        mock_signal.SIGALRM = 14
        mock_signal.signal = Mock()
        mock_signal.alarm = Mock()
        
        middleware(request)
        
        # Verify alarm was set
        assert mock_signal.alarm.call_count >= 1
        # Verify alarm was cancelled (called with 0)
        mock_signal.alarm.assert_any_call(0)
    
    def test_skip_paths_configuration(self, middleware):
        """Test that skip paths are properly configured."""
        assert '/django-admin/' in middleware.SKIP_PATHS
        assert '/admin/' in middleware.SKIP_PATHS
    
    @patch('infrastructure.timeout_middleware.logger')
    def test_timeout_is_logged(self, mock_logger, middleware, request_factory):
        """Test that timeouts are logged with proper context."""
        request = request_factory.get('/api/slow-endpoint')
        request.method = 'GET'
        error = TimeoutError("Request exceeded 30s timeout")
        
        middleware.handle_timeout(request, error)
        
        # Verify error was logged
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        
        # Check that extra context was provided
        assert 'extra' in call_args.kwargs
        extra = call_args.kwargs['extra']
        assert 'path' in extra
        assert 'method' in extra
        assert 'timeout' in extra
