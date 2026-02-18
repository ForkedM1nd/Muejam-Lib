"""
Application Performance Monitoring (APM) Configuration

This module provides APM integration for performance monitoring.
Supports both New Relic and DataDog APM solutions.
Implements Requirements 14.1-14.12 from production-readiness spec.

Features:
- API endpoint performance tracking
- Database query performance monitoring
- External service call tracking
- Cache performance metrics
- Celery task monitoring
- Custom business metrics
- Performance alerts
"""

import os
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps


class APMProvider:
    """Base class for APM providers."""
    
    def __init__(self):
        self.enabled = False
    
    def record_custom_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a custom metric."""
        raise NotImplementedError
    
    def record_transaction(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Record a transaction."""
        raise NotImplementedError
    
    def start_transaction(self, name: str, transaction_type: str = 'web'):
        """Start a transaction."""
        raise NotImplementedError
    
    def end_transaction(self):
        """End the current transaction."""
        raise NotImplementedError
    
    def record_exception(self, exception: Exception):
        """Record an exception."""
        raise NotImplementedError


class NewRelicProvider(APMProvider):
    """New Relic APM provider."""
    
    def __init__(self):
        super().__init__()
        try:
            import newrelic.agent
            self.agent = newrelic.agent
            self.enabled = True
        except ImportError:
            self.agent = None
            self.enabled = False
    
    def record_custom_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a custom metric in New Relic."""
        if not self.enabled:
            return
        
        metric_name = f"Custom/{name}"
        self.agent.record_custom_metric(metric_name, value)
    
    def record_transaction(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Record a transaction in New Relic."""
        if not self.enabled:
            return
        
        self.agent.record_custom_event('Transaction', {
            'name': name,
            'duration': duration,
            **(tags or {})
        })
    
    def start_transaction(self, name: str, transaction_type: str = 'web'):
        """Start a New Relic transaction."""
        if not self.enabled:
            return None
        
        return self.agent.current_transaction()
    
    def end_transaction(self):
        """End the current New Relic transaction."""
        if not self.enabled:
            return
        
        # New Relic handles transaction ending automatically
        pass
    
    def record_exception(self, exception: Exception):
        """Record an exception in New Relic."""
        if not self.enabled:
            return
        
        self.agent.notice_error()


class DataDogProvider(APMProvider):
    """DataDog APM provider."""
    
    def __init__(self):
        super().__init__()
        try:
            from ddtrace import tracer
            import ddtrace
            self.tracer = tracer
            self.ddtrace = ddtrace
            self.enabled = True
        except ImportError:
            self.tracer = None
            self.ddtrace = None
            self.enabled = False
    
    def record_custom_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a custom metric in DataDog."""
        if not self.enabled:
            return
        
        try:
            from datadog import statsd
            tag_list = [f"{k}:{v}" for k, v in (tags or {}).items()]
            statsd.gauge(name, value, tags=tag_list)
        except ImportError:
            pass
    
    def record_transaction(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Record a transaction in DataDog."""
        if not self.enabled:
            return
        
        span = self.tracer.current_span()
        if span:
            span.set_tag('transaction.name', name)
            span.set_tag('transaction.duration', duration)
            if tags:
                for key, value in tags.items():
                    span.set_tag(key, value)
    
    def start_transaction(self, name: str, transaction_type: str = 'web'):
        """Start a DataDog transaction."""
        if not self.enabled:
            return None
        
        return self.tracer.trace(name, service='muejam-backend', resource=name)
    
    def end_transaction(self):
        """End the current DataDog transaction."""
        if not self.enabled:
            return
        
        span = self.tracer.current_span()
        if span:
            span.finish()
    
    def record_exception(self, exception: Exception):
        """Record an exception in DataDog."""
        if not self.enabled:
            return
        
        span = self.tracer.current_span()
        if span:
            span.set_exc_info(type(exception), exception, exception.__traceback__)


class APMConfig:
    """
    APM configuration and initialization.
    
    Supports both New Relic and DataDog APM providers.
    """
    
    # APM Provider Selection
    APM_PROVIDER = os.getenv('APM_PROVIDER', 'newrelic').lower()  # 'newrelic' or 'datadog'
    APM_ENABLED = os.getenv('APM_ENABLED', 'False') == 'True'
    
    # New Relic Configuration
    NEW_RELIC_LICENSE_KEY = os.getenv('NEW_RELIC_LICENSE_KEY', '')
    NEW_RELIC_APP_NAME = os.getenv('NEW_RELIC_APP_NAME', 'MueJam Library')
    NEW_RELIC_ENVIRONMENT = os.getenv('NEW_RELIC_ENVIRONMENT', os.getenv('ENVIRONMENT', 'development'))
    
    # DataDog Configuration
    DATADOG_API_KEY = os.getenv('DATADOG_API_KEY', '')
    DATADOG_APP_KEY = os.getenv('DATADOG_APP_KEY', '')
    DATADOG_SERVICE_NAME = os.getenv('DATADOG_SERVICE_NAME', 'muejam-backend')
    DATADOG_ENVIRONMENT = os.getenv('DATADOG_ENVIRONMENT', os.getenv('ENVIRONMENT', 'development'))
    
    # Performance Thresholds (Requirements 14.7, 14.8)
    API_P95_THRESHOLD_MS = int(os.getenv('API_P95_THRESHOLD_MS', '500'))
    API_P99_THRESHOLD_MS = int(os.getenv('API_P99_THRESHOLD_MS', '1000'))
    SLOW_QUERY_THRESHOLD_MS = int(os.getenv('SLOW_QUERY_THRESHOLD_MS', '100'))
    DB_POOL_UTILIZATION_THRESHOLD = float(os.getenv('DB_POOL_UTILIZATION_THRESHOLD', '0.8'))
    
    # Transaction Tracing
    TRANSACTION_TRACE_ENABLED = os.getenv('TRANSACTION_TRACE_ENABLED', 'True') == 'True'
    SLOW_SQL_ENABLED = os.getenv('SLOW_SQL_ENABLED', 'True') == 'True'
    
    _provider: Optional[APMProvider] = None
    
    @classmethod
    def get_provider(cls) -> APMProvider:
        """
        Get the configured APM provider.
        
        Returns:
            APM provider instance (New Relic or DataDog)
        """
        if cls._provider is None:
            if cls.APM_PROVIDER == 'newrelic':
                cls._provider = NewRelicProvider()
            elif cls.APM_PROVIDER == 'datadog':
                cls._provider = DataDogProvider()
            else:
                # Default to New Relic
                cls._provider = NewRelicProvider()
        
        return cls._provider
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if APM is enabled."""
        return cls.APM_ENABLED and cls.get_provider().enabled


def init_newrelic():
    """
    Initialize New Relic APM.
    
    Implements Requirement 14.1: Integrate APM solution.
    """
    if APMConfig.APM_PROVIDER != 'newrelic' or not APMConfig.APM_ENABLED:
        return
    
    if not APMConfig.NEW_RELIC_LICENSE_KEY:
        return
    
    try:
        import newrelic.agent
        
        # Configure New Relic
        settings = newrelic.agent.global_settings()
        settings.license_key = APMConfig.NEW_RELIC_LICENSE_KEY
        settings.app_name = APMConfig.NEW_RELIC_APP_NAME
        settings.monitor_mode = True
        settings.log_level = 'info'
        
        # Transaction tracing (Requirement 14.1)
        settings.transaction_tracer.enabled = APMConfig.TRANSACTION_TRACE_ENABLED
        settings.transaction_tracer.transaction_threshold = 'apdex_f'
        settings.transaction_tracer.record_sql = 'obfuscated'
        settings.transaction_tracer.stack_trace_threshold = 0.5
        
        # Slow SQL detection (Requirement 14.3)
        settings.slow_sql.enabled = APMConfig.SLOW_SQL_ENABLED
        
        # Error collection
        settings.error_collector.enabled = True
        settings.error_collector.ignore_errors = ['django.http:Http404']
        
        # Browser monitoring
        settings.browser_monitoring.auto_instrument = True
        
        # Initialize agent
        newrelic.agent.initialize()
        
    except ImportError:
        pass


def init_datadog():
    """
    Initialize DataDog APM.
    
    Implements Requirement 14.1: Integrate APM solution.
    """
    if APMConfig.APM_PROVIDER != 'datadog' or not APMConfig.APM_ENABLED:
        return
    
    if not APMConfig.DATADOG_API_KEY:
        return
    
    try:
        from ddtrace import patch_all, config
        
        # Patch all supported libraries
        patch_all()
        
        # Configure DataDog
        config.django['service_name'] = APMConfig.DATADOG_SERVICE_NAME
        config.django['trace_query_string'] = True
        config.env = APMConfig.DATADOG_ENVIRONMENT
        
        # Database tracing (Requirement 14.3)
        config.psycopg['service_name'] = f"{APMConfig.DATADOG_SERVICE_NAME}-postgres"
        
        # Redis tracing (Requirement 14.5)
        config.redis['service_name'] = f"{APMConfig.DATADOG_SERVICE_NAME}-redis"
        
        # Celery tracing (Requirement 14.6)
        config.celery['service_name'] = f"{APMConfig.DATADOG_SERVICE_NAME}-celery"
        
    except ImportError:
        pass


class PerformanceMonitor:
    """
    Performance monitoring utilities.
    
    Provides methods for tracking various performance metrics.
    Implements Requirements 14.2-14.6, 14.10.
    """
    
    @staticmethod
    def track_api_endpoint(endpoint: str, method: str, status_code: int, duration_ms: float):
        """
        Track API endpoint performance.
        
        Implements Requirement 14.2: Track API endpoint performance.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: Response status code
            duration_ms: Request duration in milliseconds
        """
        provider = APMConfig.get_provider()
        if not provider.enabled:
            return
        
        provider.record_custom_metric(
            'api.endpoint.duration',
            duration_ms,
            tags={
                'endpoint': endpoint,
                'method': method,
                'status_code': str(status_code),
            }
        )
        
        # Alert if threshold exceeded (Requirement 14.7)
        if duration_ms > APMConfig.API_P99_THRESHOLD_MS:
            provider.record_custom_metric(
                'api.endpoint.slow',
                1,
                tags={'endpoint': endpoint, 'threshold': 'p99'}
            )
    
    @staticmethod
    def track_database_query(query: str, duration_ms: float, rows_returned: int = 0):
        """
        Track database query performance.
        
        Implements Requirement 14.3: Track database query performance.
        
        Args:
            query: SQL query (obfuscated)
            duration_ms: Query duration in milliseconds
            rows_returned: Number of rows returned
        """
        provider = APMConfig.get_provider()
        if not provider.enabled:
            return
        
        provider.record_custom_metric(
            'database.query.duration',
            duration_ms,
            tags={'query_type': query.split()[0].upper()}
        )
        
        # Track slow queries (Requirement 14.3)
        if duration_ms > APMConfig.SLOW_QUERY_THRESHOLD_MS:
            provider.record_custom_metric(
                'database.query.slow',
                1,
                tags={'duration_ms': str(int(duration_ms))}
            )
    
    @staticmethod
    def track_external_service(service: str, operation: str, duration_ms: float, success: bool):
        """
        Track external service call performance.
        
        Implements Requirement 14.4: Track external service calls.
        
        Args:
            service: Service name (e.g., 's3', 'clerk', 'resend')
            operation: Operation name
            duration_ms: Call duration in milliseconds
            success: Whether the call succeeded
        """
        provider = APMConfig.get_provider()
        if not provider.enabled:
            return
        
        provider.record_custom_metric(
            f'external.{service}.duration',
            duration_ms,
            tags={
                'operation': operation,
                'success': str(success),
            }
        )
    
    @staticmethod
    def track_cache_operation(operation: str, hit: bool, duration_ms: float = 0):
        """
        Track cache performance.
        
        Implements Requirement 14.5: Track cache performance.
        
        Args:
            operation: Cache operation (get, set, delete)
            hit: Whether it was a cache hit
            duration_ms: Operation duration in milliseconds
        """
        provider = APMConfig.get_provider()
        if not provider.enabled:
            return
        
        provider.record_custom_metric(
            'cache.operation',
            1,
            tags={
                'operation': operation,
                'hit': str(hit),
            }
        )
        
        if duration_ms > 0:
            provider.record_custom_metric(
                'cache.duration',
                duration_ms,
                tags={'operation': operation}
            )
    
    @staticmethod
    def track_celery_task(task_name: str, duration_ms: float, success: bool, queue_depth: int = 0):
        """
        Track Celery task performance.
        
        Implements Requirement 14.6: Track Celery task performance.
        
        Args:
            task_name: Name of the Celery task
            duration_ms: Task duration in milliseconds
            success: Whether the task succeeded
            queue_depth: Current queue depth
        """
        provider = APMConfig.get_provider()
        if not provider.enabled:
            return
        
        provider.record_custom_metric(
            'celery.task.duration',
            duration_ms,
            tags={
                'task': task_name,
                'success': str(success),
            }
        )
        
        if queue_depth > 0:
            provider.record_custom_metric(
                'celery.queue.depth',
                queue_depth,
                tags={'task': task_name}
            )
    
    @staticmethod
    def track_business_metric(metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Track custom business metrics.
        
        Implements Requirement 14.10: Track custom business metrics.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for filtering
        """
        provider = APMConfig.get_provider()
        if not provider.enabled:
            return
        
        provider.record_custom_metric(
            f'business.{metric_name}',
            value,
            tags=tags
        )


def track_performance(metric_name: str, tags: Optional[Dict[str, str]] = None):
    """
    Decorator to track function performance.
    
    Args:
        metric_name: Name of the metric to track
        tags: Optional tags for filtering
    
    Example:
        @track_performance('story.create')
        def create_story(data):
            # Function implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                provider = APMConfig.get_provider()
                if provider.enabled:
                    provider.record_custom_metric(
                        metric_name,
                        duration_ms,
                        tags={
                            **(tags or {}),
                            'success': str(success),
                        }
                    )
        
        return wrapper
    return decorator


# Export public API
__all__ = [
    'APMConfig',
    'PerformanceMonitor',
    'init_newrelic',
    'init_datadog',
    'track_performance',
]
