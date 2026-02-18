"""
Database Configuration for Production

This module provides database configuration with connection pooling,
read replica routing, and monitoring.

Requirements: 33.2, 33.5
"""

import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


# Connection Pool Configuration
CONNECTION_POOL_CONFIG = {
    'min_connections': int(os.getenv('DB_POOL_MIN_CONNECTIONS', '10')),
    'max_connections': int(os.getenv('DB_POOL_MAX_CONNECTIONS', '50')),
    'idle_timeout': int(os.getenv('DB_POOL_IDLE_TIMEOUT', '300')),  # 5 minutes
    'connection_timeout': float(os.getenv('DB_POOL_CONNECTION_TIMEOUT', '5.0')),
}

# Database Configuration
DATABASE_CONFIG = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': os.getenv('DB_NAME', 'muejam'),
    'USER': os.getenv('DB_USER', 'postgres'),
    'PASSWORD': os.getenv('DB_PASSWORD', ''),
    'HOST': os.getenv('DB_HOST', 'localhost'),
    'PORT': os.getenv('DB_PORT', '5432'),
    'CONN_MAX_AGE': 0,  # Don't use Django's connection pooling, use our custom pool
    'OPTIONS': {
        'connect_timeout': 10,
        'options': '-c statement_timeout=30000',  # 30 second query timeout
    },
}

# Read Replica Configuration
READ_REPLICA_CONFIG = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': os.getenv('DB_READ_NAME', os.getenv('DB_NAME', 'muejam')),
    'USER': os.getenv('DB_READ_USER', os.getenv('DB_USER', 'postgres')),
    'PASSWORD': os.getenv('DB_READ_PASSWORD', os.getenv('DB_PASSWORD', '')),
    'HOST': os.getenv('DB_READ_HOST', os.getenv('DB_HOST', 'localhost')),
    'PORT': os.getenv('DB_READ_PORT', os.getenv('DB_PORT', '5432')),
    'CONN_MAX_AGE': 0,
    'OPTIONS': {
        'connect_timeout': 10,
        'options': '-c statement_timeout=30000',
    },
}

# Database Router Configuration
USE_READ_REPLICA = os.getenv('USE_READ_REPLICA', 'false').lower() == 'true'


def get_database_settings() -> Dict[str, Any]:
    """
    Get Django database settings with connection pooling configuration.
    
    Returns:
        Dictionary of database settings for Django settings.py
    """
    databases = {
        'default': DATABASE_CONFIG.copy()
    }
    
    # Add read replica if configured
    if USE_READ_REPLICA:
        databases['read_replica'] = READ_REPLICA_CONFIG.copy()
        logger.info("Read replica configured")
    
    return databases


def get_connection_pool_config() -> Dict[str, Any]:
    """
    Get connection pool configuration.
    
    Returns:
        Dictionary of connection pool settings
    """
    return CONNECTION_POOL_CONFIG.copy()


def log_database_config():
    """Log database configuration (without sensitive data)."""
    logger.info("Database Configuration:")
    logger.info(f"  Primary Host: {DATABASE_CONFIG['HOST']}:{DATABASE_CONFIG['PORT']}")
    logger.info(f"  Database: {DATABASE_CONFIG['NAME']}")
    logger.info(f"  Connection Pool: min={CONNECTION_POOL_CONFIG['min_connections']}, "
                f"max={CONNECTION_POOL_CONFIG['max_connections']}")
    logger.info(f"  Idle Timeout: {CONNECTION_POOL_CONFIG['idle_timeout']}s")
    
    if USE_READ_REPLICA:
        logger.info(f"  Read Replica Host: {READ_REPLICA_CONFIG['HOST']}:{READ_REPLICA_CONFIG['PORT']}")
    else:
        logger.info("  Read Replica: Not configured")


# Django Database Router for Read/Write Splitting
class ReadWriteRouter:
    """
    Database router that directs read queries to read replicas and write queries to primary.
    
    Requirements: 33.5
    """
    
    def db_for_read(self, model, **hints):
        """
        Route read operations to read replica if available.
        
        Args:
            model: Django model class
            **hints: Additional routing hints
            
        Returns:
            Database alias to use for read operations
        """
        if USE_READ_REPLICA:
            return 'read_replica'
        return 'default'
    
    def db_for_write(self, model, **hints):
        """
        Route write operations to primary database.
        
        Args:
            model: Django model class
            **hints: Additional routing hints
            
        Returns:
            Database alias to use for write operations
        """
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations between objects in the same database.
        
        Args:
            obj1: First model instance
            obj2: Second model instance
            **hints: Additional routing hints
            
        Returns:
            True if relation is allowed, None otherwise
        """
        db_set = {'default', 'read_replica'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Only allow migrations on the primary database.
        
        Args:
            db: Database alias
            app_label: Application label
            model_name: Model name (optional)
            **hints: Additional routing hints
            
        Returns:
            True if migration is allowed, False otherwise
        """
        return db == 'default'


# Connection Pool Monitoring
class ConnectionPoolMonitor:
    """
    Monitor connection pool statistics and alert on issues.
    
    Requirements: 33.2
    """
    
    def __init__(self, pool_manager):
        """
        Initialize monitor with connection pool manager.
        
        Args:
            pool_manager: ConnectionPoolManager instance
        """
        self.pool_manager = pool_manager
        self.alert_threshold = 80  # Alert when utilization exceeds 80%
    
    def check_pool_health(self) -> Dict[str, Any]:
        """
        Check connection pool health and return status.
        
        Returns:
            Dictionary with pool health information
        """
        stats = self.pool_manager.get_pool_stats()
        
        health = {
            'healthy': True,
            'alerts': [],
            'stats': {}
        }
        
        for pool_type, pool_stats in stats.items():
            health['stats'][pool_type] = {
                'total': pool_stats.total_connections,
                'active': pool_stats.active_connections,
                'idle': pool_stats.idle_connections,
                'utilization': pool_stats.utilization_percent,
                'avg_wait_ms': pool_stats.wait_time_avg,
                'errors': pool_stats.connection_errors
            }
            
            # Check for high utilization
            if pool_stats.utilization_percent > self.alert_threshold:
                health['healthy'] = False
                health['alerts'].append({
                    'severity': 'warning',
                    'pool': pool_type,
                    'message': f'{pool_type.capitalize()} pool utilization at '
                              f'{pool_stats.utilization_percent:.1f}% '
                              f'(threshold: {self.alert_threshold}%)'
                })
            
            # Check for connection errors
            if pool_stats.connection_errors > 0:
                health['healthy'] = False
                health['alerts'].append({
                    'severity': 'error',
                    'pool': pool_type,
                    'message': f'{pool_type.capitalize()} pool has '
                              f'{pool_stats.connection_errors} connection errors'
                })
        
        return health
    
    def log_pool_stats(self):
        """Log current pool statistics."""
        stats = self.pool_manager.get_pool_stats()
        
        for pool_type, pool_stats in stats.items():
            logger.info(
                f"{pool_type.capitalize()} Pool: "
                f"{pool_stats.active_connections}/{pool_stats.total_connections} active "
                f"({pool_stats.utilization_percent:.1f}% utilization), "
                f"avg wait: {pool_stats.wait_time_avg:.2f}ms"
            )


# Example Django settings.py integration
DJANGO_SETTINGS_EXAMPLE = """
# Add to settings.py:

from infrastructure.database_config import (
    get_database_settings,
    get_connection_pool_config,
    ReadWriteRouter,
    log_database_config
)

# Database configuration
DATABASES = get_database_settings()

# Database routers for read/write splitting
DATABASE_ROUTERS = ['infrastructure.database_config.ReadWriteRouter']

# Connection pool configuration
CONNECTION_POOL_CONFIG = get_connection_pool_config()

# Log configuration on startup
log_database_config()
"""


if __name__ == '__main__':
    # Print configuration example
    print("Database Configuration Example")
    print("=" * 60)
    print(DJANGO_SETTINGS_EXAMPLE)
    print()
    print("Environment Variables:")
    print("=" * 60)
    print("# Primary Database")
    print("DB_NAME=muejam")
    print("DB_USER=postgres")
    print("DB_PASSWORD=your_password")
    print("DB_HOST=primary.db.example.com")
    print("DB_PORT=5432")
    print()
    print("# Read Replica (optional)")
    print("USE_READ_REPLICA=true")
    print("DB_READ_HOST=replica.db.example.com")
    print("DB_READ_PORT=5432")
    print()
    print("# Connection Pool")
    print("DB_POOL_MIN_CONNECTIONS=10")
    print("DB_POOL_MAX_CONNECTIONS=50")
    print("DB_POOL_IDLE_TIMEOUT=300")
    print("DB_POOL_CONNECTION_TIMEOUT=5.0")
