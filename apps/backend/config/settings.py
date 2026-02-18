"""
Django settings for MueJam Library project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Validate configuration on startup (Requirements 30.9, 30.10, 30.11)
# This ensures all required environment variables are present before the app starts
if os.getenv('SKIP_CONFIG_VALIDATION', 'False') != 'True':
    from infrastructure.config_validator import validate_config_on_startup
    try:
        validate_config_on_startup()
    except Exception as e:
        # Re-raise to prevent app from starting with invalid configuration
        raise

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    
    # Local apps
    'apps.users',
    'apps.stories',
    'apps.library',
    'apps.whispers',
    'apps.highlights',
    'apps.social',
    'apps.notifications',
    'apps.discovery',
    'apps.search',
    'apps.uploads',
    'apps.moderation',
    'apps.legal',
    'apps.core',
    'apps.onboarding',
    'apps.help',
    'apps.analytics',
    'apps.security',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',  # Content Security Policy middleware
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.users.middleware.ClerkAuthMiddleware',
    'apps.users.email_verification.middleware.EmailVerificationMiddleware',
    'apps.users.two_factor_auth.middleware.TwoFactorAuthMiddleware',  # 2FA enforcement
    'infrastructure.logging_middleware.RequestLoggingMiddleware',  # Request logging (Requirement 15.3)
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database - Primary Connection
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_URL', '').split('/')[-1] or 'muejam',
        'USER': os.getenv('DATABASE_URL', '').split('://')[1].split(':')[0] if '://' in os.getenv('DATABASE_URL', '') else 'muejam_user',
        'PASSWORD': os.getenv('DATABASE_URL', '').split(':')[2].split('@')[0] if '@' in os.getenv('DATABASE_URL', '') else 'muejam_password',
        'HOST': os.getenv('DATABASE_URL', '').split('@')[1].split(':')[0] if '@' in os.getenv('DATABASE_URL', '') else 'localhost',
        'PORT': os.getenv('DATABASE_URL', '').split(':')[-1].split('/')[0] if '/' in os.getenv('DATABASE_URL', '') else '5432',
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # 30 second query timeout
        },
    }
}

# Read Replicas Configuration
# Configure read replica connections for workload isolation and high availability
# Each replica should have the same credentials as primary but different host
DATABASE_REPLICAS = [
    {
        'HOST': os.getenv('DATABASE_REPLICA_1_HOST', 'localhost'),
        'PORT': os.getenv('DATABASE_REPLICA_1_PORT', '5433'),
        'WEIGHT': float(os.getenv('DATABASE_REPLICA_1_WEIGHT', '1.0')),
    },
    {
        'HOST': os.getenv('DATABASE_REPLICA_2_HOST', 'localhost'),
        'PORT': os.getenv('DATABASE_REPLICA_2_PORT', '5434'),
        'WEIGHT': float(os.getenv('DATABASE_REPLICA_2_WEIGHT', '1.0')),
    },
    {
        'HOST': os.getenv('DATABASE_REPLICA_3_HOST', 'localhost'),
        'PORT': os.getenv('DATABASE_REPLICA_3_PORT', '5435'),
        'WEIGHT': float(os.getenv('DATABASE_REPLICA_3_WEIGHT', '1.0')),
    },
]

# Database Router Configuration
# Routes read queries to replicas and write queries to primary
DATABASE_ROUTERS = ['infrastructure.database_router.ReplicationRouter']

# Connection Pool Settings
# Controls connection pooling behavior for read and write operations
DB_POOL_MIN_CONNECTIONS = int(os.getenv('DB_POOL_MIN_CONNECTIONS', '10'))
DB_POOL_MAX_CONNECTIONS = int(os.getenv('DB_POOL_MAX_CONNECTIONS', '50'))
DB_POOL_IDLE_TIMEOUT = int(os.getenv('DB_POOL_IDLE_TIMEOUT', '300'))  # seconds

# Workload Isolation Settings
# Controls query routing between primary and replicas
MAX_REPLICA_LAG = float(os.getenv('MAX_REPLICA_LAG', '5.0'))  # seconds
REPLICA_LAG_CHECK_INTERVAL = int(os.getenv('REPLICA_LAG_CHECK_INTERVAL', '10'))  # seconds

# High Availability Settings
# Controls automatic failover behavior
ENABLE_AUTO_FAILOVER = os.getenv('ENABLE_AUTO_FAILOVER', 'True') == 'True'
FAILOVER_TIMEOUT = int(os.getenv('FAILOVER_TIMEOUT', '30'))  # seconds
HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '10'))  # seconds
HEALTH_CHECK_TIMEOUT = int(os.getenv('HEALTH_CHECK_TIMEOUT', '5'))  # seconds

# Failover Notification Settings
# Configure channels for failover alerts
FAILOVER_NOTIFICATION_CHANNELS = {
    'email': {
        'enabled': os.getenv('FAILOVER_EMAIL_ENABLED', 'False') == 'True',
        'recipients': os.getenv('FAILOVER_EMAIL_RECIPIENTS', '').split(','),
    },
    'slack': {
        'enabled': os.getenv('FAILOVER_SLACK_ENABLED', 'False') == 'True',
        'webhook_url': os.getenv('FAILOVER_SLACK_WEBHOOK_URL', ''),
    },
    'pagerduty': {
        'enabled': os.getenv('FAILOVER_PAGERDUTY_ENABLED', 'False') == 'True',
        'integration_key': os.getenv('FAILOVER_PAGERDUTY_KEY', ''),
    },
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
CORS_ALLOW_CREDENTIALS = True

# CSRF Protection Configuration (Requirements 6.1, 6.2)
# CSRF middleware is enabled in MIDDLEWARE list above
# Configure CSRF cookie settings for security
CSRF_COOKIE_SECURE = not DEBUG  # Only send cookie over HTTPS in production
CSRF_COOKIE_HTTPONLY = True  # Prevent JavaScript access to CSRF cookie
CSRF_COOKIE_SAMESITE = 'Strict'  # Prevent CSRF attacks via cross-site requests
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:3000').split(',')

# Session Security Configuration (Requirements 6.11, 6.12)
SESSION_COOKIE_SECURE = not DEBUG  # Only send cookie over HTTPS in production
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
SESSION_COOKIE_SAMESITE = 'Strict'  # Prevent session fixation attacks
SESSION_COOKIE_AGE = 2592000  # 30 days in seconds
SESSION_SAVE_EVERY_REQUEST = True  # Update session on every request
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Security Headers Configuration (Requirements 6.3, 6.4, 6.5, 6.6)
# HTTP Strict Transport Security (HSTS) - Forces HTTPS for 1 year
SECURE_HSTS_SECONDS = 31536000  # 1 year in seconds (Requirement 6.4)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # Apply HSTS to all subdomains
SECURE_HSTS_PRELOAD = True  # Allow inclusion in browser HSTS preload lists

# X-Frame-Options - Prevents clickjacking attacks
X_FRAME_OPTIONS = 'DENY'  # Requirement 6.5 - Prevent page from being framed

# X-Content-Type-Options - Prevents MIME type sniffing
SECURE_CONTENT_TYPE_NOSNIFF = True  # Requirement 6.6 - Force declared content types

# X-XSS-Protection - Legacy XSS protection (for older browsers)
SECURE_BROWSER_XSS_FILTER = True

# SSL/HTTPS Redirect
SECURE_SSL_REDIRECT = not DEBUG  # Redirect all HTTP to HTTPS in production

# Content Security Policy (CSP) Configuration (Requirement 6.3)
# Restricts sources for scripts, styles, images, and other resources
# Install django-csp package: pip install django-csp
CSP_DEFAULT_SRC = ("'self'",)  # Default: only allow same-origin resources
CSP_SCRIPT_SRC = (
    "'self'",
    'cdn.jsdelivr.net',  # CDN for frontend libraries
    'www.google.com',  # Google reCAPTCHA
    'www.gstatic.com',  # Google reCAPTCHA
)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # Allow inline styles (needed for some frameworks)
    'fonts.googleapis.com',  # Google Fonts
)
CSP_IMG_SRC = (
    "'self'",
    'data:',  # Allow data URIs for inline images
    'https:',  # Allow all HTTPS images
    '*.cloudfront.net',  # AWS CloudFront CDN
)
CSP_FONT_SRC = (
    "'self'",
    'fonts.gstatic.com',  # Google Fonts
)
CSP_CONNECT_SRC = (
    "'self'",
    'https://api.clerk.com',  # Clerk authentication
)
CSP_FRAME_ANCESTORS = ("'none'",)  # Prevent framing (same as X-Frame-Options: DENY)
CSP_BASE_URI = ("'self'",)  # Restrict base tag URLs
CSP_FORM_ACTION = ("'self'",)  # Restrict form submission targets

# Clerk Authentication
CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY', '')
CLERK_PUBLISHABLE_KEY = os.getenv('CLERK_PUBLISHABLE_KEY', '')

# Valkey/Redis Configuration
# Multi-layer caching with L1 (in-memory) and L2 (Redis/Valkey)
VALKEY_URL = os.getenv('VALKEY_URL', 'redis://localhost:6379/0')

# Django cache framework configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': VALKEY_URL,
        'KEY_PREFIX': 'muejam',
        'VERSION': 1,
    }
}

# Cache TTL Configuration (in seconds)
# Configure different TTL values for different types of data
CACHE_TTL = {
    # User-related data
    'user_profile': int(os.getenv('CACHE_TTL_USER_PROFILE', '300')),  # 5 minutes
    'user_preferences': int(os.getenv('CACHE_TTL_USER_PREFERENCES', '600')),  # 10 minutes
    'user_library': int(os.getenv('CACHE_TTL_USER_LIBRARY', '180')),  # 3 minutes
    
    # Story-related data
    'story_metadata': int(os.getenv('CACHE_TTL_STORY_METADATA', '600')),  # 10 minutes
    'story_chapters': int(os.getenv('CACHE_TTL_STORY_CHAPTERS', '900')),  # 15 minutes
    'story_content': int(os.getenv('CACHE_TTL_STORY_CONTENT', '1800')),  # 30 minutes
    
    # Discovery and feeds
    'trending_stories': int(os.getenv('CACHE_TTL_TRENDING', '300')),  # 5 minutes
    'new_stories': int(os.getenv('CACHE_TTL_NEW_STORIES', '180')),  # 3 minutes
    'recommendations': int(os.getenv('CACHE_TTL_RECOMMENDATIONS', '600')),  # 10 minutes
    
    # Social data
    'whispers_feed': int(os.getenv('CACHE_TTL_WHISPERS_FEED', '60')),  # 1 minute
    'notifications': int(os.getenv('CACHE_TTL_NOTIFICATIONS', '30')),  # 30 seconds
    'follower_counts': int(os.getenv('CACHE_TTL_FOLLOWER_COUNTS', '300')),  # 5 minutes
    
    # Search results
    'search_results': int(os.getenv('CACHE_TTL_SEARCH_RESULTS', '300')),  # 5 minutes
    'autocomplete': int(os.getenv('CACHE_TTL_AUTOCOMPLETE', '600')),  # 10 minutes
    
    # Static/rarely changing data
    'genres': int(os.getenv('CACHE_TTL_GENRES', '3600')),  # 1 hour
    'tags': int(os.getenv('CACHE_TTL_TAGS', '3600')),  # 1 hour
    
    # Default TTL for unspecified cache types
    'default': int(os.getenv('CACHE_TTL_DEFAULT', '300')),  # 5 minutes
}

# L1 Cache Configuration (in-memory LRU cache)
L1_CACHE_MAX_SIZE = int(os.getenv('L1_CACHE_MAX_SIZE', '1000'))
L1_CACHE_DEFAULT_TTL = int(os.getenv('L1_CACHE_DEFAULT_TTL', '60'))  # 60 seconds

# Rate Limiting Configuration
# Distributed rate limiting using Redis/Valkey
RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'True') == 'True'
RATE_LIMIT_REDIS_URL = os.getenv('RATE_LIMIT_REDIS_URL', VALKEY_URL)

# Per-user rate limits (queries per minute)
RATE_LIMIT_PER_USER = int(os.getenv('RATE_LIMIT_PER_USER', '100'))

# Global rate limits (queries per minute across all users)
RATE_LIMIT_GLOBAL = int(os.getenv('RATE_LIMIT_GLOBAL', '10000'))

# Rate limit window size in seconds
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '60'))

# Admin users bypass rate limits
RATE_LIMIT_ADMIN_BYPASS = os.getenv('RATE_LIMIT_ADMIN_BYPASS', 'True') == 'True'

# django-ratelimit configuration
# Use Redis cache backend for distributed rate limiting
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_ENABLE = RATE_LIMIT_ENABLED

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET', 'muejam-media')

# Resend Email Configuration
RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')

# Sentry Error Tracking Configuration (Requirements 13.1, 13.2, 13.6)
# Get your DSN from: https://sentry.io/settings/projects/
SENTRY_DSN = os.getenv('SENTRY_DSN', '')
SENTRY_ENVIRONMENT = os.getenv('SENTRY_ENVIRONMENT', os.getenv('ENVIRONMENT', 'development'))
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1'))  # 10% of transactions
SENTRY_PROFILES_SAMPLE_RATE = float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.1'))  # 10% of transactions
APP_VERSION = os.getenv('APP_VERSION', os.getenv('VERSION', '1.0.0'))

# Initialize Sentry if DSN is configured
if SENTRY_DSN:
    from infrastructure.sentry_config import init_sentry
    init_sentry()

# Application Performance Monitoring (APM) Configuration (Requirements 14.1-14.12)
# Supports both New Relic and DataDog APM providers
APM_ENABLED = os.getenv('APM_ENABLED', 'False') == 'True'
APM_PROVIDER = os.getenv('APM_PROVIDER', 'newrelic').lower()  # 'newrelic' or 'datadog'

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

# Initialize APM if enabled
if APM_ENABLED:
    if APM_PROVIDER == 'newrelic':
        from infrastructure.apm_config import init_newrelic
        init_newrelic()
    elif APM_PROVIDER == 'datadog':
        from infrastructure.apm_config import init_datadog
        init_datadog()

# Google Safe Browsing API Configuration
# Used for URL validation in content moderation (Requirements 4.6, 4.7)
# Get your API key from: https://developers.google.com/safe-browsing/v4/get-started
GOOGLE_SAFE_BROWSING_API_KEY = os.getenv('GOOGLE_SAFE_BROWSING_API_KEY', '')

# Google reCAPTCHA v3 Configuration
# Used for bot protection on signup, login, and content submission (Requirements 5.4, 5.5)
# Get your keys from: https://www.google.com/recaptcha/admin
RECAPTCHA_SECRET_KEY = os.getenv('RECAPTCHA_SECRET_KEY', '')
RECAPTCHA_SCORE_THRESHOLD = float(os.getenv('RECAPTCHA_SCORE_THRESHOLD', '0.5'))

# Frontend URL
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# Structured Logging Configuration (Requirements 15.1-15.12)
# JSON-formatted structured logging with automatic PII redaction
from infrastructure.logging_config import LoggingConfig

LOGGING = LoggingConfig.get_logging_config()

# Create logs directory if it doesn't exist
import os
os.makedirs('logs', exist_ok=True)

# DRF Spectacular Settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'MueJam Library API',
    'DESCRIPTION': '''
    MueJam Library is a digital library platform for serial stories with an integrated micro-posting system.
    
    ## Features
    - **Story Discovery**: Browse trending, new, and personalized story recommendations
    - **Reading Experience**: Distraction-free reader with customizable settings
    - **Library Management**: Organize stories into personal shelves
    - **Whispers**: Micro-posting system for global, story-linked, and highlight-linked posts
    - **Social Features**: Follow authors, block users, and engage with the community
    - **Notifications**: Stay informed about replies and follows
    
    ## Authentication
    All authenticated endpoints require a Bearer token in the Authorization header.
    Tokens are issued by Clerk authentication service.
    
    Example: `Authorization: Bearer <your_token>`
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/v1',
    'SERVERS': [
        {'url': 'http://localhost:8000', 'description': 'Development server'},
        {'url': 'https://api.muejam.com', 'description': 'Production server'},
    ],
    'TAGS': [
        {'name': 'Authentication', 'description': 'User authentication and profile management'},
        {'name': 'Stories', 'description': 'Story and chapter management'},
        {'name': 'Library', 'description': 'Personal library and shelf management'},
        {'name': 'Reading', 'description': 'Reading progress, bookmarks, and highlights'},
        {'name': 'Whispers', 'description': 'Micro-posting system'},
        {'name': 'Social', 'description': 'Follow and block operations'},
        {'name': 'Notifications', 'description': 'Notification management'},
        {'name': 'Discovery', 'description': 'Content discovery feeds'},
        {'name': 'Search', 'description': 'Search and autocomplete'},
        {'name': 'Uploads', 'description': 'Media upload management'},
        {'name': 'Moderation', 'description': 'Content reporting'},
        {'name': 'Health', 'description': 'System health monitoring'},
    ],
    'CONTACT': {
        'name': 'MueJam Library Support',
        'email': 'support@muejam.com',
    },
    'LICENSE': {
        'name': 'Proprietary',
    },
}
