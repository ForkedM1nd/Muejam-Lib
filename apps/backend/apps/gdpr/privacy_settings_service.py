"""
Privacy Settings Service

Manages user privacy settings and consent management records.

Requirements:
- 11.1: Provide privacy settings page with granular controls
- 11.2-11.7: Control various privacy settings
- 11.8: Apply changes immediately
- 11.10: Store consent records with timestamps
"""

import logging
from datetime import datetime
from prisma import Prisma
from prisma.models import PrivacySettings, UserConsent, LegalDocument
from prisma.enums import VisibilityLevel, CommentPermission, FollowerApproval

logger = logging.getLogger(__name__)


class PrivacySettingsService:
    """Service for managing user privacy settings."""
    
    async def get_or_create_settings(self, user_id: str) -> dict:
        """
        Get user's privacy settings or create default settings.
        
        Args:
            user_id: User ID
            
        Returns:
            Privacy settings dictionary
            
        Requirements: 11.1
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Try to get existing settings
            settings = await db.privacysettings.find_unique(
                where={'user_id': user_id}
            )
            
            # Create default settings if none exist
            if not settings:
                settings = await db.privacysettings.create(
                    data={
                        'user_id': user_id,
                        'profile_visibility': VisibilityLevel.PUBLIC,
                        'reading_history_visibility': VisibilityLevel.PRIVATE,
                        'analytics_opt_out': False,
                        'marketing_emails': True,
                        'comment_permissions': CommentPermission.ANYONE,
                        'follower_approval_required': FollowerApproval.ANYONE
                    }
                )
            
            return self._serialize_settings(settings)
            
        finally:
            await db.disconnect()
    
    async def update_settings(self, user_id: str, updates: dict) -> dict:
        """
        Update user's privacy settings.
        
        Args:
            user_id: User ID
            updates: Dictionary of settings to update
            
        Returns:
            Updated privacy settings dictionary
            
        Requirements: 11.1-11.8, 11.10
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Ensure settings exist
            await self.get_or_create_settings(user_id)
            
            # Prepare update data
            update_data = {}
            
            # Validate and add each field
            if 'profile_visibility' in updates:
                update_data['profile_visibility'] = VisibilityLevel(updates['profile_visibility'])
            
            if 'reading_history_visibility' in updates:
                update_data['reading_history_visibility'] = VisibilityLevel(updates['reading_history_visibility'])
            
            if 'analytics_opt_out' in updates:
                update_data['analytics_opt_out'] = bool(updates['analytics_opt_out'])
            
            if 'marketing_emails' in updates:
                update_data['marketing_emails'] = bool(updates['marketing_emails'])
            
            if 'comment_permissions' in updates:
                update_data['comment_permissions'] = CommentPermission(updates['comment_permissions'])
            
            if 'follower_approval_required' in updates:
                update_data['follower_approval_required'] = FollowerApproval(updates['follower_approval_required'])
            
            # Update settings
            settings = await db.privacysettings.update(
                where={'user_id': user_id},
                data=update_data
            )
            
            # Record consent for privacy setting changes
            await self._record_privacy_consent(db, user_id, updates)
            
            logger.info(f"Privacy settings updated for user {user_id}")
            
            return self._serialize_settings(settings)
            
        finally:
            await db.disconnect()
    
    async def get_consent_history(self, user_id: str) -> list:
        """
        Get user's consent history.
        
        Args:
            user_id: User ID
            
        Returns:
            List of consent records
            
        Requirements: 11.11
        """
        db = Prisma()
        await db.connect()
        
        try:
            consents = await db.userconsent.find_many(
                where={'user_id': user_id},
                include={'document': True},
                order={'consented_at': 'desc'}
            )
            
            return [
                {
                    'id': consent.id,
                    'document_type': consent.document.document_type,
                    'document_version': consent.document.version,
                    'consented_at': consent.consented_at.isoformat(),
                    'ip_address': consent.ip_address
                }
                for consent in consents
            ]
            
        finally:
            await db.disconnect()
    
    async def withdraw_consent(self, user_id: str, consent_type: str) -> dict:
        """
        Withdraw consent for optional data processing.
        
        Args:
            user_id: User ID
            consent_type: Type of consent to withdraw (e.g., 'analytics', 'marketing')
            
        Returns:
            Updated privacy settings
            
        Requirements: 11.12, 11.13
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Map consent types to settings fields
            consent_mapping = {
                'analytics': {'analytics_opt_out': True},
                'marketing': {'marketing_emails': False}
            }
            
            if consent_type not in consent_mapping:
                raise ValueError(f"Invalid consent type: {consent_type}")
            
            # Update settings to reflect withdrawn consent
            updates = consent_mapping[consent_type]
            settings = await self.update_settings(user_id, updates)
            
            logger.info(f"Consent withdrawn for user {user_id}: {consent_type}")
            
            return settings
            
        finally:
            await db.disconnect()
    
    async def _record_privacy_consent(self, db: Prisma, user_id: str, changes: dict):
        """
        Record consent for privacy setting changes.
        
        Args:
            db: Prisma database connection
            user_id: User ID
            changes: Dictionary of changed settings
            
        Requirements: 11.10
        """
        # Get or create a privacy policy document for consent tracking
        privacy_doc = await db.legaldocument.find_first(
            where={
                'document_type': 'PRIVACY',
                'is_active': True
            }
        )
        
        if privacy_doc:
            # Record consent with metadata about what changed
            await db.userconsent.create(
                data={
                    'user_id': user_id,
                    'document_id': privacy_doc.id,
                    'ip_address': '0.0.0.0',  # Will be set by view
                    'user_agent': 'API'  # Will be set by view
                }
            )
    
    def _serialize_settings(self, settings: PrivacySettings) -> dict:
        """
        Serialize privacy settings to dictionary.
        
        Args:
            settings: PrivacySettings model instance
            
        Returns:
            Dictionary representation
        """
        return {
            'id': settings.id,
            'user_id': settings.user_id,
            'profile_visibility': settings.profile_visibility,
            'reading_history_visibility': settings.reading_history_visibility,
            'analytics_opt_out': settings.analytics_opt_out,
            'marketing_emails': settings.marketing_emails,
            'comment_permissions': settings.comment_permissions,
            'follower_approval_required': settings.follower_approval_required,
            'created_at': settings.created_at.isoformat(),
            'updated_at': settings.updated_at.isoformat()
        }
