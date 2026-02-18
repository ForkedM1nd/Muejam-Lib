"""
Django management command to monitor database connection pool.

Usage:
    python manage.py monitor_connection_pool
    python manage.py monitor_connection_pool --watch
    python manage.py monitor_connection_pool --json
"""

from django.core.management.base import BaseCommand
import time
import json
from infrastructure.connection_pool_monitor import (
    ConnectionPoolMonitor,
    print_connection_pool_report
)


class Command(BaseCommand):
    help = 'Monitor database connection pool health and statistics'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--watch',
            action='store_true',
            help='Continuously monitor and refresh every 5 seconds'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Refresh interval in seconds (default: 5)'
        )
    
    def handle(self, *args, **options):
        monitor = ConnectionPoolMonitor()
        
        if options['json']:
            # Output JSON format
            health = monitor.check_health()
            self.stdout.write(json.dumps(health, indent=2))
            return
        
        if options['watch']:
            # Continuous monitoring
            interval = options['interval']
            self.stdout.write(
                self.style.SUCCESS(
                    f'Monitoring connection pool (refresh every {interval}s, Ctrl+C to stop)...\n'
                )
            )
            
            try:
                while True:
                    print_connection_pool_report()
                    time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write('\nMonitoring stopped.')
        else:
            # Single report
            print_connection_pool_report()
