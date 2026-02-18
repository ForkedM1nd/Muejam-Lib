"""Views for core functionality (health check)."""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.cache import cache
from datetime import datetime, timezone
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.types import OpenApiTypes


@extend_schema(
    tags=['Health'],
    summary='System health check',
    description='''
    Check the health status of the MueJam Library API and its dependencies.
    
    This endpoint verifies:
    - Database connectivity (PostgreSQL)
    - Cache connectivity (Valkey/Redis)
    
    Returns HTTP 200 if all systems are operational, HTTP 503 if any dependency is down.
    
    **Note**: This endpoint does not require authentication.
    ''',
    responses={
        200: OpenApiTypes.OBJECT,
        503: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Healthy Response',
            value={
                'status': 'healthy',
                'timestamp': '2024-01-20T15:30:00.000000',
                'checks': {
                    'database': 'healthy',
                    'cache': 'healthy'
                }
            },
            response_only=True,
            status_codes=['200'],
        ),
        OpenApiExample(
            'Unhealthy Response',
            value={
                'status': 'unhealthy',
                'timestamp': '2024-01-20T15:30:00.000000',
                'checks': {
                    'database': 'healthy',
                    'cache': 'unhealthy: Connection refused'
                }
            },
            response_only=True,
            status_codes=['503'],
        ),
    ]
)
@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint to verify system status.
    Returns HTTP 200 if all dependencies are healthy, HTTP 503 otherwise.
    """
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'checks': {}
    }
    
    # Check database connectivity
    try:
        connection.ensure_connection()
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Check cache connectivity
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['checks']['cache'] = 'healthy'
        else:
            health_status['checks']['cache'] = 'unhealthy: cache read/write failed'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['cache'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    status_code = status.HTTP_200_OK if health_status['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(health_status, status=status_code)
