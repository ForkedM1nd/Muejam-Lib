"""
Database Configuration with Connection Pooling

This module provides database configuration with proper connection pooling
for production readiness. Implements CONN_MAX_AGE for persistent connections
and configurable timeouts.

Requirements: Production Readiness Audit - Task 2.1
"""

import os
import logging
from urllib.parse import urlparse
from typing import Dict, Any

logger = logging.getLogger(__name__)


def get_database_config() -> Dict[str, Any]:
    """
    Get database configuration with connection pooling enabled.
    
    This function configures Django's database settings with:
    - Connection pooling via CONN_MAX_AGE (10 minutes)
    - Connection timeout (10 seconds)
    - Query timeout (30 seconds)
    - Proper connection string parsing
    - Secrets Manager integration for production
    
    Returns:
        Dictionary containing Django database configuration
        
    Raises:
        ValueError: If DATABASE_URL is not set or invalid
    """
    # Try to get DATABASE_URL from Secrets Manager in production
    environment = os.getenv('ENVIRONMENT', 'development')
    use_secrets_manager = os.getenv('USE_SECRETS_MANAGER', 'False') == 'True'
    
    database_url = os.getenv('DATABASE_URL', '')
    
    # In production with Secrets Manager enabled, try to load from secrets
    if use_secrets_manager and environment == 'production' and not database_url:
        try:
            from infrastructure.secrets_manager import get_secrets_manager
            secrets_manager = get_secrets_manager()
            db_secrets = secrets_manager.get_secret('database/primary')
            database_url = db_secrets.get('connection_string', '')
            logger.info("Loaded DATABASE_URL from Secrets Manager")
        except Exception as e:
            logger.error(f"Failed to retrieve database secrets from Secrets Manager: {e}")
            # Fall through to environment variable or fallback
    
    if not database_url:
        # Fallback for development - construct from individual env vars
        logger.warning("DATABASE_URL not set, using fallback configuration")
        return {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'muejam'),
            'USER': os.getenv('DB_USER', 'muejam_user'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'muejam_password'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': int(os.getenv('DB_PORT', '5432')),
            'CONN_MAX_AGE': 600,  # Keep connections alive for 10 minutes
            'OPTIONS': {
                'connect_timeout': 10,  # 10 second connection timeout
                'options': '-c statement_timeout=30000',  # 30 second query timeout
            },
        }
    
    # Parse DATABASE_URL
    try:
        parsed = urlparse(database_url)
        
        if not parsed.scheme or parsed.scheme not in ['postgres', 'postgresql']:
            raise ValueError(f"Invalid database URL scheme: {parsed.scheme}")
        
        config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed.path[1:] if parsed.path else 'muejam',
            'USER': parsed.username or 'muejam_user',
            'PASSWORD': parsed.password or '',
            'HOST': parsed.hostname or 'localhost',
            'PORT': parsed.port or 5432,
            # Connection pooling: Keep connections alive for 10 minutes
            # This prevents creating new connections for every request
            'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '600')),
            'OPTIONS': {
                # Connection timeout: Fail fast if database is unreachable
                'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '10')),
                # Query timeout: Prevent long-running queries from blocking
                'options': f"-c statement_timeout={os.getenv('DB_STATEMENT_TIMEOUT', '30000')}",
            },
        }
        
        logger.info(
            f"Database configuration loaded: "
            f"host={config['HOST']}, "
            f"port={config['PORT']}, "
            f"database={config['NAME']}, "
            f"conn_max_age={config['CONN_MAX_AGE']}s"
        )
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to parse DATABASE_URL: {e}")
        raise ValueError(f"Invalid DATABASE_URL: {e}")


def get_pgbouncer_config() -> Dict[str, Any]:
    """
    Get database configuration for connecting through pgbouncer.
    
    When using pgbouncer, the application connects to pgbouncer instead
    of directly to PostgreSQL. Pgbouncer handles connection pooling.
    
    Returns:
        Dictionary containing pgbouncer database configuration
    """
    pgbouncer_url = os.getenv('PGBOUNCER_URL', '')
    
    if not pgbouncer_url:
        # Fallback: assume pgbouncer is on port 6432
        logger.info("PGBOUNCER_URL not set, using default port 6432")
        return {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'muejam'),
            'USER': os.getenv('DB_USER', 'muejam_user'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'muejam_password'),
            'HOST': os.getenv('PGBOUNCER_HOST', 'localhost'),
            'PORT': int(os.getenv('PGBOUNCER_PORT', '6432')),
            # With pgbouncer, we can use persistent connections
            'CONN_MAX_AGE': 600,
            'OPTIONS': {
                'connect_timeout': 10,
                'options': '-c statement_timeout=30000',
            },
        }
    
    # Parse PGBOUNCER_URL
    parsed = urlparse(pgbouncer_url)
    
    config = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': parsed.path[1:] if parsed.path else 'muejam',
        'USER': parsed.username or 'muejam_user',
        'PASSWORD': parsed.password or '',
        'HOST': parsed.hostname or 'localhost',
        'PORT': parsed.port or 6432,
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
        },
    }
    
    logger.info(
        f"Pgbouncer configuration loaded: "
        f"host={config['HOST']}, "
        f"port={config['PORT']}"
    )
    
    return config


def should_use_pgbouncer() -> bool:
    """
    Determine if pgbouncer should be used based on environment.
    
    Returns:
        True if pgbouncer should be used, False otherwise
    """
    use_pgbouncer = os.getenv('USE_PGBOUNCER', 'false').lower() == 'true'
    
    if use_pgbouncer:
        logger.info("Using pgbouncer for connection pooling")
    else:
        logger.info("Using Django's built-in connection pooling (CONN_MAX_AGE)")
    
    return use_pgbouncer


def get_database_settings() -> Dict[str, Dict[str, Any]]:
    """
    Get complete database settings for Django DATABASES configuration.
    
    This function returns the appropriate database configuration based on
    whether pgbouncer is enabled or not.
    
    Returns:
        Dictionary with 'default' database configuration
    """
    if should_use_pgbouncer():
        databases = {
            'default': get_pgbouncer_config()
        }
    else:
        databases = {
            'default': get_database_config()
        }
    
    return databases


# Connection pool monitoring utilities
def log_connection_pool_stats():
    """
    Log current connection pool statistics.
    
    This function can be called periodically to monitor connection pool health.
    """
    from django.db import connection
    
    try:
        # Get connection info
        conn_params = connection.get_connection_params()
        logger.info(
            f"Connection pool stats: "
            f"host={conn_params.get('host')}, "
            f"database={conn_params.get('database')}"
        )
        
        # Check if connection is alive
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            logger.info("Database connection is healthy")
            
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")


if __name__ == '__main__':
    # Test configuration
    print("Database Configuration Test")
    print("=" * 60)
    
    try:
        config = get_database_config()
        print("✓ Database configuration loaded successfully")
        print(f"  Host: {config['HOST']}")
        print(f"  Port: {config['PORT']}")
        print(f"  Database: {config['NAME']}")
        print(f"  Connection Max Age: {config['CONN_MAX_AGE']}s")
        print(f"  Connect Timeout: {config['OPTIONS']['connect_timeout']}s")
    except Exception as e:
        print(f"✗ Configuration error: {e}")
    
    print()
    print("Environment Variables:")
    print("=" * 60)
    print("# Direct PostgreSQL connection:")
    print("DATABASE_URL=postgresql://user:password@host:5432/database")
    print()
    print("# Or individual variables:")
    print("DB_NAME=muejam")
    print("DB_USER=muejam_user")
    print("DB_PASSWORD=your_password")
    print("DB_HOST=localhost")
    print("DB_PORT=5432")
    print()
    print("# Optional: Use pgbouncer")
    print("USE_PGBOUNCER=true")
    print("PGBOUNCER_URL=postgresql://user:password@host:6432/database")
    print()
    print("# Optional: Customize timeouts")
    print("DB_CONN_MAX_AGE=600  # seconds")
    print("DB_CONNECT_TIMEOUT=10  # seconds")
    print("DB_STATEMENT_TIMEOUT=30000  # milliseconds")
