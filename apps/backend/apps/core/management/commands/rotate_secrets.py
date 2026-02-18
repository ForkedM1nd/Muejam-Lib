"""
Management command to rotate secrets in AWS Secrets Manager.

Usage:
    python manage.py rotate_secrets --type database --name primary
    python manage.py rotate_secrets --type api-key --name resend
    python manage.py rotate_secrets --all

Requirements: 30.4, 30.5 - Automatic secret rotation
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from infrastructure.secrets_manager import get_secrets_manager, SecretsManagerError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Rotate secrets in AWS Secrets Manager'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['database', 'api-key'],
            help='Type of secret to rotate'
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Name of the secret to rotate (e.g., primary, resend)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Rotate all configured secrets'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be rotated without actually rotating'
        )
    
    def handle(self, *args, **options):
        secrets_manager = get_secrets_manager()
        
        if options['all']:
            self.rotate_all_secrets(secrets_manager, options['dry_run'])
        elif options['type'] and options['name']:
            self.rotate_single_secret(
                secrets_manager,
                options['type'],
                options['name'],
                options['dry_run']
            )
        else:
            raise CommandError(
                'Please specify either --all or both --type and --name'
            )
    
    def rotate_single_secret(self, secrets_manager, secret_type, name, dry_run):
        """Rotate a single secret"""
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY RUN] Would rotate {secret_type} secret: {name}'
                )
            )
            return
        
        try:
            if secret_type == 'database':
                new_value = secrets_manager.rotate_database_password(name)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully rotated database password for: {name}'
                    )
                )
                self.stdout.write(
                    self.style.WARNING(
                        'IMPORTANT: Update database server with new password!'
                    )
                )
            
            elif secret_type == 'api-key':
                new_value = secrets_manager.rotate_api_key(name)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully rotated API key for: {name}'
                    )
                )
                self.stdout.write(
                    self.style.WARNING(
                        'IMPORTANT: Update service configuration with new API key!'
                    )
                )
        
        except SecretsManagerError as e:
            raise CommandError(f'Failed to rotate secret: {e}')
    
    def rotate_all_secrets(self, secrets_manager, dry_run):
        """Rotate all configured secrets"""
        # Define secrets to rotate
        secrets_to_rotate = [
            ('database', 'primary'),
            ('api-key', 'resend'),
            ('api-key', 'aws'),
            ('api-key', 'clerk'),
        ]
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('[DRY RUN] Would rotate the following secrets:')
            )
            for secret_type, name in secrets_to_rotate:
                self.stdout.write(f'  - {secret_type}: {name}')
            return
        
        self.stdout.write('Rotating all secrets...\n')
        
        success_count = 0
        failure_count = 0
        
        for secret_type, name in secrets_to_rotate:
            try:
                self.rotate_single_secret(secrets_manager, secret_type, name, False)
                success_count += 1
            except CommandError as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to rotate {secret_type}/{name}: {e}')
                )
                failure_count += 1
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS(f'Successfully rotated: {success_count} secrets')
        )
        if failure_count > 0:
            self.stdout.write(
                self.style.ERROR(f'Failed to rotate: {failure_count} secrets')
            )
        self.stdout.write('=' * 60)
