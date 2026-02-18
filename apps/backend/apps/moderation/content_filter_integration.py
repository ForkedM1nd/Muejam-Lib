"""
Content filter integration service for automated content moderation.

This module provides integration between the content filter pipeline and
content submission endpoints, implementing requirements 4.1-4.5.
"""

import logging
from typing import Dict, Optional
from prisma import Prisma
from .content_filters import ContentFilterPipeline
from .filter_config_service import FilterConfigService

logger = logging.getLogger(__name__)


class ContentFilterIntegration:
    """
    Service for integrating content filters into content submission flow.
    
    Implements requirements:
    - 4.1: Filter profanity in content
    - 4.2: Block spam patterns
    - 4.3: Return appropriate errors for blocked content
    - 4.4: Create high-priority reports for hate speech
    - 4.5: Log automated filtering actions
    """
    
    # System user ID for automated reports (can be configured)
    SYSTEM_USER_ID = 'system'
    
    def __init__(self, db: Optional[Prisma] = None):
        """
        Initialize the content filter integration service.
        
        Args:
            db: Optional Prisma database connection
        """
        self.db = db
        self.config_service = FilterConfigService(db) if db else None
    
    async def filter_and_validate_content(
        self,
        content: str,
        content_type: str,
        content_id: Optional[str] = None
    ) -> Dict:
        """
        Filter content and return validation result.
        
        This method runs the content through all configured filters and
        determines if the content should be allowed, blocked, or flagged
        for review.
        
        Args:
            content: Text content to filter
            content_type: Type of content (story, chapter, whisper)
            content_id: Optional ID of the content (for logging flags)
            
        Returns:
            Dictionary with validation results:
            {
                'allowed': bool,  # Whether content should be allowed
                'blocked': bool,  # Whether content should be blocked
                'error_message': str,  # User-friendly error message if blocked
                'flags': list,  # List of detected issues
                'auto_actions': list,  # Automated actions to take
                'details': dict  # Detailed filter results
            }
            
        Requirements:
            - 4.1: Filter profanity
            - 4.2: Detect spam
            - 4.3: Return appropriate errors
            - 4.4: Flag hate speech
        """
        # Get configured pipeline
        if self.config_service:
            pipeline = await self.config_service.get_pipeline()
        else:
            # Use default pipeline if no config service
            pipeline = ContentFilterPipeline()
        
        # Run filters
        filter_result = pipeline.filter_content(content, content_type)
        
        # Determine if content should be blocked
        blocked = not filter_result['allowed']
        
        # Generate user-friendly error message
        error_message = None
        if blocked:
            error_message = self._generate_error_message(filter_result['flags'])
        
        # Log automated flags if content_id provided
        if content_id and filter_result['flags'] and self.config_service:
            await self._log_automated_flags(
                content_type,
                content_id,
                filter_result
            )
        
        return {
            'allowed': filter_result['allowed'],
            'blocked': blocked,
            'error_message': error_message,
            'flags': filter_result['flags'],
            'auto_actions': filter_result.get('auto_actions', []),
            'details': filter_result.get('details', {})
        }
    
    async def handle_auto_actions(
        self,
        content_type: str,
        content_id: str,
        auto_actions: list,
        filter_details: dict,
        user_id: Optional[str] = None
    ) -> None:
        """
        Handle automated actions based on filter results.
        
        Args:
            content_type: Type of content (story, chapter, whisper)
            content_id: ID of the content
            auto_actions: List of automated actions to perform
            filter_details: Detailed filter results
            user_id: Optional user ID for logging
            
        Requirements:
            - 4.4: Create high-priority reports for hate speech
            - 4.5: Log automated filtering actions
            - 4.7: Log blocked URL attempts
        """
        if not self.db:
            logger.warning("No database connection, skipping auto actions")
            return
        
        for action in auto_actions:
            if action == 'create_high_priority_report':
                await self._create_automated_report(
                    content_type,
                    content_id,
                    filter_details
                )
            elif action == 'log_blocked_url_attempt':
                await self._log_blocked_url_attempt(
                    content_type,
                    content_id,
                    filter_details,
                    user_id
                )
    
    async def _create_automated_report(
        self,
        content_type: str,
        content_id: str,
        filter_details: dict
    ) -> None:
        """
        Create an automated high-priority report for flagged content.
        
        Args:
            content_type: Type of content
            content_id: ID of the content
            filter_details: Detailed filter results
            
        Requirements:
            - 4.4: Create high-priority reports for hate speech
        """
        try:
            # Build report reason from filter details
            flags = []
            if 'hate_speech' in filter_details:
                flags.append('hate speech')
            if 'profanity' in filter_details:
                flags.append('profanity')
            if 'spam' in filter_details:
                flags.append('spam')
            
            reason = f"Automated detection: {', '.join(flags)}"
            
            # Build report data
            report_data = {
                'reporter_id': self.SYSTEM_USER_ID,
                'reason': reason,
                'status': 'PENDING'
            }
            
            # Add content-specific fields
            if content_type == 'story':
                report_data['story_id'] = content_id
            elif content_type == 'chapter':
                report_data['chapter_id'] = content_id
            elif content_type == 'whisper':
                report_data['whisper_id'] = content_id
            
            # Check if system user exists, if not create it
            system_user = await self.db.userprofile.find_unique(
                where={'clerk_user_id': self.SYSTEM_USER_ID}
            )
            
            if not system_user:
                # Create system user for automated reports
                system_user = await self.db.userprofile.create(
                    data={
                        'clerk_user_id': self.SYSTEM_USER_ID,
                        'handle': 'system',
                        'display_name': 'Automated System',
                        'email': 'system@muejam.internal'
                    }
                )
                report_data['reporter_id'] = system_user.id
            else:
                report_data['reporter_id'] = system_user.id
            
            # Create report
            report = await self.db.report.create(data=report_data)
            
            logger.info(
                f"Created automated report {report.id} for {content_type} {content_id}"
            )
            
        except Exception as e:
            logger.error(
                f"Failed to create automated report for {content_type} {content_id}: {e}"
            )
    
    async def _log_automated_flags(
        self,
        content_type: str,
        content_id: str,
        filter_result: dict
    ) -> None:
        """
        Log automated flags to the database.
        
        Args:
            content_type: Type of content
            content_id: ID of the content
            filter_result: Filter results with flags and details
            
        Requirements:
            - 4.5: Log automated filtering actions
        """
        if not self.config_service:
            return
        
        try:
            for flag_type in filter_result['flags']:
                confidence = filter_result.get('details', {}).get(
                    flag_type, {}
                ).get('confidence', 0.0)
                
                await self.config_service.log_automated_flag(
                    content_type=content_type,
                    content_id=content_id,
                    flag_type=flag_type,
                    confidence=confidence
                )
        except Exception as e:
            logger.error(f"Failed to log automated flags: {e}")
    
    def _generate_error_message(self, flags: list) -> str:
        """
        Generate user-friendly error message based on detected flags.
        
        Args:
            flags: List of detected issues
            
        Returns:
            User-friendly error message
            
        Requirements:
            - 4.3: Return appropriate errors for blocked content
            - 4.7: Block content with malicious URLs
        """
        if 'spam' in flags:
            return (
                "Your content was blocked due to spam detection. "
                "Please remove excessive links, repeated text, or promotional content."
            )
        elif 'profanity' in flags:
            return (
                "Your content contains inappropriate language. "
                "Please revise your content and try again."
            )
        elif 'malicious_url' in flags:
            return (
                "Your content contains a suspicious or malicious URL. "
                "Please remove the link and try again."
            )
        else:
            return (
                "Your content was blocked by our automated filters. "
                "Please review our content policy and try again."
            )
    
    async def _log_blocked_url_attempt(
        self,
        content_type: str,
        content_id: str,
        filter_details: dict,
        user_id: Optional[str] = None
    ) -> None:
        """
        Log a blocked content submission attempt due to malicious URLs.
        
        Args:
            content_type: Type of content
            content_id: ID of the content
            filter_details: Detailed filter results
            user_id: Optional user ID
            
        Requirements:
            - 4.7: Log blocked attempts
        """
        try:
            malicious_url_details = filter_details.get('malicious_url', {})
            malicious_urls = malicious_url_details.get('malicious_urls', [])
            
            logger.warning(
                f"Blocked {content_type} submission due to malicious URLs. "
                f"Content ID: {content_id}, User ID: {user_id}, "
                f"Malicious URLs: {', '.join(malicious_urls)}, "
                f"Threat details: {malicious_url_details.get('threat_details', {})}"
            )
            
            # Optionally store in database for audit trail
            if self.config_service:
                await self.config_service.log_automated_flag(
                    content_type=content_type,
                    content_id=content_id,
                    flag_type='malicious_url',
                    confidence=1.0,
                    metadata={
                        'malicious_urls': malicious_urls,
                        'threat_details': malicious_url_details.get('threat_details', {})
                    }
                )
        except Exception as e:
            logger.error(f"Failed to log blocked URL attempt: {e}")
