"""
Management command to validate environment configuration.

Usage:
    python manage.py validate_config
    python manage.py validate_config --export-docs
    python manage.py validate_config --environment production

Requirements: 30.9, 30.10, 30.11 - Configuration validation
"""

import logging
from django.core.management.base import BaseCommand
from infrastructure.config_validator import ConfigValidator, ConfigValidationError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Validate environment configuration and generate documentation'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--environment',
            type=str,
            choices=['production', 'staging', 'development'],
            help='Environment to validate (default: current environment)'
        )
        parser.add_argument(
            '--export-docs',
            action='store_true',
            help='Export environment variables documentation to file'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='docs/ENVIRONMENT_VARIABLES.md',
            help='Output path for documentation (default: docs/ENVIRONMENT_VARIABLES.md)'
        )
        parser.add_argument(
            '--no-fail',
            action='store_true',
            help='Do not fail on validation errors (just report them)'
        )
    
    def handle(self, *args, **options):
        environment = options.get('environment')
        export_docs = options.get('export_docs')
        output_path = options.get('output')
        no_fail = options.get('no_fail')
        
        # Create validator
        validator = ConfigValidator(environment=environment)
        
        # Export documentation if requested
        if export_docs:
            self.export_documentation(validator, output_path)
            return
        
        # Validate configuration
        self.validate_configuration(validator, no_fail)
    
    def validate_configuration(self, validator, no_fail):
        """Validate environment configuration"""
        self.stdout.write('=' * 80)
        self.stdout.write(
            self.style.HTTP_INFO(
                f'Validating configuration for environment: {validator.environment}'
            )
        )
        self.stdout.write('=' * 80)
        self.stdout.write('')
        
        try:
            is_valid, errors = validator.validate(fail_on_error=not no_fail)
            
            if is_valid:
                self.stdout.write(
                    self.style.SUCCESS('✓ Configuration validation passed!')
                )
                self.stdout.write('')
                self.stdout.write('All required environment variables are present.')
            else:
                self.stdout.write(
                    self.style.ERROR('✗ Configuration validation failed!')
                )
                self.stdout.write('')
                self.stdout.write('The following errors were found:')
                self.stdout.write('')
                
                for i, error in enumerate(errors, 1):
                    self.stdout.write(f'{i}. {error}')
                    self.stdout.write('')
                
                if not no_fail:
                    self.stdout.write(
                        self.style.WARNING(
                            'Use --no-fail to continue despite validation errors'
                        )
                    )
        
        except ConfigValidationError as e:
            self.stdout.write(self.style.ERROR(str(e)))
            raise
        
        self.stdout.write('=' * 80)
    
    def export_documentation(self, validator, output_path):
        """Export environment variables documentation"""
        self.stdout.write('=' * 80)
        self.stdout.write(
            self.style.HTTP_INFO('Exporting environment variables documentation')
        )
        self.stdout.write('=' * 80)
        self.stdout.write('')
        
        try:
            validator.export_documentation(output_path)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Documentation exported successfully to: {output_path}'
                )
            )
            self.stdout.write('')
            self.stdout.write('You can now commit this file to version control.')
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to export documentation: {e}')
            )
            raise
        
        self.stdout.write('=' * 80)
