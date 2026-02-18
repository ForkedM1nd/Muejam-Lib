"""
Sentry Error Tracking Configuration

This module initializes Sentry for error tracking and monitoring.
Implements Requirements 13.1, 13.2, 13.6 from production-readiness spec.

Features:
- Django, Celery, and Redis integrations
- Sensitive data scrubbing (passwords, tokens, PII)
- Performance monitoring with configurable sample rates
- Environment and release tracking
"""

import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration


def scrub_sensitive_data(event, hint):
    """
    Remove sensitive data from error reports before sending to Sentry.
    
    Implements Requirement 13.6: Redact sensitive data from error reports.
    
    Scrubs:
    - Authorization headers
    - API keys
    - Password fields
    - Tokens
    - Session cookies
    
    Args:
        event: Sentry event dictionary
        hint: Additional context about the event
    
    Returns:
        Modified event with sensitive data removed
    """
    # Scrub request headers
    if 'request' in event:
        if 'headers' in event['request']:
            # Remove authorization headers
            event['request']['headers'].pop('Authorization', None)
            event['request']['headers'].pop('X-API-Key', None)
            event['request']['headers'].pop('Cookie', None)
            event['request']['headers'].pop('Set-Cookie', None)
        
        # Scrub request data
        if 'data' in event['request']:
            if isinstance(event['request']['data'], dict):
                # Remove password fields
                event['request']['data'].pop('password', None)
                event['request']['data'].pop('old_password', None)
                event['request']['data'].pop('new_password', None)
                event['request']['data'].pop('password_confirmation', None)
                
                # Remove token fields
                event['request']['data'].pop('token', None)
                event['request']['data'].pop('access_token', None)
                event['request']['data'].pop('refresh_token', None)
                event['request']['data'].pop('api_key', None)
                
                # Remove sensitive user data
                event['request']['data'].pop('ssn', None)
                event['request']['data'].pop('credit_card', None)
                event['request']['data'].pop('cvv', None)
        
        # Scrub query parameters
        if 'query_string' in event['request']:
            # Remove sensitive query params
            event['request']['query_string'] = event['request']['query_string'].replace(
                'password=', 'password=[REDACTED]&'
            ).replace(
                'token=', 'token=[REDACTED]&'
            ).replace(
                'api_key=', 'api_key=[REDACTED]&'
            )
    
    # Scrub user context
    if 'user' in event:
        # Keep user ID but remove email and IP for privacy
        if 'email' in event['user']:
            event['user']['email'] = '[REDACTED]'
        if 'ip_address' in event['user']:
            event['user']['ip_address'] = '[REDACTED]'
    
    return event


def scrub_breadcrumb_data(crumb, hint):
    """
    Remove sensitive data from breadcrumbs.
    
    Breadcrumbs show user actions leading to errors.
    This function ensures no sensitive data is included.
    
    Args:
        crumb: Breadcrumb dictionary
        hint: Additional context
    
    Returns:
        Modified breadcrumb with sensitive data removed
    """
    if crumb.get('category') == 'http':
        # Scrub HTTP request breadcrumbs
        if 'data' in crumb:
            if isinstance(crumb['data'], dict):
                crumb['data'].pop('Authorization', None)
                crumb['data'].pop('Cookie', None)
    
    return crumb


def init_sentry():
    """
    Initialize Sentry SDK with Django, Celery, and Redis integrations.
    
    Implements Requirements:
    - 13.1: Integrate Sentry for error tracking
    - 13.2: Send error details including stack trace, user context, request data
    - 13.6: Redact sensitive data from error reports
    
    Configuration via environment variables:
    - SENTRY_DSN: Sentry project DSN (required)
    - SENTRY_ENVIRONMENT: Environment name (e.g., production, staging, development)
    - SENTRY_TRACES_SAMPLE_RATE: Percentage of transactions to trace (0.0 to 1.0)
    - SENTRY_PROFILES_SAMPLE_RATE: Percentage of transactions to profile (0.0 to 1.0)
    - APP_VERSION: Application version for release tracking
    """
    sentry_dsn = os.getenv('SENTRY_DSN', '')
    
    # Only initialize if DSN is configured
    if not sentry_dsn:
        return
    
    # Get configuration from environment
    environment = os.getenv('SENTRY_ENVIRONMENT', os.getenv('ENVIRONMENT', 'development'))
    traces_sample_rate = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1'))
    profiles_sample_rate = float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.1'))
    release = os.getenv('APP_VERSION', os.getenv('VERSION', 'unknown'))
    
    sentry_sdk.init(
        dsn=sentry_dsn,
        
        # Integrations for Django, Celery, and Redis
        integrations=[
            DjangoIntegration(
                transaction_style='url',  # Use URL patterns for transaction names
                middleware_spans=True,  # Track middleware execution
                signals_spans=True,  # Track Django signals
            ),
            CeleryIntegration(
                monitor_beat_tasks=True,  # Monitor Celery beat tasks
                exclude_beat_tasks=None,  # Don't exclude any beat tasks
            ),
            RedisIntegration(),
        ],
        
        # Performance monitoring
        traces_sample_rate=traces_sample_rate,  # 10% of transactions by default
        profiles_sample_rate=profiles_sample_rate,  # 10% of transactions by default
        
        # Environment and release tracking
        environment=environment,
        release=f"muejam-backend@{release}",
        
        # Sensitive data scrubbing
        before_send=scrub_sensitive_data,
        before_breadcrumb=scrub_breadcrumb_data,
        
        # Additional options
        send_default_pii=False,  # Don't send PII by default
        attach_stacktrace=True,  # Always attach stack traces
        max_breadcrumbs=50,  # Keep last 50 breadcrumbs
        
        # Error filtering
        ignore_errors=[
            # Ignore common non-critical errors
            'django.http.Http404',
            'rest_framework.exceptions.NotFound',
            'rest_framework.exceptions.PermissionDenied',
        ],
    )


class ErrorTracker:
    """
    Helper class for capturing errors and messages in Sentry.
    
    Provides convenient methods for error tracking with custom context.
    """
    
    @staticmethod
    def capture_exception(exception, context=None, level='error'):
        """
        Capture an exception with optional custom context.
        
        Args:
            exception: The exception to capture
            context: Dictionary of additional context to include
            level: Error level (error, warning, info)
        """
        with sentry_sdk.push_scope() as scope:
            # Set error level
            scope.level = level
            
            # Add custom context
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            
            sentry_sdk.capture_exception(exception)
    
    @staticmethod
    def capture_message(message, level='info', context=None):
        """
        Capture a message with optional custom context.
        
        Args:
            message: The message to capture
            level: Message level (info, warning, error)
            context: Dictionary of additional context to include
        """
        with sentry_sdk.push_scope() as scope:
            # Set message level
            scope.level = level
            
            # Add custom context
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            
            sentry_sdk.capture_message(message, level=level)
    
    @staticmethod
    def set_user(user_id, email=None, username=None):
        """
        Set user context for error tracking.
        
        Args:
            user_id: User ID
            email: User email (will be redacted in before_send)
            username: Username
        """
        sentry_sdk.set_user({
            'id': str(user_id),
            'email': email,
            'username': username,
        })
    
    @staticmethod
    def set_tag(key, value):
        """
        Set a tag for filtering errors in Sentry.
        
        Args:
            key: Tag key
            value: Tag value
        """
        sentry_sdk.set_tag(key, value)
    
    @staticmethod
    def set_context(name, context):
        """
        Set custom context for error tracking.
        
        Args:
            name: Context name
            context: Dictionary of context data
        """
        sentry_sdk.set_context(name, context)
