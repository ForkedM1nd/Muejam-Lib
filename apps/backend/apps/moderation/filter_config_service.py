"""
Service for managing content filter configurations.

This module provides functionality to load and manage filter configurations
from the database, implementing requirement 4.8.
"""

from typing import Dict, Optional, Set
from prisma import Prisma
from prisma.enums import FilterType, FilterSensitivity
from .content_filters import ContentFilterPipeline


class FilterConfigService:
    """
    Service for loading and managing content filter configurations.
    
    Implements requirement 4.8: Allow administrators to configure filter
    sensitivity levels (strict, moderate, permissive).
    """
    
    def __init__(self, db: Optional[Prisma] = None):
        """
        Initialize the filter config service.
        
        Args:
            db: Prisma database client instance
        """
        self.db = db or Prisma()
    
    async def get_filter_config(self, filter_type: FilterType) -> Optional[Dict]:
        """
        Get configuration for a specific filter type.
        
        Args:
            filter_type: Type of filter (PROFANITY, SPAM, HATE_SPEECH)
            
        Returns:
            Dictionary with filter configuration or None if not found
        """
        config = await self.db.contentfilterconfig.find_unique(
            where={'filter_type': filter_type}
        )
        
        if not config:
            return None
        
        return {
            'enabled': config.enabled,
            'sensitivity': config.sensitivity,
            'whitelist': set(config.whitelist) if config.whitelist else set(),
            'blacklist': set(config.blacklist) if config.blacklist else set()
        }
    
    async def create_or_update_config(
        self,
        filter_type: FilterType,
        sensitivity: FilterSensitivity,
        enabled: bool,
        whitelist: Optional[Set[str]] = None,
        blacklist: Optional[Set[str]] = None,
        updated_by: str = 'system'
    ) -> Dict:
        """
        Create or update a filter configuration.
        
        Args:
            filter_type: Type of filter
            sensitivity: Sensitivity level (STRICT, MODERATE, PERMISSIVE)
            enabled: Whether the filter is enabled
            whitelist: Set of terms to ignore
            blacklist: Set of additional terms to flag
            updated_by: User ID who updated the config
            
        Returns:
            Updated configuration dictionary
        """
        whitelist_list = list(whitelist) if whitelist else []
        blacklist_list = list(blacklist) if blacklist else []
        
        config = await self.db.contentfilterconfig.upsert(
            where={'filter_type': filter_type},
            data={
                'create': {
                    'filter_type': filter_type,
                    'sensitivity': sensitivity,
                    'enabled': enabled,
                    'whitelist': whitelist_list,
                    'blacklist': blacklist_list,
                    'updated_by': updated_by
                },
                'update': {
                    'sensitivity': sensitivity,
                    'enabled': enabled,
                    'whitelist': whitelist_list,
                    'blacklist': blacklist_list,
                    'updated_by': updated_by
                }
            }
        )
        
        return {
            'id': config.id,
            'filter_type': config.filter_type,
            'sensitivity': config.sensitivity,
            'enabled': config.enabled,
            'whitelist': config.whitelist,
            'blacklist': config.blacklist,
            'updated_at': config.updated_at
        }
    
    async def get_pipeline(self) -> ContentFilterPipeline:
        """
        Create a ContentFilterPipeline with current database configurations.
        
        Returns:
            Configured ContentFilterPipeline instance
        """
        # Load configurations for all filter types
        profanity_config = await self.get_filter_config(FilterType.PROFANITY)
        spam_config = await self.get_filter_config(FilterType.SPAM)
        hate_speech_config = await self.get_filter_config(FilterType.HATE_SPEECH)
        
        # Build configuration dictionaries
        profanity_kwargs = {}
        if profanity_config and profanity_config['enabled']:
            profanity_kwargs = {
                'sensitivity': profanity_config['sensitivity'],
                'whitelist': profanity_config['whitelist'],
                'custom_words': profanity_config['blacklist']
            }
        
        spam_kwargs = {}
        if spam_config and spam_config['enabled']:
            spam_kwargs = {
                'sensitivity': spam_config['sensitivity']
            }
        
        hate_speech_kwargs = {}
        if hate_speech_config and hate_speech_config['enabled']:
            hate_speech_kwargs = {
                'sensitivity': hate_speech_config['sensitivity'],
                'custom_keywords': hate_speech_config['blacklist']
            }
        
        return ContentFilterPipeline(
            profanity_config=profanity_kwargs,
            spam_config=spam_kwargs,
            hate_speech_config=hate_speech_kwargs
        )
    
    async def initialize_default_configs(self):
        """
        Initialize default filter configurations if they don't exist.
        
        This should be called during application startup to ensure
        default configurations are available.
        """
        default_configs = [
            {
                'filter_type': FilterType.PROFANITY,
                'sensitivity': FilterSensitivity.MODERATE,
                'enabled': True
            },
            {
                'filter_type': FilterType.SPAM,
                'sensitivity': FilterSensitivity.MODERATE,
                'enabled': True
            },
            {
                'filter_type': FilterType.HATE_SPEECH,
                'sensitivity': FilterSensitivity.MODERATE,
                'enabled': True
            }
        ]
        
        for config in default_configs:
            existing = await self.db.contentfilterconfig.find_unique(
                where={'filter_type': config['filter_type']}
            )
            
            if not existing:
                await self.db.contentfilterconfig.create(
                    data={
                        'filter_type': config['filter_type'],
                        'sensitivity': config['sensitivity'],
                        'enabled': config['enabled'],
                        'whitelist': [],
                        'blacklist': [],
                        'updated_by': 'system'
                    }
                )
    
    async def log_automated_flag(
        self,
        content_type: str,
        content_id: str,
        flag_type: str,
        confidence: float
    ) -> Dict:
        """
        Log an automated content flag for review.
        
        Args:
            content_type: Type of content (story, chapter, whisper, etc.)
            content_id: ID of the flagged content
            flag_type: Type of flag (profanity, spam, hate_speech)
            confidence: Confidence score of the detection
            
        Returns:
            Created AutomatedFlag record
        """
        flag = await self.db.automatedflag.create(
            data={
                'content_type': content_type,
                'content_id': content_id,
                'flag_type': flag_type,
                'confidence': confidence,
                'reviewed': False
            }
        )
        
        return {
            'id': flag.id,
            'content_type': flag.content_type,
            'content_id': flag.content_id,
            'flag_type': flag.flag_type,
            'confidence': flag.confidence,
            'created_at': flag.created_at
        }
