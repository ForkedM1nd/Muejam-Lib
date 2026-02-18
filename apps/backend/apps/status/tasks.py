"""
Status Page Celery Tasks.

Implements Requirement 18.4: Automatically update component status every 60 seconds.
"""
from celery import shared_task
from .health_check_service import HealthCheckService


@shared_task
def perform_health_checks():
    """
    Perform automated health checks on all components.
    
    Implements Requirement 18.4: Automatically update component status.
    
    This task should be scheduled to run every 60 seconds using Celery Beat.
    """
    try:
        results = HealthCheckService.check_all_components()
        return {
            'success': True,
            'results': results
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# Celery Beat schedule configuration (add to settings.py):
"""
CELERY_BEAT_SCHEDULE = {
    'status-health-checks': {
        'task': 'apps.status.tasks.perform_health_checks',
        'schedule': 60.0,  # Run every 60 seconds
    },
}
"""
