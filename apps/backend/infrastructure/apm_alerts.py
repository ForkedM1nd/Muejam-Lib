"""
APM Performance Alerting

This module provides performance alerting functionality for APM.
Implements Requirements 14.7 and 14.8: Alert on performance thresholds.
"""

import os
from typing import Dict, Optional
from infrastructure.apm_config import APMConfig


class PerformanceAlertConfig:
    """
    Configuration for performance alerts.
    
    Implements Requirements:
    - 14.7: Alert when API response times exceed thresholds (p95 > 500ms, p99 > 1000ms)
    - 14.8: Alert when database connection pool utilization exceeds 80%
    """
    
    # Alert Thresholds
    API_P95_THRESHOLD_MS = APMConfig.API_P95_THRESHOLD_MS
    API_P99_THRESHOLD_MS = APMConfig.API_P99_THRESHOLD_MS
    SLOW_QUERY_THRESHOLD_MS = APMConfig.SLOW_QUERY_THRESHOLD_MS
    DB_POOL_UTILIZATION_THRESHOLD = APMConfig.DB_POOL_UTILIZATION_THRESHOLD
    
    # Alert Channels
    ALERT_EMAIL_ENABLED = os.getenv('PERFORMANCE_ALERT_EMAIL_ENABLED', 'True') == 'True'
    ALERT_EMAIL_RECIPIENTS = os.getenv('PERFORMANCE_ALERT_EMAIL_RECIPIENTS', '').split(',')
    ALERT_SLACK_ENABLED = os.getenv('PERFORMANCE_ALERT_SLACK_ENABLED', 'False') == 'True'
    ALERT_SLACK_WEBHOOK_URL = os.getenv('PERFORMANCE_ALERT_SLACK_WEBHOOK_URL', '')
    
    @classmethod
    def get_alert_rules(cls) -> Dict:
        """
        Get performance alert rules for APM configuration.
        
        Returns:
            Dictionary of alert rules
        """
        return {
            'api_response_time': {
                'name': 'API Response Time Alert',
                'description': 'Alert when API response times exceed thresholds',
                'conditions': [
                    {
                        'metric': 'api.endpoint.duration',
                        'aggregation': 'p95',
                        'threshold': cls.API_P95_THRESHOLD_MS,
                        'operator': '>',
                        'window': '5m',
                    },
                    {
                        'metric': 'api.endpoint.duration',
                        'aggregation': 'p99',
                        'threshold': cls.API_P99_THRESHOLD_MS,
                        'operator': '>',
                        'window': '5m',
                    },
                ],
                'severity': 'high',
                'channels': cls._get_alert_channels(),
            },
            'slow_database_queries': {
                'name': 'Slow Database Queries',
                'description': 'Alert when database queries exceed threshold',
                'conditions': [
                    {
                        'metric': 'database.query.slow',
                        'aggregation': 'count',
                        'threshold': 10,
                        'operator': '>',
                        'window': '5m',
                    },
                ],
                'severity': 'medium',
                'channels': cls._get_alert_channels(),
            },
            'database_pool_utilization': {
                'name': 'Database Connection Pool Utilization',
                'description': 'Alert when database pool utilization exceeds 80%',
                'conditions': [
                    {
                        'metric': 'database.pool.utilization',
                        'aggregation': 'avg',
                        'threshold': cls.DB_POOL_UTILIZATION_THRESHOLD,
                        'operator': '>',
                        'window': '5m',
                    },
                ],
                'severity': 'high',
                'channels': cls._get_alert_channels(),
            },
            'external_service_latency': {
                'name': 'External Service Latency',
                'description': 'Alert when external service calls are slow',
                'conditions': [
                    {
                        'metric': 'external.*.duration',
                        'aggregation': 'p95',
                        'threshold': 2000,  # 2 seconds
                        'operator': '>',
                        'window': '5m',
                    },
                ],
                'severity': 'medium',
                'channels': cls._get_alert_channels(),
            },
            'cache_miss_rate': {
                'name': 'High Cache Miss Rate',
                'description': 'Alert when cache miss rate is high',
                'conditions': [
                    {
                        'metric': 'cache.operation',
                        'aggregation': 'miss_rate',
                        'threshold': 0.5,  # 50% miss rate
                        'operator': '>',
                        'window': '10m',
                    },
                ],
                'severity': 'low',
                'channels': cls._get_alert_channels(),
            },
            'celery_queue_depth': {
                'name': 'High Celery Queue Depth',
                'description': 'Alert when Celery queue depth is high',
                'conditions': [
                    {
                        'metric': 'celery.queue.depth',
                        'aggregation': 'max',
                        'threshold': 100,
                        'operator': '>',
                        'window': '5m',
                    },
                ],
                'severity': 'medium',
                'channels': cls._get_alert_channels(),
            },
        }
    
    @classmethod
    def _get_alert_channels(cls) -> list:
        """Get configured alert channels."""
        channels = []
        
        if cls.ALERT_EMAIL_ENABLED and cls.ALERT_EMAIL_RECIPIENTS:
            channels.append({
                'type': 'email',
                'recipients': cls.ALERT_EMAIL_RECIPIENTS,
            })
        
        if cls.ALERT_SLACK_ENABLED and cls.ALERT_SLACK_WEBHOOK_URL:
            channels.append({
                'type': 'slack',
                'webhook_url': cls.ALERT_SLACK_WEBHOOK_URL,
            })
        
        return channels


class PerformanceAlerter:
    """
    Utility class for sending performance alerts.
    """
    
    @staticmethod
    def send_alert(
        alert_name: str,
        metric_name: str,
        current_value: float,
        threshold: float,
        severity: str = 'medium'
    ):
        """
        Send a performance alert.
        
        Args:
            alert_name: Name of the alert
            metric_name: Name of the metric that triggered the alert
            current_value: Current value of the metric
            threshold: Threshold that was exceeded
            severity: Alert severity (low, medium, high, critical)
        """
        if not PerformanceAlertConfig.ALERT_EMAIL_ENABLED and not PerformanceAlertConfig.ALERT_SLACK_ENABLED:
            return
        
        # Send email alert
        if PerformanceAlertConfig.ALERT_EMAIL_ENABLED:
            PerformanceAlerter._send_email_alert(
                alert_name, metric_name, current_value, threshold, severity
            )
        
        # Send Slack alert
        if PerformanceAlertConfig.ALERT_SLACK_ENABLED:
            PerformanceAlerter._send_slack_alert(
                alert_name, metric_name, current_value, threshold, severity
            )
    
    @staticmethod
    def _send_email_alert(
        alert_name: str,
        metric_name: str,
        current_value: float,
        threshold: float,
        severity: str
    ):
        """Send email alert."""
        try:
            from infrastructure.email_service import send_alert_email
            
            subject = f"[{severity.upper()}] Performance Alert: {alert_name}"
            body = f"""
Performance Alert Triggered

Alert: {alert_name}
Metric: {metric_name}
Current Value: {current_value:.2f}
Threshold: {threshold:.2f}
Severity: {severity.upper()}

Please investigate and take appropriate action.
            """
            
            for recipient in PerformanceAlertConfig.ALERT_EMAIL_RECIPIENTS:
                if recipient:
                    send_alert_email(recipient, subject, body)
        
        except Exception as e:
            print(f"Failed to send email alert: {e}")
    
    @staticmethod
    def _send_slack_alert(
        alert_name: str,
        metric_name: str,
        current_value: float,
        threshold: float,
        severity: str
    ):
        """Send Slack alert."""
        try:
            import requests
            
            # Determine color based on severity
            color_map = {
                'low': '#FFA500',      # Orange
                'medium': '#FF8C00',   # Dark Orange
                'high': '#FF4500',     # Red Orange
                'critical': '#FF0000', # Red
            }
            color = color_map.get(severity, '#FFA500')
            
            # Build Slack message
            message = {
                'attachments': [
                    {
                        'color': color,
                        'title': f'{severity.upper()}: {alert_name}',
                        'fields': [
                            {
                                'title': 'Metric',
                                'value': metric_name,
                                'short': True,
                            },
                            {
                                'title': 'Current Value',
                                'value': f'{current_value:.2f}',
                                'short': True,
                            },
                            {
                                'title': 'Threshold',
                                'value': f'{threshold:.2f}',
                                'short': True,
                            },
                            {
                                'title': 'Environment',
                                'value': os.getenv('ENVIRONMENT', 'unknown'),
                                'short': True,
                            },
                        ],
                        'footer': 'MueJam Library Performance Monitoring',
                        'ts': int(__import__('time').time()),
                    }
                ],
            }
            
            # Send to Slack
            response = requests.post(
                PerformanceAlertConfig.ALERT_SLACK_WEBHOOK_URL,
                json=message,
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"Failed to send Slack alert: {response.status_code}")
        
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")


# New Relic Alert Configuration
def configure_newrelic_alerts():
    """
    Configure New Relic alert policies.
    
    This function provides the configuration that should be applied
    in the New Relic dashboard or via API.
    """
    return {
        'policies': [
            {
                'name': 'API Performance',
                'incident_preference': 'PER_CONDITION',
                'conditions': [
                    {
                        'name': 'API Response Time P95 > 500ms',
                        'type': 'apm_app_metric',
                        'metric': 'response_time_web',
                        'condition_scope': 'application',
                        'terms': [
                            {
                                'duration': 5,
                                'operator': 'above',
                                'priority': 'critical',
                                'threshold': 0.5,  # 500ms
                                'time_function': 'all',
                            }
                        ],
                    },
                    {
                        'name': 'API Response Time P99 > 1000ms',
                        'type': 'apm_app_metric',
                        'metric': 'response_time_web',
                        'condition_scope': 'application',
                        'terms': [
                            {
                                'duration': 5,
                                'operator': 'above',
                                'priority': 'critical',
                                'threshold': 1.0,  # 1000ms
                                'time_function': 'all',
                            }
                        ],
                    },
                ],
            },
            {
                'name': 'Database Performance',
                'incident_preference': 'PER_CONDITION',
                'conditions': [
                    {
                        'name': 'Database Pool Utilization > 80%',
                        'type': 'apm_app_metric',
                        'metric': 'database_pool_utilization',
                        'condition_scope': 'application',
                        'terms': [
                            {
                                'duration': 5,
                                'operator': 'above',
                                'priority': 'critical',
                                'threshold': 0.8,
                                'time_function': 'all',
                            }
                        ],
                    },
                ],
            },
        ],
    }


# DataDog Monitor Configuration
def configure_datadog_monitors():
    """
    Configure DataDog monitors.
    
    This function provides the configuration that should be applied
    in the DataDog dashboard or via API.
    """
    return {
        'monitors': [
            {
                'name': 'API Response Time P95 > 500ms',
                'type': 'metric alert',
                'query': 'avg(last_5m):p95:trace.django.request{*} > 500',
                'message': 'API response time P95 exceeded 500ms threshold',
                'tags': ['service:muejam-backend', 'alert:performance'],
                'options': {
                    'thresholds': {
                        'critical': 500,
                        'warning': 400,
                    },
                    'notify_no_data': False,
                    'notify_audit': False,
                },
            },
            {
                'name': 'API Response Time P99 > 1000ms',
                'type': 'metric alert',
                'query': 'avg(last_5m):p99:trace.django.request{*} > 1000',
                'message': 'API response time P99 exceeded 1000ms threshold',
                'tags': ['service:muejam-backend', 'alert:performance'],
                'options': {
                    'thresholds': {
                        'critical': 1000,
                        'warning': 800,
                    },
                    'notify_no_data': False,
                    'notify_audit': False,
                },
            },
            {
                'name': 'Database Pool Utilization > 80%',
                'type': 'metric alert',
                'query': 'avg(last_5m):database.pool.utilization{*} > 0.8',
                'message': 'Database connection pool utilization exceeded 80%',
                'tags': ['service:muejam-backend', 'alert:database'],
                'options': {
                    'thresholds': {
                        'critical': 0.8,
                        'warning': 0.7,
                    },
                    'notify_no_data': False,
                    'notify_audit': False,
                },
            },
        ],
    }


# Export public API
__all__ = [
    'PerformanceAlertConfig',
    'PerformanceAlerter',
    'configure_newrelic_alerts',
    'configure_datadog_monitors',
]
