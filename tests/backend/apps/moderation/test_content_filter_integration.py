"""
Tests for content filter integration with content submission endpoints.

This module tests the integration of content filters with whispers, stories,
and chapters, implementing requirements 4.1-4.5.
"""

import pytest
import asyncio
from prisma import Prisma
from apps.moderation.content_filter_integration import ContentFilterIntegration


class TestContentFilterIntegration:
    """Test suite for content filter integration service."""
    
    @pytest.mark.asyncio
    async def test_filter_and_validate_clean_content(self):
        """
        Test that clean content passes validation.
        
        Requirements:
            - 4.1: Filter profanity
            - 4.2: Detect spam
        """
        db = Prisma()
        await db.connect()
        
        try:
            integration = ContentFilterIntegration(db)
            
            # Test clean content
            result = await integration.filter_and_validate_content(
                content="This is a perfectly normal whisper about cats.",
                content_type="whisper"
            )
            
            assert result['allowed'] is True
            assert result['blocked'] is False
            assert result['error_message'] is None
            assert len(result['flags']) == 0
            
        finally:
            await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_filter_blocks_spam_content(self):
        """
        Test that spam content is blocked.
        
        Requirements:
            - 4.2: Block spam patterns
            - 4.3: Return appropriate errors
        """
        db = Prisma()
        await db.connect()
        
        try:
            integration = ContentFilterIntegration(db)
            
            # Test spam content with excessive links
            spam_content = (
                "Buy now! Click here! "
                "http://spam1.com http://spam2.com http://spam3.com "
                "Limited time offer!"
            )
            
            result = await integration.filter_and_validate_content(
                content=spam_content,
                content_type="whisper"
            )
            
            assert result['allowed'] is False
            assert result['blocked'] is True
            assert result['error_message'] is not None
            assert 'spam' in result['flags']
            assert 'spam' in result['error_message'].lower()
            
        finally:
            await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_filter_blocks_high_profanity(self):
        """
        Test that high-severity profanity is blocked.
        
        Requirements:
            - 4.1: Filter profanity
            - 4.3: Return appropriate errors
        """
        db = Prisma()
        await db.connect()
        
        try:
            integration = ContentFilterIntegration(db)
            
            # Test content with high-severity profanity
            profane_content = "This is some fuck shit content"
            
            result = await integration.filter_and_validate_content(
                content=profane_content,
                content_type="whisper"
            )
            
            # Should be blocked with default MODERATE sensitivity
            assert result['blocked'] is True
            assert 'profanity' in result['flags']
            assert result['error_message'] is not None
            
        finally:
            await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_hate_speech_triggers_auto_report(self):
        """
        Test that hate speech detection triggers automated report creation.
        
        Requirements:
            - 4.4: Create high-priority reports for hate speech
        """
        db = Prisma()
        await db.connect()
        
        try:
            integration = ContentFilterIntegration(db)
            
            # Test content with hate speech patterns
            hate_content = "All [group] are subhuman and should die"
            
            result = await integration.filter_and_validate_content(
                content=hate_content,
                content_type="whisper"
            )
            
            # Hate speech should trigger auto-action
            assert 'hate_speech' in result['flags']
            assert 'create_high_priority_report' in result['auto_actions']
            
        finally:
            await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_error_message_generation(self):
        """
        Test that appropriate error messages are generated for different flags.
        
        Requirements:
            - 4.3: Return appropriate errors for blocked content
        """
        integration = ContentFilterIntegration()
        
        # Test spam error message
        spam_message = integration._generate_error_message(['spam'])
        assert 'spam' in spam_message.lower()
        assert 'links' in spam_message.lower() or 'promotional' in spam_message.lower()
        
        # Test profanity error message
        profanity_message = integration._generate_error_message(['profanity'])
        assert 'inappropriate' in profanity_message.lower() or 'language' in profanity_message.lower()
        
        # Test malicious URL error message
        url_message = integration._generate_error_message(['malicious_url'])
        assert 'url' in url_message.lower() or 'link' in url_message.lower()
    
    @pytest.mark.asyncio
    async def test_multiple_content_types(self):
        """
        Test that filters work for different content types.
        
        Requirements:
            - 4.1: Filter profanity across content types
            - 4.2: Detect spam across content types
        """
        db = Prisma()
        await db.connect()
        
        try:
            integration = ContentFilterIntegration(db)
            
            spam_content = "Buy now! http://spam1.com http://spam2.com http://spam3.com"
            
            # Test whisper
            whisper_result = await integration.filter_and_validate_content(
                content=spam_content,
                content_type="whisper"
            )
            assert whisper_result['blocked'] is True
            
            # Test story
            story_result = await integration.filter_and_validate_content(
                content=spam_content,
                content_type="story"
            )
            assert story_result['blocked'] is True
            
            # Test chapter
            chapter_result = await integration.filter_and_validate_content(
                content=spam_content,
                content_type="chapter"
            )
            assert chapter_result['blocked'] is True
            
        finally:
            await db.disconnect()


def run_tests():
    """Run all tests."""
    pytest.main([__file__, '-v'])


if __name__ == '__main__':
    run_tests()
