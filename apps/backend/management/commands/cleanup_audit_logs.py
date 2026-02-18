"""
Django management command to clean up old audit logs based on retention policy.

Usage:
    python manage.py cleanup_audit_logs --older-than 90 --type authentication
    python manage.py cleanup_audit_logs --older-than 730 --type moderation --dry-run
"""

from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
import asyncio
from prisma import Prisma
from prisma.enums import AuditActionType


class Command(BaseCommand):
    help = 'Clean up old audit logs based on retention policy'
    
    # Retention policies (in days)
    RETENTION_POLICIES = {
        'authentication': 90,
        'moderation': 730,  # 2 years
        'administrative': 2555,  # 7 years
        'data_access': 2555,  # 7 years
        'api_operations': 90
    }
    
    # Action type mappings
    ACTION_TYPE_CATEGORIES = {
        'authentication': [
            AuditActionType.LOGIN_SUCCESS,
            AuditActionType.LOGIN_FAILED,
            AuditActionType.LOGOUT,
            AuditActionType.PASSWORD_CHANGE,
            AuditActionType.TWO_FA_ENABLED,
            AuditActionType.TWO_FA_DISABLED
        ],
        'moderation': [
            AuditActionType.CONTENT_TAKEDOWN,
            AuditActionType.USER_SUSPENSION,
            AuditActionType.REPORT_RESOLUTION,
            AuditActionType.ROLE_ASSIGNMENT
        ],
        'administrative': [
            AuditActionType.CONFIG_CHANGE,
            AuditActionType.USER_ROLE_CHANGE,
            AuditActionType.SYSTEM_SETTINGS_UPDATE
        ],
        'data_access': [
            AuditActionType.DATA_EXPORT_REQUEST,
            AuditActionType.ACCOUNT_DELETION_REQUEST,
            AuditActionType.PRIVACY_SETTINGS_CHANGE
        ],
        'api_operations': [
            AuditActionType.API_KEY_CREATED,
            AuditActionType.API_KEY_REVOKED
        ]
    }
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--older-than',
            type=int,
            help='Delete logs older than N days'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['authentication', 'moderation', 'administrative', 'data_access', 'api_operations', 'all'],
            default='all',
            help='Type of logs to clean up'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--archive',
            action='store_true',
            help='Archive logs before deletion'
        )
        parser.add_argument(
            '--archive-path',
            type=str,
            default='/var/backups/audit-logs',
            help='Path to archive logs'
        )
    
    def handle(self, *args, **options):
        asyncio.run(self.async_handle(*args, **options))
    
    async def async_handle(self, *args, **options):
        older_than = options.get('older_than')
        log_type = options.get('type')
        dry_run = options.get('dry_run')
        archive = options.get('archive')
        archive_path = options.get('archive_path')
        
        # Use retention policy if --older-than not specified
        if not older_than:
            if log_type == 'all':
                self.stdout.write(
                    self.style.ERROR('Must specify --older-than when using --type all')
                )
                return
            older_than = self.RETENTION_POLICIES.get(log_type, 90)
        
        cutoff_date = datetime.now() - timedelta(days=older_than)
        
        self.stdout.write(
            self.style.WARNING(f'\nAudit Log Cleanup')
        )
        self.stdout.write(f'Type: {log_type}')
        self.stdout.write(f'Cutoff date: {cutoff_date.isoformat()}')
        self.stdout.write(f'Dry run: {dry_run}')
        self.stdout.write(f'Archive: {archive}\n')
        
        db = Prisma()
        await db.connect()
        
        try:
            # Get action types to clean up
            if log_type == 'all':
                action_types = None  # All types
            else:
                action_types = self.ACTION_TYPE_CATEGORIES.get(log_type, [])
            
            # Build query
            where_clause = {'created_at': {'lt': cutoff_date}}
            if action_types:
                where_clause['action_type'] = {'in': action_types}
            
            # Count logs to be deleted
            count = await db.auditlog.count(where=where_clause)
            
            if count == 0:
                self.stdout.write(
                    self.style.SUCCESS('No logs to clean up')
                )
                return
            
            self.stdout.write(
                self.style.WARNING(f'Found {count} logs to clean up')
            )
            
            # Archive if requested
            if archive and not dry_run:
                self.stdout.write('Archiving logs...')
                await self.archive_logs(db, where_clause, archive_path)
                self.stdout.write(
                    self.style.SUCCESS('Logs archived successfully')
                )
            
            # Delete logs
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f'DRY RUN: Would delete {count} logs')
                )
                
                # Show sample of logs that would be deleted
                sample = await db.auditlog.find_many(
                    where=where_clause,
                    take=5,
                    order={'created_at': 'asc'}
                )
                
                self.stdout.write('\nSample logs that would be deleted:')
                for log in sample:
                    self.stdout.write(
                        f'  - {log.created_at.isoformat()} | {log.action_type} | User: {log.user_id}'
                    )
            else:
                self.stdout.write('Deleting logs...')
                result = await db.auditlog.delete_many(where=where_clause)
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted {result} logs')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
            raise
        finally:
            await db.disconnect()
    
    async def archive_logs(self, db, where_clause, archive_path):
        """Archive logs before deletion"""
        import json
        import os
        from datetime import datetime
        
        # Create archive directory
        os.makedirs(archive_path, exist_ok=True)
        
        # Fetch logs to archive
        logs = await db.auditlog.find_many(
            where=where_clause,
            order={'created_at': 'asc'}
        )
        
        # Create archive file
        archive_file = os.path.join(
            archive_path,
            f'audit_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jsonl'
        )
        
        # Write logs to file (JSONL format)
        with open(archive_file, 'w') as f:
            for log in logs:
                log_dict = {
                    'id': log.id,
                    'user_id': log.user_id,
                    'action_type': log.action_type,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id,
                    'ip_address': log.ip_address,
                    'user_agent': log.user_agent,
                    'result': log.result,
                    'metadata': log.metadata,
                    'created_at': log.created_at.isoformat()
                }
                f.write(json.dumps(log_dict) + '\n')
        
        self.stdout.write(f'Archived to: {archive_file}')
