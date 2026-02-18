"""
Test Sentry Integration

This test verifies that Sentry is properly configured and can capture errors.
Run with: python manage.py test tests.test_sentry_integration
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.http import Http404
from rest_framework.exceptions import NotFound, PermissionDenied


class SentryIntegrationTest(TestCase):
    """Test Sentry error tracking integration"""
    
    def test_sentry_dsn_configured(self):
        """Test that SENTRY_DSN is configured"""
        from django.conf import settings
        
        # In test environment, SENTRY_DSN might not be set
        # This test just verifies the configuration structure exists
        self.assertTrue(hasattr(settings, 'SENTRY_DSN'))
    
    @patch('sentry_sdk.init')
    def test_sentry_initialization(self, mock_init):
        """Test that Sentry initializes with correct configuration"""
        from infrastructure.sentry_config import init_sentry
        
        # Set up environment
        with patch.dict(os.environ, {
            'SENTRY_DSN': 'https://test@sentry.io/123456',
            'SENTRY_ENVIRONMENT': 'test',
            'SENTRY_TRACES_SAMPLE_RATE': '0.1',
            'APP_VERSION': '1.0.0'
        }):
            init_sentry()
        
        # Verify init was called
        mock_init.assert_called_once()
        
        # Verify configuration
        call_kwargs = mock_init.call_args[1]
        self.assertEqual(call_kwargs['dsn'], 'https://test@sentry.io/123456')
        self.assertEqual(call_kwargs['environment'], 'test')
        self.assertEqual(call_kwargs['traces_sample_rate'], 0.1)
        self.assertIn('muejam-backend@1.0.0', call_kwargs['release'])
        self.assertFalse(call_kwargs['send_default_pii'])
        self.assertTrue(call_kwargs['attach_stacktrace'])
    
    def test_sentry_not_initialized_without_dsn(self):
        """Test that Sentry doesn't initialize without DSN"""
        from infrastructure.sentry_config import init_sentry
        
        with patch.dict(os.environ, {'SENTRY_DSN': ''}, clear=True):
            with patch('sentry_sdk.init') as mock_init:
                init_sentry()
                mock_init.assert_not_called()
    
    def test_sensitive_data_scrubbing(self):
        """Test that sensitive data is scrubbed from error reports"""
        from infrastructure.sentry_config import scrub_sensitive_data
        
        # Create event with sensitive data
        event = {
            'request': {
                'headers': {
                    'Authorization': 'Bearer secret_token',
                    'X-API-Key': 'api_key_123',
                    'Cookie': 'session=abc123',
                    'Content-Type': 'application/json'
                },
                'data': {
                    'username': 'testuser',
                    'password': 'secret123',
                    'token': 'jwt_token',
                    'api_key': 'key_123',
                    'email': 'test@example.com'
                },
                'query_string': 'username=test&password=secret&token=abc'
            },
            'user': {
                'id': '123',
                'email': 'user@example.com',
                'ip_address': '192.168.1.1'
            }
        }
        
        # Scrub sensitive data
        scrubbed = scrub_sensitive_data(event, None)
        
        # Verify headers are scrubbed
        self.assertNotIn('Authorization', scrubbed['request']['headers'])
        self.assertNotIn('X-API-Key', scrubbed['request']['headers'])
        self.assertNotIn('Cookie', scrubbed['request']['headers'])
        self.assertIn('Content-Type', scrubbed['request']['headers'])
        
        # Verify request data is scrubbed
        self.assertNotIn('password', scrubbed['request']['data'])
        self.assertNotIn('token', scrubbed['request']['data'])
        self.assertNotIn('api_key', scrubbed['request']['data'])
        self.assertIn('username', scrubbed['request']['data'])
        self.assertIn('email', scrubbed['request']['data'])
        
        # Verify query string is scrubbed
        self.assertIn('[REDACTED]', scrubbed['request']['query_string'])
        
        # Verify user data is scrubbed
        self.assertEqual(scrubbed['user']['email'], '[REDACTED]')
        self.assertEqual(scrubbed['user']['ip_address'], '[REDACTED]')
        self.assertIn('id', scrubbed['user'])
    
    def test_breadcrumb_scrubbing(self):
        """Test that sensitive data is scrubbed from breadcrumbs"""
        from infrastructure.sentry_config import scrub_breadcrumb_data
        
        # Create breadcrumb with sensitive data
        crumb = {
            'category': 'http',
            'data': {
                'url': 'https://api.example.com/users',
                'Authorization': 'Bearer token',
                'Cookie': 'session=abc'
            }
        }
        
        # Scrub breadcrumb
        scrubbed = scrub_breadcrumb_data(crumb, None)
        
        # Verify sensitive data is removed
        self.assertNotIn('Authorization', scrubbed['data'])
        self.assertNotIn('Cookie', scrubbed['data'])
        self.assertIn('url', scrubbed['data'])
    
    def test_ignored_errors(self):
        """Test that certain errors are ignored"""
        from infrastructure.sentry_config import init_sentry
        
        with patch.dict(os.environ, {'SENTRY_DSN': 'https://test@sentry.io/123456'}):
            with patch('sentry_sdk.init') as mock_init:
                init_sentry()
                
                call_kwargs = mock_init.call_args[1]
                ignored_errors = call_kwargs['ignore_errors']
                
                # Verify common non-critical errors are ignored
                self.assertIn('django.http.Http404', ignored_errors)
                self.assertIn('rest_framework.exceptions.NotFound', ignored_errors)
                self.assertIn('rest_framework.exceptions.PermissionDenied', ignored_errors)
    
    @patch('sentry_sdk.capture_exception')
    def test_error_tracker_capture_exception(self, mock_capture):
        """Test ErrorTracker.capture_exception"""
        from infrastructure.sentry_config import ErrorTracker
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            ErrorTracker.capture_exception(
                e,
                context={'user_id': '123', 'action': 'test'},
                level='error'
            )
        
        # Verify capture was called
        mock_capture.assert_called_once()
    
    def test_sentry_integrations_configured(self):
        """Test that Django, Celery, and Redis integrations are configured"""
        from infrastructure.sentry_config import init_sentry
        
        with patch.dict(os.environ, {'SENTRY_DSN': 'https://test@sentry.io/123456'}):
            with patch('sentry_sdk.init') as mock_init:
                init_sentry()
                
                call_kwargs = mock_init.call_args[1]
                integrations = call_kwargs['integrations']
                
                # Verify integrations are present
                self.assertEqual(len(integrations), 3)
                
                # Check integration types
                integration_names = [type(i).__name__ for i in integrations]
                self.assertIn('DjangoIntegration', integration_names)
                self.assertIn('CeleryIntegration', integration_names)
                self.assertIn('RedisIntegration', integration_names)


class SentryAlertConfigTest(TestCase):
    """Test Sentry alert configuration"""
    
    def test_alert_thresholds(self):
        """Test that alert thresholds are configured"""
        from infrastructure.sentry_alerts import SentryAlertConfig
        
        self.assertIsInstance(SentryAlertConfig.CRITICAL_ERROR_THRESHOLD, int)
        self.assertIsInstance(SentryAlertConfig.ERROR_RATE_THRESHOLD, float)
        self.assertGreater(SentryAlertConfig.CRITICAL_ERROR_THRESHOLD, 0)
        self.assertGreater(SentryAlertConfig.ERROR_RATE_THRESHOLD, 0)
    
    def test_email_alert_configuration(self):
        """Test email alert configuration"""
        from infrastructure.sentry_alerts import SentryAlertConfig
        
        self.assertIsInstance(SentryAlertConfig.EMAIL_ALERTS_ENABLED, bool)
        self.assertIsInstance(SentryAlertConfig.ALERT_EMAIL_RECIPIENTS, list)
    
    def test_slack_integration_configuration(self):
        """Test Slack integration configuration"""
        from infrastructure.sentry_alerts import SentryAlertConfig
        
        self.assertIsInstance(SentryAlertConfig.SLACK_ALERTS_ENABLED, bool)
        self.assertIsInstance(SentryAlertConfig.SLACK_WEBHOOK_URL, str)
        self.assertIsInstance(SentryAlertConfig.SLACK_CHANNEL, str)
    
    def test_error_grouping_rules(self):
        """Test error grouping rules are defined"""
        from infrastructure.sentry_alerts import SentryAlertConfig
        
        rules = SentryAlertConfig.ERROR_GROUPING_RULES
        
        # Verify key error categories are defined
        self.assertIn('database', rules)
        self.assertIn('authentication', rules)
        self.assertIn('external_service', rules)
        self.assertIn('rate_limit', rules)
        self.assertIn('validation', rules)
        
        # Verify each rule has required fields
        for category, rule in rules.items():
            self.assertIn('fingerprint', rule)
            self.assertIn('patterns', rule)
            self.assertIsInstance(rule['patterns'], list)


@pytest.mark.integration
class SentryEndToEndTest(TestCase):
    """End-to-end tests for Sentry integration (requires SENTRY_DSN)"""
    
    @pytest.mark.skipif(
        not os.getenv('SENTRY_DSN'),
        reason="SENTRY_DSN not configured"
    )
    def test_send_test_error_to_sentry(self):
        """Send a test error to Sentry to verify integration works"""
        import sentry_sdk
        
        # Capture a test exception
        try:
            raise Exception("Test error from Sentry integration test")
        except Exception as e:
            event_id = sentry_sdk.capture_exception(e)
            self.assertIsNotNone(event_id)
            print(f"Test error sent to Sentry with event ID: {event_id}")
    
    @pytest.mark.skipif(
        not os.getenv('SENTRY_DSN'),
        reason="SENTRY_DSN not configured"
    )
    def test_send_test_message_to_sentry(self):
        """Send a test message to Sentry"""
        import sentry_sdk
        
        event_id = sentry_sdk.capture_message(
            "Test message from Sentry integration test",
            level='info'
        )
        self.assertIsNotNone(event_id)
        print(f"Test message sent to Sentry with event ID: {event_id}")
