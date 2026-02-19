"""
Test Mode Service for Mobile Backend Integration

This service provides test mode functionality for QA and development testing.
Includes mock data generation and test mode detection.

Requirements: 18.1, 18.2, 18.3, 18.4
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class TestModeService:
    """
    Service for test mode functionality.
    
    Provides mock data generation and test mode utilities for mobile testing.
    """
    
    @staticmethod
    def is_test_mode(request) -> bool:
        """
        Check if request is in test mode.
        
        Args:
            request: Django request object
            
        Returns:
            True if test mode is enabled
        """
        # Check for test mode header
        test_mode_header = request.headers.get('X-Test-Mode', '').lower()
        return test_mode_header in ['true', '1', 'yes']
    
    @staticmethod
    def generate_mock_stories(count: int = 5) -> List[Dict]:
        """
        Generate mock story data for testing.
        
        Args:
            count: Number of mock stories to generate
            
        Returns:
            List of mock story dictionaries
        """
        stories = []
        
        for i in range(count):
            story_id = f"test_story_{uuid4().hex[:8]}"
            stories.append({
                'id': story_id,
                'title': f'Test Story {i + 1}',
                'description': f'This is a test story for mobile testing purposes. Story number {i + 1}.',
                'author_id': f'test_user_{uuid4().hex[:8]}',
                'author_name': f'Test Author {i + 1}',
                'genre': ['Fantasy', 'Adventure', 'Mystery'][i % 3],
                'status': 'published',
                'chapter_count': (i + 1) * 3,
                'view_count': (i + 1) * 100,
                'like_count': (i + 1) * 25,
                'created_at': (datetime.now() - timedelta(days=i * 7)).isoformat(),
                'updated_at': (datetime.now() - timedelta(days=i)).isoformat(),
                'cover_image_url': f'https://example.com/covers/{story_id}.jpg',
                'deep_link': f'muejam://story/{story_id}'
            })
        
        return stories
    
    @staticmethod
    def generate_mock_chapters(story_id: str, count: int = 3) -> List[Dict]:
        """
        Generate mock chapter data for testing.
        
        Args:
            story_id: Story ID for the chapters
            count: Number of mock chapters to generate
            
        Returns:
            List of mock chapter dictionaries
        """
        chapters = []
        
        for i in range(count):
            chapter_id = f"test_chapter_{uuid4().hex[:8]}"
            chapters.append({
                'id': chapter_id,
                'story_id': story_id,
                'title': f'Chapter {i + 1}: Test Chapter',
                'content': f'This is test content for chapter {i + 1}. ' * 50,
                'chapter_number': i + 1,
                'word_count': 500 + (i * 100),
                'status': 'published',
                'created_at': (datetime.now() - timedelta(days=i * 3)).isoformat(),
                'updated_at': (datetime.now() - timedelta(days=i)).isoformat(),
                'deep_link': f'muejam://chapter/{chapter_id}'
            })
        
        return chapters
    
    @staticmethod
    def generate_mock_whispers(count: int = 5) -> List[Dict]:
        """
        Generate mock whisper data for testing.
        
        Args:
            count: Number of mock whispers to generate
            
        Returns:
            List of mock whisper dictionaries
        """
        whispers = []
        
        for i in range(count):
            whisper_id = f"test_whisper_{uuid4().hex[:8]}"
            whispers.append({
                'id': whisper_id,
                'content': f'Test whisper {i + 1}: This is a test whisper for mobile testing.',
                'author_id': f'test_user_{uuid4().hex[:8]}',
                'author_name': f'Test User {i + 1}',
                'like_count': (i + 1) * 5,
                'reply_count': i * 2,
                'created_at': (datetime.now() - timedelta(hours=i * 2)).isoformat(),
                'deep_link': f'muejam://whisper/{whisper_id}'
            })
        
        return whispers
    
    @staticmethod
    def generate_mock_users(count: int = 3) -> List[Dict]:
        """
        Generate mock user data for testing.
        
        Args:
            count: Number of mock users to generate
            
        Returns:
            List of mock user dictionaries
        """
        users = []
        
        for i in range(count):
            user_id = f"test_user_{uuid4().hex[:8]}"
            users.append({
                'id': user_id,
                'username': f'testuser{i + 1}',
                'display_name': f'Test User {i + 1}',
                'bio': f'This is a test user bio for testing purposes. User {i + 1}.',
                'avatar_url': f'https://example.com/avatars/{user_id}.jpg',
                'follower_count': (i + 1) * 50,
                'following_count': (i + 1) * 30,
                'story_count': (i + 1) * 5,
                'joined_at': (datetime.now() - timedelta(days=i * 30)).isoformat(),
                'deep_link': f'muejam://profile/{user_id}'
            })
        
        return users
    
    @staticmethod
    def generate_mock_data(data_type: str = 'all', count: Optional[int] = None) -> Dict:
        """
        Generate comprehensive mock data for testing.
        
        Args:
            data_type: Type of data to generate ('stories', 'chapters', 'whispers', 'users', 'all')
            count: Number of items to generate (uses defaults if None)
            
        Returns:
            Dictionary containing mock data
        """
        result = {}
        
        if data_type in ['stories', 'all']:
            story_count = count if count is not None else 5
            result['stories'] = TestModeService.generate_mock_stories(story_count)
        
        if data_type in ['chapters', 'all']:
            chapter_count = count if count is not None else 3
            # Generate chapters for a test story
            test_story_id = f"test_story_{uuid4().hex[:8]}"
            result['chapters'] = TestModeService.generate_mock_chapters(test_story_id, chapter_count)
        
        if data_type in ['whispers', 'all']:
            whisper_count = count if count is not None else 5
            result['whispers'] = TestModeService.generate_mock_whispers(whisper_count)
        
        if data_type in ['users', 'all']:
            user_count = count if count is not None else 3
            result['users'] = TestModeService.generate_mock_users(user_count)
        
        return result
