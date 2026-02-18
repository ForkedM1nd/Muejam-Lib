"""
Data Export Service

Generates comprehensive user data exports for GDPR compliance.

Requirements:
- 10.1: Provide "Download My Data" feature
- 10.2: Generate comprehensive JSON file with all user data
- 10.3: Include profile, stories, chapters, whispers, comments, likes, follows, reading history
- 10.4: Send email notification with download link
- 10.5: Expire download links after 7 days
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from prisma import Prisma
from prisma.enums import DataExportStatus
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DataExportService:
    """Service for generating and managing user data exports"""
    
    def __init__(self):
        self.db = Prisma()
        self.s3_client = boto3.client('s3')
        self.bucket_name = 'muejam-data-exports'  # Configure via environment variable
    
    async def create_export_request(self, user_id: str) -> Dict[str, Any]:
        """
        Create a new data export request.
        
        Args:
            user_id: ID of the user requesting export
            
        Returns:
            Export request dictionary
            
        Requirements: 10.1
        """
        await self.db.connect()
        try:
            # Create export request
            export_request = await self.db.dataexportrequest.create(
                data={
                    'user_id': user_id,
                    'status': DataExportStatus.PENDING
                }
            )
            
            logger.info(
                f"Data export request created",
                extra={
                    'user_id': user_id,
                    'request_id': export_request.id
                }
            )
            
            return {
                'id': export_request.id,
                'user_id': export_request.user_id,
                'status': export_request.status,
                'requested_at': export_request.requested_at.isoformat()
            }
        finally:
            await self.db.disconnect()
    
    async def generate_export(self, export_request_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive data export for a user.
        
        This method should be called asynchronously (e.g., via Celery task).
        
        Args:
            export_request_id: ID of the export request
            
        Returns:
            Updated export request dictionary
            
        Requirements: 10.2, 10.3
        """
        await self.db.connect()
        try:
            # Get export request
            export_request = await self.db.dataexportrequest.find_unique(
                where={'id': export_request_id}
            )
            
            if not export_request:
                raise ValueError(f"Export request not found: {export_request_id}")
            
            # Update status to processing
            await self.db.dataexportrequest.update(
                where={'id': export_request_id},
                data={'status': DataExportStatus.PROCESSING}
            )
            
            user_id = export_request.user_id
            
            try:
                # Gather all user data
                data = {
                    'export_info': {
                        'generated_at': datetime.utcnow().isoformat(),
                        'user_id': user_id,
                        'format_version': '1.0'
                    },
                    'profile': await self._export_profile(user_id),
                    'stories': await self._export_stories(user_id),
                    'chapters': await self._export_chapters(user_id),
                    'whispers': await self._export_whispers(user_id),
                    'likes': await self._export_likes(user_id),
                    'follows': await self._export_follows(user_id),
                    'reading_progress': await self._export_reading_progress(user_id),
                    'bookmarks': await self._export_bookmarks(user_id),
                    'highlights': await self._export_highlights(user_id),
                    'notifications': await self._export_notifications(user_id),
                    'consent_records': await self._export_consent_records(user_id)
                }
                
                # Generate JSON file
                json_data = json.dumps(data, indent=2, default=str)
                
                # Upload to S3
                s3_key = f'exports/{user_id}/{export_request_id}.json'
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=json_data.encode('utf-8'),
                    ContentType='application/json'
                )
                
                # Generate presigned URL (7 day expiration)
                download_url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': s3_key
                    },
                    ExpiresIn=604800  # 7 days in seconds
                )
                
                expires_at = datetime.utcnow() + timedelta(days=7)
                
                # Update export request
                updated_request = await self.db.dataexportrequest.update(
                    where={'id': export_request_id},
                    data={
                        'status': DataExportStatus.COMPLETED,
                        'completed_at': datetime.utcnow(),
                        'download_url': download_url,
                        'expires_at': expires_at
                    }
                )
                
                logger.info(
                    f"Data export completed",
                    extra={
                        'user_id': user_id,
                        'request_id': export_request_id,
                        'data_size': len(json_data)
                    }
                )
                
                return {
                    'id': updated_request.id,
                    'user_id': updated_request.user_id,
                    'status': updated_request.status,
                    'requested_at': updated_request.requested_at.isoformat(),
                    'completed_at': updated_request.completed_at.isoformat() if updated_request.completed_at else None,
                    'download_url': updated_request.download_url,
                    'expires_at': updated_request.expires_at.isoformat() if updated_request.expires_at else None
                }
                
            except Exception as e:
                # Update status to failed
                await self.db.dataexportrequest.update(
                    where={'id': export_request_id},
                    data={
                        'status': DataExportStatus.FAILED,
                        'error_message': str(e)
                    }
                )
                
                logger.error(
                    f"Data export failed",
                    extra={
                        'user_id': user_id,
                        'request_id': export_request_id,
                        'error': str(e)
                    }
                )
                
                raise
        finally:
            await self.db.disconnect()
    
    async def get_export_request(self, export_request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get export request by ID.
        
        Args:
            export_request_id: ID of the export request
            
        Returns:
            Export request dictionary or None
        """
        await self.db.connect()
        try:
            export_request = await self.db.dataexportrequest.find_unique(
                where={'id': export_request_id}
            )
            
            if not export_request:
                return None
            
            return {
                'id': export_request.id,
                'user_id': export_request.user_id,
                'status': export_request.status,
                'requested_at': export_request.requested_at.isoformat(),
                'completed_at': export_request.completed_at.isoformat() if export_request.completed_at else None,
                'download_url': export_request.download_url,
                'expires_at': export_request.expires_at.isoformat() if export_request.expires_at else None,
                'error_message': export_request.error_message
            }
        finally:
            await self.db.disconnect()
    
    async def _export_profile(self, user_id: str) -> Dict[str, Any]:
        """Export user profile information"""
        profile = await self.db.userprofile.find_unique(
            where={'id': user_id}
        )
        
        if not profile:
            return {}
        
        return {
            'id': profile.id,
            'clerk_user_id': profile.clerk_user_id,
            'handle': profile.handle,
            'display_name': profile.display_name,
            'bio': profile.bio,
            'avatar_key': profile.avatar_key,
            'age_verified': profile.age_verified,
            'age_verified_at': profile.age_verified_at.isoformat() if profile.age_verified_at else None,
            'created_at': profile.created_at.isoformat(),
            'updated_at': profile.updated_at.isoformat()
        }
    
    async def _export_stories(self, user_id: str) -> list:
        """Export user's stories"""
        stories = await self.db.story.find_many(
            where={'author_id': user_id},
            order={'created_at': 'desc'}
        )
        
        return [
            {
                'id': story.id,
                'slug': story.slug,
                'title': story.title,
                'blurb': story.blurb,
                'cover_key': story.cover_key,
                'published': story.published,
                'published_at': story.published_at.isoformat() if story.published_at else None,
                'created_at': story.created_at.isoformat(),
                'updated_at': story.updated_at.isoformat()
            }
            for story in stories
        ]
    
    async def _export_chapters(self, user_id: str) -> list:
        """Export chapters from user's stories"""
        # Get user's stories first
        stories = await self.db.story.find_many(
            where={'author_id': user_id},
            select={'id': True}
        )
        
        story_ids = [story.id for story in stories]
        
        if not story_ids:
            return []
        
        chapters = await self.db.chapter.find_many(
            where={'story_id': {'in': story_ids}},
            order={'created_at': 'desc'}
        )
        
        return [
            {
                'id': chapter.id,
                'story_id': chapter.story_id,
                'chapter_number': chapter.chapter_number,
                'title': chapter.title,
                'content': chapter.content,
                'published': chapter.published,
                'published_at': chapter.published_at.isoformat() if chapter.published_at else None,
                'created_at': chapter.created_at.isoformat(),
                'updated_at': chapter.updated_at.isoformat()
            }
            for chapter in chapters
        ]
    
    async def _export_whispers(self, user_id: str) -> list:
        """Export user's whispers"""
        whispers = await self.db.whisper.find_many(
            where={'user_id': user_id},
            order={'created_at': 'desc'}
        )
        
        return [
            {
                'id': whisper.id,
                'content': whisper.content,
                'media_key': whisper.media_key,
                'scope': whisper.scope,
                'story_id': whisper.story_id,
                'highlight_id': whisper.highlight_id,
                'parent_id': whisper.parent_id,
                'created_at': whisper.created_at.isoformat()
            }
            for whisper in whispers
        ]
    
    async def _export_likes(self, user_id: str) -> list:
        """Export user's whisper likes"""
        likes = await self.db.whisperlike.find_many(
            where={'user_id': user_id},
            order={'created_at': 'desc'}
        )
        
        return [
            {
                'whisper_id': like.whisper_id,
                'created_at': like.created_at.isoformat()
            }
            for like in likes
        ]
    
    async def _export_follows(self, user_id: str) -> Dict[str, list]:
        """Export user's follows (following and followers)"""
        following = await self.db.follow.find_many(
            where={'follower_id': user_id},
            order={'created_at': 'desc'}
        )
        
        followers = await self.db.follow.find_many(
            where={'following_id': user_id},
            order={'created_at': 'desc'}
        )
        
        return {
            'following': [
                {
                    'user_id': follow.following_id,
                    'created_at': follow.created_at.isoformat()
                }
                for follow in following
            ],
            'followers': [
                {
                    'user_id': follow.follower_id,
                    'created_at': follow.created_at.isoformat()
                }
                for follow in followers
            ]
        }
    
    async def _export_reading_progress(self, user_id: str) -> list:
        """Export user's reading progress"""
        progress = await self.db.readingprogress.find_many(
            where={'user_id': user_id},
            order={'updated_at': 'desc'}
        )
        
        return [
            {
                'chapter_id': p.chapter_id,
                'offset': p.offset,
                'updated_at': p.updated_at.isoformat()
            }
            for p in progress
        ]
    
    async def _export_bookmarks(self, user_id: str) -> list:
        """Export user's bookmarks"""
        bookmarks = await self.db.bookmark.find_many(
            where={'user_id': user_id},
            order={'created_at': 'desc'}
        )
        
        return [
            {
                'chapter_id': bookmark.chapter_id,
                'offset': bookmark.offset,
                'created_at': bookmark.created_at.isoformat()
            }
            for bookmark in bookmarks
        ]
    
    async def _export_highlights(self, user_id: str) -> list:
        """Export user's highlights"""
        highlights = await self.db.highlight.find_many(
            where={'user_id': user_id},
            order={'created_at': 'desc'}
        )
        
        return [
            {
                'chapter_id': highlight.chapter_id,
                'start_offset': highlight.start_offset,
                'end_offset': highlight.end_offset,
                'created_at': highlight.created_at.isoformat()
            }
            for highlight in highlights
        ]
    
    async def _export_notifications(self, user_id: str) -> list:
        """Export user's notifications"""
        notifications = await self.db.notification.find_many(
            where={'user_id': user_id},
            order={'created_at': 'desc'}
        )
        
        return [
            {
                'type': notification.type,
                'actor_id': notification.actor_id,
                'whisper_id': notification.whisper_id,
                'read_at': notification.read_at.isoformat() if notification.read_at else None,
                'created_at': notification.created_at.isoformat()
            }
            for notification in notifications
        ]
    
    async def _export_consent_records(self, user_id: str) -> list:
        """Export user's consent records"""
        consents = await self.db.userconsent.find_many(
            where={'user_id': user_id},
            order={'consented_at': 'desc'}
        )
        
        return [
            {
                'document_id': consent.document_id,
                'consented_at': consent.consented_at.isoformat(),
                'ip_address': consent.ip_address,
                'user_agent': consent.user_agent
            }
            for consent in consents
        ]
