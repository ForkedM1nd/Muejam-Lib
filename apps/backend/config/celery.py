"""
Celery configuration for MueJam Library project.
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('muejam')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'update-trending-scores': {
        'task': 'apps.discovery.tasks.update_trending_scores',
        'schedule': 1800.0,  # Every 30 minutes
    },
    'apply-daily-decay': {
        'task': 'apps.discovery.tasks.apply_daily_decay',
        'schedule': 86400.0,  # Every 24 hours
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
