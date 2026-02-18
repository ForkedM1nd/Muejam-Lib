"""
Celery Tasks for GDPR Data Export and Deletion

Async tasks for processing data exports and account deletions.
"""

import logging
from celery import shared_task
from .data_export_service import DataExportService
from .account_deletion_service import AccountDeletionService
from .email_service import send_export_ready_email, send_deletion_complete_email

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_data_export(self, export_request_id: str):
    """
    Generate user data export asynchronously.
    
    Args:
        export_request_id: ID of the export request
        
    Requirements: 10.2, 10.4
    """
    try:
        service = DataExportService()
        
        # Generate export (this is an async function, so we need to run it)
        import asyncio
        result = asyncio.run(service.generate_export(export_request_id))
        
        # Send email notification
        if result['status'] == 'COMPLETED':
            asyncio.run(send_export_ready_email(
                user_id=result['user_id'],
                download_url=result['download_url'],
                expires_at=result['expires_at']
            ))
        
        logger.info(f"Data export task completed: {export_request_id}")
        return result
        
    except Exception as e:
        logger.error(f"Data export task failed: {export_request_id}, error: {str(e)}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task
def process_scheduled_deletions():
    """
    Process all scheduled account deletions that are due.
    
    This task should be run daily via cron.
    
    Requirements: 10.8, 10.11, 10.13
    """
    try:
        service = AccountDeletionService()
        
        import asyncio
        result = asyncio.run(service.process_scheduled_deletions())
        
        # Send final confirmation emails for completed deletions
        for user_id in result['user_ids']:
            # TODO: Get user email before deletion
            user_email = f"user_{user_id}@example.com"
            asyncio.run(send_deletion_complete_email(user_id, user_email))
        
        logger.info(
            f"Scheduled deletions processed",
            extra={
                'total': result['total'],
                'successful': result['successful'],
                'failed': result['failed']
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Scheduled deletions task failed: {str(e)}")
        raise

