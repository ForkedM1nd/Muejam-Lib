"""
Django management command to create full-text search indexes.

Usage:
    python manage.py create_search_indexes
"""

from django.core.management.base import BaseCommand
from django.db import connection

from infrastructure.search_indexes import create_search_indexes, SEARCH_INDEXES


class Command(BaseCommand):
    help = 'Create full-text search indexes for PostgreSQL'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating full-text search indexes...'))
        self.stdout.write(f'Total indexes to create: {len(SEARCH_INDEXES)}')
        self.stdout.write('')
        
        try:
            with connection.cursor() as cursor:
                count = create_search_indexes(cursor)
                
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(
                f'✓ Successfully created {count} search indexes'
            ))
            self.stdout.write('')
            self.stdout.write('Search indexes created:')
            self.stdout.write('  - stories.search_vector (title, description, content)')
            self.stdout.write('  - user_profiles.search_vector (display_name, username, bio)')
            self.stdout.write('  - tags.search_vector (name, description)')
            self.stdout.write('  - Filter indexes (genre, completion_status, word_count, updated_at)')
            self.stdout.write('  - search_queries table for analytics')
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('Search indexes are ready to use!'))
            
        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'✗ Error creating search indexes: {e}'))
            raise
