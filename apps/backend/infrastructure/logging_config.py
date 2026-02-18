"""
Structured Logging Configuration

This module provides structured JSON logging for the MueJam Library platform.
Implements Requirements 15.1-15.12 from production-readiness spec.

Features:
- JSON-formatted structured logging
- Automatic request context injection
- PII redaction
- CloudWatch Logs integration
- Log-based alerting support
"""

import os
import re
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from functools import wraps


class PIIRedactor:
    """
    Redacts sensitive data from log messages.
    
    Implements Requirement 15.10: Redact sensitive data from logs.
    """
    
    # Regex patterns for PII detection
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b')
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b')
    
    # Sensitive field names to redact
    SENSITIVE_FIELDS = {
        'password', 'token', 'secret', 'api_key', 'authorization',
        'credit_card', 'ssn', 'social_security', 'access_token',
        'refresh_token', 'private_key', 'secret_key'
    }
    
    @classmethod
    def redact_text(cls, text: str) -> str:
        """
        Redact PII from text content.
        
        Args:
            text: Text to redact
            
        Returns:
            Redacted text
        """
        if not isinstance(text, str):
            return text
        
        # Redact email addresses
        text = cls.EMAIL_PATTERN.sub('[EMAIL_REDACTED]', text)
        
        # Redact phone numbers
        text = cls.PHONE_PATTERN.sub('[PHONE_REDACTED]', text)
        
        # Redact SSN
        text = cls.SSN_PATTERN.sub('[SSN_REDACTED]', text)
        
        # Redact credit card numbers
        text = cls.CREDIT_CARD_PATTERN.sub('[CARD_REDACTED]', text)
        
        return text
    
    @classmethod
    def redact_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact sensitive fields from dictionary.
        
        Args:
            data: Dictionary to redact
            
        Returns:
            Redacted dictionary
        """
        if not isinstance(data, dict):
            return data
        
        redacted = {}
        for key, value in data.items():
            # Check if field name is sensitive
            if any(sensitive in key.lower() for sensitive in cls.SENSITIVE_FIELDS):
                redacted[key] = '[REDACTED]'
            elif isinstance(value, dict):
                redacted[key] = cls.redact_dict(value)
            elif isinstance(value, list):
                redacted[key] = [cls.redact_dict(item) if isinstance(item, dict) else cls.redact_text(str(item)) for item in value]
            elif isinstance(value, str):
                redacted[key] = cls.redact_text(value)
            else:
                redacted[key] = value
        
        return redacted


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.
    
    Implements Requirement 15.1: Use structured logging with JSON format.
    Implements Requirement 15.2: Include standard fields in each log entry.
    """
    
    def __init__(self, service_name: str = 'muejam-backend'):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        # Base log entry (Requirement 15.2)
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat() + 'Z',
            'level': record.levelname,
            'service': self.service_name,
            'message': record.getMessage(),
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info),
            }
        
        # Redact sensitive data (Requirement 15.10)
        log_entry = PIIRedactor.redact_dict(log_entry)
        
        return json.dumps(log_entry)


class StructuredLogger:
    """
    Structured logging helper with automatic context injection.
    
    Implements Requirement 15.2: Add request context automatically.
    """
    
    def __init__(self, name: str):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (usually __name__)
        """
        self.logger = logging.getLogger(name)
        self._context = {}
    
    def set_context(self, **kwargs):
        """
        Set context fields for all subsequent log entries.
        
        Args:
            **kwargs: Context fields to set
        """
        self._context.update(kwargs)
    
    def clear_context(self):
        """Clear all context fields."""
        self._context = {}
    
    def _log(self, level: int, message: str, **kwargs):
        """
        Internal log method with context injection.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional fields
        """
        extra_fields = {**self._context, **kwargs}
        
        # Create log record with extra fields
        extra = {'extra_fields': extra_fields}
        
        # Add request context if available
        if 'request_id' in extra_fields:
            extra['request_id'] = extra_fields.pop('request_id')
        if 'user_id' in extra_fields:
            extra['user_id'] = extra_fields.pop('user_id')
        if 'ip_address' in extra_fields:
            extra['ip_address'] = extra_fields.pop('ip_address')
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, extra={'extra_fields': {**self._context, **kwargs}})


class LoggingConfig:
    """
    Logging configuration for Django application.
    
    Implements Requirements 15.1-15.12.
    """
    
    # Environment Configuration
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    SERVICE_NAME = os.getenv('SERVICE_NAME', 'muejam-backend')
    
    # CloudWatch Logs Configuration (Requirement 15.7)
    CLOUDWATCH_ENABLED = os.getenv('CLOUDWATCH_LOGS_ENABLED', 'False') == 'True'
    CLOUDWATCH_LOG_GROUP = os.getenv('CLOUDWATCH_LOG_GROUP', '/muejam/backend')
    CLOUDWATCH_LOG_STREAM = os.getenv('CLOUDWATCH_LOG_STREAM', f'{ENVIRONMENT}-{SERVICE_NAME}')
    CLOUDWATCH_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # Log Retention Configuration (Requirement 15.8)
    LOG_RETENTION_DAYS_HOT = int(os.getenv('LOG_RETENTION_DAYS_HOT', '90'))
    LOG_RETENTION_DAYS_COLD = int(os.getenv('LOG_RETENTION_DAYS_COLD', '365'))
    
    # Log Volume Alerting (Requirement 15.12)
    LOG_VOLUME_ALERT_THRESHOLD = int(os.getenv('LOG_VOLUME_ALERT_THRESHOLD', '10000'))  # logs per minute
    LOG_VOLUME_CHECK_INTERVAL = int(os.getenv('LOG_VOLUME_CHECK_INTERVAL', '60'))  # seconds
    
    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        """
        Get Django LOGGING configuration dictionary.
        
        Returns:
            Django LOGGING configuration
        """
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'json': {
                    '()': 'infrastructure.logging_config.JSONFormatter',
                    'service_name': cls.SERVICE_NAME,
                },
                'console': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                },
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'json' if cls.ENVIRONMENT == 'production' else 'console',
                    'level': cls.LOG_LEVEL,
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': 'logs/muejam.log',
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 10,
                    'formatter': 'json',
                    'level': cls.LOG_LEVEL,
                },
            },
            'loggers': {
                'django': {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': False,
                },
                'django.request': {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': False,
                },
                'django.db.backends': {
                    'handlers': ['console', 'file'],
                    'level': 'WARNING',  # Only log slow queries and errors
                    'propagate': False,
                },
                'apps': {
                    'handlers': ['console', 'file'],
                    'level': cls.LOG_LEVEL,
                    'propagate': False,
                },
                'infrastructure': {
                    'handlers': ['console', 'file'],
                    'level': cls.LOG_LEVEL,
                    'propagate': False,
                },
            },
            'root': {
                'handlers': ['console', 'file'],
                'level': cls.LOG_LEVEL,
            },
        }
        
        # Add CloudWatch handler if enabled (Requirement 15.7)
        if cls.CLOUDWATCH_ENABLED:
            try:
                import watchtower
                
                config['handlers']['cloudwatch'] = {
                    'class': 'watchtower.CloudWatchLogHandler',
                    'log_group': cls.CLOUDWATCH_LOG_GROUP,
                    'stream_name': cls.CLOUDWATCH_LOG_STREAM,
                    'formatter': 'json',
                    'level': cls.LOG_LEVEL,
                }
                
                # Add CloudWatch handler to all loggers
                for logger_config in config['loggers'].values():
                    if 'cloudwatch' not in logger_config['handlers']:
                        logger_config['handlers'].append('cloudwatch')
                
                config['root']['handlers'].append('cloudwatch')
                
            except ImportError:
                pass  # watchtower not installed
        
        return config


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)


def log_api_request(logger: StructuredLogger, method: str, path: str, status_code: int, 
                   response_time_ms: float, user_agent: str, user_id: Optional[str] = None):
    """
    Log API request.
    
    Implements Requirement 15.3: Log all API requests.
    
    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        status_code: Response status code
        response_time_ms: Response time in milliseconds
        user_agent: User agent string
        user_id: User ID if authenticated
    """
    logger.info(
        'API request',
        event_type='api_request',
        method=method,
        path=path,
        status_code=status_code,
        response_time_ms=response_time_ms,
        user_agent=user_agent,
        user_id=user_id,
    )


def log_authentication_event(logger: StructuredLogger, event_type: str, user_id: Optional[str] = None,
                            success: bool = True, reason: Optional[str] = None):
    """
    Log authentication event.
    
    Implements Requirement 15.4: Log all authentication events.
    
    Args:
        logger: Logger instance
        event_type: Type of auth event (login, logout, token_refresh, etc.)
        user_id: User ID
        success: Whether the event succeeded
        reason: Failure reason if applicable
    """
    logger.info(
        f'Authentication event: {event_type}',
        event_type='authentication',
        auth_event_type=event_type,
        user_id=user_id,
        success=success,
        reason=reason,
    )


def log_moderation_action(logger: StructuredLogger, moderator_id: str, action_type: str,
                         content_id: str, reason: str):
    """
    Log moderation action.
    
    Implements Requirement 15.5: Log all moderation actions.
    
    Args:
        logger: Logger instance
        moderator_id: Moderator user ID
        action_type: Type of moderation action
        content_id: Content ID
        reason: Reason for action
    """
    logger.info(
        f'Moderation action: {action_type}',
        event_type='moderation',
        moderator_id=moderator_id,
        action_type=action_type,
        content_id=content_id,
        reason=reason,
    )


def log_rate_limit_event(logger: StructuredLogger, ip_address: str, endpoint: str,
                        limit_type: str, limit_exceeded: str):
    """
    Log rate limiting event.
    
    Implements Requirement 15.6: Log all rate limiting events.
    
    Args:
        logger: Logger instance
        ip_address: Client IP address
        endpoint: API endpoint
        limit_type: Type of rate limit (ip, user, endpoint)
        limit_exceeded: Limit that was exceeded
    """
    logger.warning(
        f'Rate limit exceeded: {limit_exceeded}',
        event_type='rate_limit',
        ip_address=ip_address,
        endpoint=endpoint,
        limit_type=limit_type,
        limit_exceeded=limit_exceeded,
    )


# Export public API
__all__ = [
    'LoggingConfig',
    'StructuredLogger',
    'JSONFormatter',
    'PIIRedactor',
    'get_logger',
    'log_api_request',
    'log_authentication_event',
    'log_moderation_action',
    'log_rate_limit_event',
]
