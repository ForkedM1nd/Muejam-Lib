"""
Sentry Alert Configuration

This module provides configuration and utilities for Sentry error grouping and alerting.
Implements Requirements 13.4, 13.5, 13.12 from production-readiness spec.

Features:
- Error grouping rules
- Email alert configuration
- Slack integration for notifications
- Alert thresholds and rules
"""

import os
from typing import Dict, List, Optional


class SentryAlertConfig:
    """
    Configuration for Sentry alerts and notifications.
    
    This class defines alert rules, thresholds, and notification channels
    for critical errors in the application.
    """
    
    # Alert Thresholds
    CRITICAL_ERROR_THRESHOLD = int(os.getenv('SENTRY_CRITICAL_ERROR_THRESHOLD', '10'))
    ERROR_RATE_THRESHOLD = float(os.getenv('SENTRY_ERROR_RATE_THRESHOLD', '0.01'))  # 1%
    
    # Email Alert Configuration (Requirement 13.5)
    EMAIL_ALERTS_ENABLED = os.getenv('SENTRY_EMAIL_ALERTS_ENABLED', 'True') == 'True'
    ALERT_EMAIL_RECIPIENTS = os.getenv('SENTRY_ALERT_EMAIL_RECIPIENTS', '').split(',')
    
    # Slack Integration Configuration (Requirement 13.12)
    SLACK_WEBHOOK_URL = os.getenv('SENTRY_SLACK_WEBHOOK_URL', '')
    SLACK_ALERTS_ENABLED = os.getenv('SENTRY_SLACK_ALERTS_ENABLED', 'False') == 'True'
    SLACK_CHANNEL = os.getenv('SENTRY_SLACK_CHANNEL', '#engineering-alerts')
    
    # Error Grouping Rules (Requirement 13.4)
    # These rules help Sentry group similar errors together
    ERROR_GROUPING_RULES = {
        # Group database errors by query type
        'database': {
            'fingerprint': ['{{ default }}', 'database', '{{ transaction }}'],
            'patterns': [
                'psycopg',
                'DatabaseError',
                'OperationalError',
                'IntegrityError',
            ]
        },
        
        # Group authentication errors
        'authentication': {
            'fingerprint': ['{{ default }}', 'auth', '{{ function }}'],
            'patterns': [
                'AuthenticationFailed',
                'PermissionDenied',
                'InvalidToken',
                'clerk',
            ]
        },
        
        # Group external service errors
        'external_service': {
            'fingerprint': ['{{ default }}', 'external', '{{ function }}'],
            'patterns': [
                'ConnectionError',
                'Timeout',
                'HTTPError',
                'RequestException',
                'boto3',
                'resend',
            ]
        },
        
        # Group rate limiting errors
        'rate_limit': {
            'fingerprint': ['{{ default }}', 'rate_limit', '{{ endpoint }}'],
            'patterns': [
                'Ratelimited',
                'TooManyRequests',
                '429',
            ]
        },
        
        # Group validation errors
        'validation': {
            'fingerprint': ['{{ default }}', 'validation', '{{ function }}'],
            'patterns': [
                'ValidationError',
                'SerializerError',
                'InvalidInput',
            ]
        },
    }
    
    # Critical Error Patterns
    # Errors matching these patterns trigger immediate alerts
    CRITICAL_ERROR_PATTERNS = [
        'DatabaseError',
        'OperationalError',
        'ConnectionError',
        'OutOfMemory',
        'DiskFull',
        'SecurityError',
        'DataLoss',
    ]
    
    # Ignored Error Patterns
    # These errors are expected and should not trigger alerts
    IGNORED_ERROR_PATTERNS = [
        'Http404',
        'NotFound',
        'PermissionDenied',
        'AuthenticationFailed',
    ]
    
    @classmethod
    def get_alert_rules(cls) -> List[Dict]:
        """
        Get alert rules for Sentry configuration.
        
        Returns:
            List of alert rule configurations
        """
        rules = []
        
        # Critical error alert
        if cls.EMAIL_ALERTS_ENABLED or cls.SLACK_ALERTS_ENABLED:
            rules.append({
                'name': 'Critical Errors',
                'conditions': [
                    {
                        'id': 'sentry.rules.conditions.event_attribute.EventAttributeCondition',
                        'attribute': 'level',
                        'match': 'eq',
                        'value': 'error',
                    },
                    {
                        'id': 'sentry.rules.conditions.tagged_event.TaggedEventCondition',
                        'key': 'severity',
                        'match': 'eq',
                        'value': 'critical',
                    },
                ],
                'actions': cls._get_alert_actions(),
                'frequency': 5,  # Alert every 5 minutes
            })
        
        # High error rate alert
        if cls.EMAIL_ALERTS_ENABLED or cls.SLACK_ALERTS_ENABLED:
            rules.append({
                'name': 'High Error Rate',
                'conditions': [
                    {
                        'id': 'sentry.rules.conditions.event_frequency.EventFrequencyCondition',
                        'value': cls.CRITICAL_ERROR_THRESHOLD,
                        'interval': '1m',
                    },
                ],
                'actions': cls._get_alert_actions(),
                'frequency': 30,  # Alert every 30 minutes
            })
        
        return rules
    
    @classmethod
    def _get_alert_actions(cls) -> List[Dict]:
        """
        Get alert actions based on enabled notification channels.
        
        Returns:
            List of alert action configurations
        """
        actions = []
        
        # Email notifications
        if cls.EMAIL_ALERTS_ENABLED and cls.ALERT_EMAIL_RECIPIENTS:
            actions.append({
                'id': 'sentry.mail.actions.NotifyEmailAction',
                'targetType': 'Member',
                'targetIdentifier': cls.ALERT_EMAIL_RECIPIENTS,
            })
        
        # Slack notifications
        if cls.SLACK_ALERTS_ENABLED and cls.SLACK_WEBHOOK_URL:
            actions.append({
                'id': 'sentry.integrations.slack.notify_action.SlackNotifyServiceAction',
                'workspace': cls.SLACK_WEBHOOK_URL,
                'channel': cls.SLACK_CHANNEL,
            })
        
        return actions
    
    @classmethod
    def should_alert(cls, error_type: str, error_count: int = 1) -> bool:
        """
        Determine if an error should trigger an alert.
        
        Args:
            error_type: Type or message of the error
            error_count: Number of occurrences
        
        Returns:
            True if alert should be triggered
        """
        # Check if error is in ignored patterns
        for pattern in cls.IGNORED_ERROR_PATTERNS:
            if pattern.lower() in error_type.lower():
                return False
        
        # Check if error is critical
        for pattern in cls.CRITICAL_ERROR_PATTERNS:
            if pattern.lower() in error_type.lower():
                return True
        
        # Check if error count exceeds threshold
        if error_count >= cls.CRITICAL_ERROR_THRESHOLD:
            return True
        
        return False


class SlackNotifier:
    """
    Utility class for sending Slack notifications about errors.
    
    Implements Requirement 13.12: Slack integration for error notifications.
    """
    
    def __init__(self):
        self.webhook_url = SentryAlertConfig.SLACK_WEBHOOK_URL
        self.enabled = SentryAlertConfig.SLACK_ALERTS_ENABLED
        self.channel = SentryAlertConfig.SLACK_CHANNEL
    
    def send_error_notification(
        self,
        error_message: str,
        error_type: str,
        error_count: int,
        sentry_url: Optional[str] = None
    ) -> bool:
        """
        Send error notification to Slack.
        
        Args:
            error_message: Error message
            error_type: Type of error
            error_count: Number of occurrences
            sentry_url: URL to Sentry issue
        
        Returns:
            True if notification sent successfully
        """
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            import requests
            
            # Determine severity color
            if error_count >= SentryAlertConfig.CRITICAL_ERROR_THRESHOLD:
                color = '#FF0000'  # Red for critical
                severity = 'CRITICAL'
            else:
                color = '#FFA500'  # Orange for warning
                severity = 'WARNING'
            
            # Build Slack message
            message = {
                'channel': self.channel,
                'username': 'Sentry Error Bot',
                'icon_emoji': ':rotating_light:',
                'attachments': [
                    {
                        'color': color,
                        'title': f'{severity}: {error_type}',
                        'text': error_message,
                        'fields': [
                            {
                                'title': 'Occurrences',
                                'value': str(error_count),
                                'short': True,
                            },
                            {
                                'title': 'Environment',
                                'value': os.getenv('SENTRY_ENVIRONMENT', 'unknown'),
                                'short': True,
                            },
                        ],
                        'footer': 'MueJam Library Error Tracking',
                        'ts': int(__import__('time').time()),
                    }
                ],
            }
            
            # Add Sentry link if available
            if sentry_url:
                message['attachments'][0]['actions'] = [
                    {
                        'type': 'button',
                        'text': 'View in Sentry',
                        'url': sentry_url,
                    }
                ]
            
            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=5
            )
            
            return response.status_code == 200
            
        except Exception as e:
            # Don't let Slack notification failures break the application
            print(f"Failed to send Slack notification: {e}")
            return False


# Export configuration
__all__ = [
    'SentryAlertConfig',
    'SlackNotifier',
]
