"""
Property-Based Tests for Deep Link Service

Tests universal properties that should hold for all deep link generation.
Feature: mobile-backend-integration
"""

import pytest
from hypothesis import given, strategies as st, assume
from urllib.parse import urlparse, unquote
from apps.core.deep_link_service import DeepLinkService


# Strategies for generating test data
valid_platforms = st.sampled_from(['ios', 'android', None])
invalid_platforms = st.text().filter(lambda x: x not in ['ios', 'android', None])

# Generate valid IDs (non-empty strings)
valid_ids = st.text(min_size=1, max_size=100).filter(lambda x: x.strip() != '')

# Generate IDs with special characters that need URL encoding
special_char_ids = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Z'))
).filter(lambda x: x.strip() != '')


class TestDeepLinkProperties:
    """Property-based tests for DeepLinkService"""
    
    @given(story_id=valid_ids, platform=valid_platforms)
    def test_property_14_mobile_deep_link_inclusion_stories(self, story_id, platform):
        """
        **Validates: Requirements 6.1**
        
        Feature: mobile-backend-integration, Property 14: Mobile Deep Link Inclusion
        
        For any mobile client request to endpoints returning stories,
        the response SHALL include properly formatted deep links.
        """
        link = DeepLinkService.generate_story_link(story_id, platform)
        
        # Deep link must be a non-empty string
        assert isinstance(link, str)
        assert len(link) > 0
        
        # Deep link must start with the correct scheme
        assert link.startswith('muejam://')
        
        # Deep link must contain the story path
        assert 'story/' in link
    
    @given(chapter_id=valid_ids, platform=valid_platforms)
    def test_property_14_mobile_deep_link_inclusion_chapters(self, chapter_id, platform):
        """
        **Validates: Requirements 6.1**
        
        Feature: mobile-backend-integration, Property 14: Mobile Deep Link Inclusion
        
        For any mobile client request to endpoints returning chapters,
        the response SHALL include properly formatted deep links.
        """
        link = DeepLinkService.generate_chapter_link(chapter_id, platform)
        
        # Deep link must be a non-empty string
        assert isinstance(link, str)
        assert len(link) > 0
        
        # Deep link must start with the correct scheme
        assert link.startswith('muejam://')
        
        # Deep link must contain the chapter path
        assert 'chapter/' in link
    
    @given(whisper_id=valid_ids, platform=valid_platforms)
    def test_property_14_mobile_deep_link_inclusion_whispers(self, whisper_id, platform):
        """
        **Validates: Requirements 6.1**
        
        Feature: mobile-backend-integration, Property 14: Mobile Deep Link Inclusion
        
        For any mobile client request to endpoints returning whispers,
        the response SHALL include properly formatted deep links.
        """
        link = DeepLinkService.generate_whisper_link(whisper_id, platform)
        
        # Deep link must be a non-empty string
        assert isinstance(link, str)
        assert len(link) > 0
        
        # Deep link must start with the correct scheme
        assert link.startswith('muejam://')
        
        # Deep link must contain the whisper path
        assert 'whisper/' in link
    
    @given(user_id=valid_ids, platform=valid_platforms)
    def test_property_14_mobile_deep_link_inclusion_profiles(self, user_id, platform):
        """
        **Validates: Requirements 6.1**
        
        Feature: mobile-backend-integration, Property 14: Mobile Deep Link Inclusion
        
        For any mobile client request to endpoints returning user profiles,
        the response SHALL include properly formatted deep links.
        """
        link = DeepLinkService.generate_profile_link(user_id, platform)
        
        # Deep link must be a non-empty string
        assert isinstance(link, str)
        assert len(link) > 0
        
        # Deep link must start with the correct scheme
        assert link.startswith('muejam://')
        
        # Deep link must contain the profile path
        assert 'profile/' in link
    
    @given(resource_id=special_char_ids, platform=valid_platforms)
    def test_property_15_deep_link_format_validation(self, resource_id, platform):
        """
        **Validates: Requirements 6.2, 6.4**
        
        Feature: mobile-backend-integration, Property 15: Deep Link Format Validation
        
        For any generated deep link, the URL SHALL follow the platform-specific
        scheme (muejam://) and be properly URL-encoded with no invalid characters.
        """
        # Test with all resource types
        links = [
            DeepLinkService.generate_story_link(resource_id, platform),
            DeepLinkService.generate_chapter_link(resource_id, platform),
            DeepLinkService.generate_whisper_link(resource_id, platform),
            DeepLinkService.generate_profile_link(resource_id, platform),
        ]
        
        for link in links:
            # Must follow platform-specific scheme
            assert link.startswith('muejam://'), f"Link does not start with correct scheme: {link}"
            
            # Must be parseable as a URL
            parsed = urlparse(link)
            assert parsed.scheme == 'muejam'
            
            # Path must not be empty
            assert parsed.path, f"Link has empty path: {link}"
            
            # No invalid characters (spaces, unencoded special chars)
            # The path after the resource type should be URL-encoded
            assert ' ' not in link, f"Link contains unencoded space: {link}"
            
            # Should not have triple slashes (muejam:///...)
            assert '///' not in link, f"Link has triple slashes: {link}"
    
    @given(story_id=valid_ids)
    def test_property_15_url_encoding_consistency(self, story_id):
        """
        **Validates: Requirements 6.4**
        
        Test that URL encoding is applied consistently across platforms.
        """
        ios_link = DeepLinkService.generate_story_link(story_id, 'ios')
        android_link = DeepLinkService.generate_story_link(story_id, 'android')
        
        # Both platforms should produce identical links (same scheme)
        assert ios_link == android_link
    
    @given(resource_id=valid_ids, platform=valid_platforms)
    def test_deep_link_idempotency(self, resource_id, platform):
        """
        Test that generating the same deep link multiple times produces identical results.
        """
        link1 = DeepLinkService.generate_story_link(resource_id, platform)
        link2 = DeepLinkService.generate_story_link(resource_id, platform)
        
        assert link1 == link2, "Deep link generation should be idempotent"
    
    @given(resource_id=valid_ids, platform=valid_platforms)
    def test_deep_link_uniqueness(self, resource_id, platform):
        """
        Test that different resource types produce different deep links for the same ID.
        """
        story_link = DeepLinkService.generate_story_link(resource_id, platform)
        chapter_link = DeepLinkService.generate_chapter_link(resource_id, platform)
        whisper_link = DeepLinkService.generate_whisper_link(resource_id, platform)
        profile_link = DeepLinkService.generate_profile_link(resource_id, platform)
        
        # All links should be different
        links = [story_link, chapter_link, whisper_link, profile_link]
        assert len(set(links)) == 4, "Different resource types should produce unique links"
    
    @given(platform=invalid_platforms)
    def test_invalid_platform_rejection(self, platform):
        """
        Test that invalid platforms are rejected with appropriate error.
        """
        assume(platform not in [None, 'ios', 'android'])
        
        with pytest.raises(ValueError, match="Invalid platform"):
            DeepLinkService.generate_story_link('test_id', platform)
    
    @given(platform=valid_platforms)
    def test_empty_id_rejection(self, platform):
        """
        Test that empty IDs are rejected for all resource types.
        """
        with pytest.raises(ValueError):
            DeepLinkService.generate_story_link('', platform)
        
        with pytest.raises(ValueError):
            DeepLinkService.generate_chapter_link('', platform)
        
        with pytest.raises(ValueError):
            DeepLinkService.generate_whisper_link('', platform)
        
        with pytest.raises(ValueError):
            DeepLinkService.generate_profile_link('', platform)
