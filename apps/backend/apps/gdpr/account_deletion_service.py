"""
Account Deletion Service

Handles account deletion requests with 30-day retention period and anonymization.
Implements data_deletion functionality for GDPR right to be forgotten.

Requirements:
- 10.6: Provide "Delete My Account" feature requiring password confirmation
- 10.7: Send confirmation email with cancellation link
- 10.8: Complete deletion within 30 days unless cancelled
- 10.9: Remove all PII and replace content author with "Deleted User"
- 10.10: Retain content in soft-deleted state
- 10.11: Permanently delete after 30-day retention
- 10.13: Send final confirmation email
- 10.14: Allow cancellation within 30-day window
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from prisma import Prisma
from prisma.enums import DeletionStatus

logger = logging.getLogger(__name__)


class AccountDeletionService:
    """Service for managing account deletion requests and anonymization"""
    
    def __init__(self):
        self.db = Prisma()
    
    async def create_deletion_request(self, user_id: str) -> Dict[str, Any]:
        """
        Create a new account deletion request.
        
        Args:
            user_id: ID of the user requesting deletion
            
        Returns:
            Deletion request dictionary
            
        Requirements: 10.6, 10.7
        """
        await self.db.connect()
        try:
            # Check if there's already a pending deletion request
            existing_request = await self.db.deletionrequest.find_first(
                where={
                    'user_id': user_id,
                    'status': DeletionStatus.PENDING
                }
            )
            
            if existing_request:
                return {
                    'id': existing_request.id,
                    'user_id': existing_request.user_id,
                    'status': existing_request.status,
                    'requested_at': existing_request.requested_at.isoformat(),
                    'scheduled_deletion_at': existing_request.scheduled_deletion_at.isoformat(),
                    'message': 'Deletion request already exists'
                }
            
            # Create new deletion request with 30-day retention
            scheduled_deletion_at = datetime.utcnow() + timedelta(days=30)
            
            deletion_request = await self.db.deletionrequest.create(
                data={
                    'user_id': user_id,
                    'scheduled_deletion_at': scheduled_deletion_at,
                    'status': DeletionStatus.PENDING
                }
            )
            
            logger.info(
                f"Account deletion request created",
                extra={
                    'user_id': user_id,
                    'request_id': deletion_request.id,
                    'scheduled_deletion_at': scheduled_deletion_at.isoformat()
                }
            )
            
            return {
                'id': deletion_request.id,
                'user_id': deletion_request.user_id,
                'status': deletion_request.status,
                'requested_at': deletion_request.requested_at.isoformat(),
                'scheduled_deletion_at': deletion_request.scheduled_deletion_at.isoformat()
            }
        finally:
            await self.db.disconnect()
    
    async def cancel_deletion_request(self, deletion_request_id: str, user_id: str) -> Dict[str, Any]:
        """
        Cancel a pending deletion request.
        
        Args:
            deletion_request_id: ID of the deletion request
            user_id: ID of the user (for verification)
            
        Returns:
            Updated deletion request dictionary
            
        Requirements: 10.14
        """
        await self.db.connect()
        try:
            # Get deletion request
            deletion_request = await self.db.deletionrequest.find_unique(
                where={'id': deletion_request_id}
            )
            
            if not deletion_request:
                raise ValueError(f"Deletion request not found: {deletion_request_id}")
            
            # Verify ownership
            if deletion_request.user_id != user_id:
                raise PermissionError("User does not own this deletion request")
            
            # Check if already cancelled or completed
            if deletion_request.status != DeletionStatus.PENDING:
                raise ValueError(f"Cannot cancel deletion request with status: {deletion_request.status}")
            
            # Cancel the request
            updated_request = await self.db.deletionrequest.update(
                where={'id': deletion_request_id},
                data={
                    'status': DeletionStatus.CANCELLED,
                    'cancelled_at': datetime.utcnow()
                }
            )
            
            logger.info(
                f"Account deletion request cancelled",
                extra={
                    'user_id': user_id,
                    'request_id': deletion_request_id
                }
            )
            
            return {
                'id': updated_request.id,
                'user_id': updated_request.user_id,
                'status': updated_request.status,
                'requested_at': updated_request.requested_at.isoformat(),
                'scheduled_deletion_at': updated_request.scheduled_deletion_at.isoformat(),
                'cancelled_at': updated_request.cancelled_at.isoformat() if updated_request.cancelled_at else None
            }
        finally:
            await self.db.disconnect()
    
    async def anonymize_account(self, user_id: str) -> Dict[str, Any]:
        """
        Anonymize user account by removing PII and marking as deleted.
        
        This is the soft-delete phase that happens immediately or after 30 days.
        
        Args:
            user_id: ID of the user to anonymize
            
        Returns:
            Summary of anonymization actions
            
        Requirements: 10.9, 10.10
        """
        await self.db.connect()
        try:
            # Get user profile
            profile = await self.db.userprofile.find_unique(
                where={'id': user_id}
            )
            
            if not profile:
                raise ValueError(f"User profile not found: {user_id}")
            
            # Store email for final notification
            original_email = profile.clerk_user_id  # TODO: Get actual email from Clerk
            
            # Anonymize profile
            await self.db.userprofile.update(
                where={'id': user_id},
                data={
                    'display_name': 'Deleted User',
                    'bio': None,
                    'avatar_key': None,
                    'handle': f'deleted_{user_id[:8]}'  # Keep unique but anonymized
                }
            )
            
            # Delete sensitive data
            deleted_counts = {
                'totp_devices': 0,
                'backup_codes': 0,
                'api_keys': 0,
                'email_verifications': 0,
                'auth_events': 0
            }
            
            # Delete 2FA devices
            totp_result = await self.db.totpdevice.delete_many(
                where={'user_id': user_id}
            )
            deleted_counts['totp_devices'] = totp_result
            
            # Delete backup codes
            backup_result = await self.db.backupcode.delete_many(
                where={'user_id': user_id}
            )
            deleted_counts['backup_codes'] = backup_result
            
            # Delete API keys
            api_key_result = await self.db.apikey.delete_many(
                where={'user_id': user_id}
            )
            deleted_counts['api_keys'] = api_key_result
            
            # Delete email verifications
            email_verify_result = await self.db.emailverification.delete_many(
                where={'user_id': user_id}
            )
            deleted_counts['email_verifications'] = email_verify_result
            
            # Keep auth events for audit but could optionally delete
            # auth_result = await self.db.authenticationevent.delete_many(
            #     where={'user_id': user_id}
            # )
            # deleted_counts['auth_events'] = auth_result
            
            logger.info(
                f"Account anonymized",
                extra={
                    'user_id': user_id,
                    'deleted_counts': deleted_counts
                }
            )
            
            return {
                'user_id': user_id,
                'anonymized': True,
                'original_email': original_email,
                'deleted_counts': deleted_counts
            }
        finally:
            await self.db.disconnect()
    
    async def permanently_delete_account(self, user_id: str) -> Dict[str, Any]:
        """
        Permanently delete all user data after 30-day retention period.
        
        This is the hard-delete phase that happens after the retention period.
        
        Args:
            user_id: ID of the user to permanently delete
            
        Returns:
            Summary of deletion actions
            
        Requirements: 10.11
        """
        await self.db.connect()
        try:
            deleted_counts = {
                'profile': 0,
                'stories': 0,
                'chapters': 0,
                'whispers': 0,
                'likes': 0,
                'follows': 0,
                'reading_progress': 0,
                'bookmarks': 0,
                'highlights': 0,
                'notifications': 0,
                'reports': 0,
                'consents': 0
            }
            
            # Delete user-generated content
            # Note: Consider keeping stories/chapters with anonymized author
            # For now, we'll delete everything
            
            # Delete whisper likes
            likes_result = await self.db.whisperlike.delete_many(
                where={'user_id': user_id}
            )
            deleted_counts['likes'] = likes_result
            
            # Delete whispers
            whispers_result = await self.db.whisper.delete_many(
                where={'user_id': user_id}
            )
            deleted_counts['whispers'] = whispers_result
            
            # Delete follows (as follower)
            follows_follower_result = await self.db.follow.delete_many(
                where={'follower_id': user_id}
            )
            
            # Delete follows (as following)
            follows_following_result = await self.db.follow.delete_many(
                where={'following_id': user_id}
            )
            deleted_counts['follows'] = follows_follower_result + follows_following_result
            
            # Delete reading progress
            progress_result = await self.db.readingprogress.delete_many(
                where={'user_id': user_id}
            )
            deleted_counts['reading_progress'] = progress_result
            
            # Delete bookmarks
            bookmarks_result = await self.db.bookmark.delete_many(
                where={'user_id': user_id}
            )
            deleted_counts['bookmarks'] = bookmarks_result
            
            # Delete highlights
            highlights_result = await self.db.highlight.delete_many(
                where={'user_id': user_id}
            )
            deleted_counts['highlights'] = highlights_result
            
            # Delete notifications
            notifications_result = await self.db.notification.delete_many(
                where={'user_id': user_id}
            )
            deleted_counts['notifications'] = notifications_result
            
            # Delete reports made by user
            reports_result = await self.db.report.delete_many(
                where={'reporter_id': user_id}
            )
            deleted_counts['reports'] = reports_result
            
            # Delete consent records
            consents_result = await self.db.userconsent.delete_many(
                where={'user_id': user_id}
            )
            deleted_counts['consents'] = consents_result
            
            # Delete chapters from user's stories
            stories = await self.db.story.find_many(
                where={'author_id': user_id},
                select={'id': True}
            )
            story_ids = [story.id for story in stories]
            
            if story_ids:
                chapters_result = await self.db.chapter.delete_many(
                    where={'story_id': {'in': story_ids}}
                )
                deleted_counts['chapters'] = chapters_result
            
            # Delete stories
            stories_result = await self.db.story.delete_many(
                where={'author_id': user_id}
            )
            deleted_counts['stories'] = stories_result
            
            # Finally, delete the user profile
            await self.db.userprofile.delete(
                where={'id': user_id}
            )
            deleted_counts['profile'] = 1
            
            logger.info(
                f"Account permanently deleted",
                extra={
                    'user_id': user_id,
                    'deleted_counts': deleted_counts
                }
            )
            
            return {
                'user_id': user_id,
                'permanently_deleted': True,
                'deleted_counts': deleted_counts
            }
        finally:
            await self.db.disconnect()
    
    async def process_scheduled_deletions(self) -> Dict[str, Any]:
        """
        Process all deletion requests that are due for execution.
        
        This should be run as a scheduled task (e.g., daily cron job).
        
        Returns:
            Summary of processed deletions
            
        Requirements: 10.8, 10.11
        """
        await self.db.connect()
        try:
            # Find all pending deletion requests that are due
            now = datetime.utcnow()
            
            due_deletions = await self.db.deletionrequest.find_many(
                where={
                    'status': DeletionStatus.PENDING,
                    'scheduled_deletion_at': {'lte': now}
                }
            )
            
            processed = {
                'total': len(due_deletions),
                'successful': 0,
                'failed': 0,
                'user_ids': []
            }
            
            for deletion_request in due_deletions:
                try:
                    user_id = deletion_request.user_id
                    
                    # Anonymize account first (soft delete)
                    anonymize_result = await self.anonymize_account(user_id)
                    
                    # Permanently delete (hard delete)
                    delete_result = await self.permanently_delete_account(user_id)
                    
                    # Update deletion request status
                    await self.db.deletionrequest.update(
                        where={'id': deletion_request.id},
                        data={
                            'status': DeletionStatus.COMPLETED,
                            'completed_at': datetime.utcnow()
                        }
                    )
                    
                    processed['successful'] += 1
                    processed['user_ids'].append(user_id)
                    
                    logger.info(
                        f"Scheduled deletion processed",
                        extra={
                            'user_id': user_id,
                            'request_id': deletion_request.id
                        }
                    )
                    
                except Exception as e:
                    processed['failed'] += 1
                    logger.error(
                        f"Failed to process scheduled deletion",
                        extra={
                            'user_id': deletion_request.user_id,
                            'request_id': deletion_request.id,
                            'error': str(e)
                        }
                    )
            
            return processed
        finally:
            await self.db.disconnect()
    
    async def get_deletion_request(self, deletion_request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get deletion request by ID.
        
        Args:
            deletion_request_id: ID of the deletion request
            
        Returns:
            Deletion request dictionary or None
        """
        await self.db.connect()
        try:
            deletion_request = await self.db.deletionrequest.find_unique(
                where={'id': deletion_request_id}
            )
            
            if not deletion_request:
                return None
            
            return {
                'id': deletion_request.id,
                'user_id': deletion_request.user_id,
                'status': deletion_request.status,
                'requested_at': deletion_request.requested_at.isoformat(),
                'scheduled_deletion_at': deletion_request.scheduled_deletion_at.isoformat(),
                'cancelled_at': deletion_request.cancelled_at.isoformat() if deletion_request.cancelled_at else None,
                'completed_at': deletion_request.completed_at.isoformat() if deletion_request.completed_at else None
            }
        finally:
            await self.db.disconnect()
