"""
Django management command to create database indexes for performance optimization.

Usage:
    python manage.py create_indexes
    python manage.py create_indexes --category moderation
    python manage.py create_indexes --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import connection
from infrastructure.database_indexes import (
    get_all_index_statements,
    get_index_statements_by_category,
    print_index_summary
)


class Command(BaseCommand):
    help = 'Create database indexes for performance optimization'

    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            type=str,
            help='Create indexes for specific category only',
            choices=[
                'moderation', 'rate_limiting', 'audit_log', 'nsfw',
                'notification', 'privacy', 'discovery', 'security',
                '2fa', 'composite'
            ]
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show SQL statements without executing them'
        )

    def handle(self, *args, **options):
        category = options.get('category')
        dry_run = options.get('dry_run', False)

        self.stdout.write(self.style.SUCCESS('Database Index Optimization'))
        self.stdout.write('=' * 60)
        
        # Get SQL statements
        if category:
            sql = get_index_statements_by_category(category)
            self.stdout.write(f'Category: {category}')
        else:
            sql = get_all_index_statements()
            self.stdout.write('Creating all indexes')
        
        self.stdout.write('=' * 60)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN MODE - No changes will be made\n'))
            self.stdout.write(sql)
            return
        
        # Execute SQL
        try:
            with connection.cursor() as cursor:
                self.stdout.write('\nExecuting index creation...')
                cursor.execute(sql)
                self.stdout.write(self.style.SUCCESS('✓ Indexes created successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error creating indexes: {str(e)}'))
            raise
        
        # Print summary
        self.stdout.write('\n')
        print_index_summary()
        
        self.stdout.write(self.style.SUCCESS('\nIndex optimization complete!'))
        self.stdout.write('\nTo verify indexes, run:')
        self.stdout.write('  SELECT indexname, tablename FROM pg_indexes WHERE schemaname = \'public\' ORDER BY tablename, indexname;')
