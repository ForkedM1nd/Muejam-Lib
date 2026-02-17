"""
Django settings for MueJam Library project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    'apps.core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.users.middleware.ClerkAuthMiddleware',
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
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
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

# Frontend URL
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

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
