"""
Celery Beat Schedule Configuration for Notifications.

Add this to your main Celery configuration in settings.py:

from apps.notifications.celery_config import NOTIFICATION_BEAT_SCHEDULE

CELERY_BEAT_SCHEDULE = {
    **CELERY_BEAT_SCHEDULE,
    **NOTIFICATION_BEAT_SCHEDULE
}
"""
from celery.schedules import crontab

NOTIFICATION_BEAT_SCHEDULE = {
    # Daily digest at 9 AM every day
    'send-daily-digests': {
        'task': 'apps.notifications.tasks.send_daily_digests',
        'schedule': crontab(hour=9, minute=0),
        'options': {
            'expires': 3600,  # Task expires after 1 hour
        }
    },
    
    # Weekly digest at 9 AM every Monday
    'send-weekly-digests': {
        'task': 'apps.notifications.tasks.send_weekly_digests',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),
        'options': {
            'expires': 3600,  # Task expires after 1 hour
        }
    },
}
