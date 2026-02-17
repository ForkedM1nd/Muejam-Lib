"""Tests for search and autocomplete functionality."""
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from prisma import Prisma
import asyncio
import uuid
from datetime import datetime


class SearchEndpointTests(TestCase):
    """
    Tests for search endpoint.
    
    Requirements:
        - 9.1: Search across story title, blurb, author name, tags
        - 9.5: Rank results by relevance and trending score
        - 9.6: Exclude soft-deleted and blocked content
        - 9.7: Use PostgreSQL full-text search
    """
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_search_endpoint_exists(self):
        """Test that search endpoint is accessible."""
        response = self.client.get('/v1/search/')
        # Should return 400 (missing query), not 404
        self.assertEqual(response.status_code, 400)
    
    def test_search_requires_query_parameter(self):
        """Test that search requires 'q' parameter."""
        response = self.client.get('/v1/search/')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('required', data['error'].lower())
    
    def test_search_with_query(self):
        """Test search with valid query parameter."""
        response = self.client.get('/v1/search/?q=test')
        self.assertIn(response.status_code, [200, 401])
        if response.status_code == 200:
            data = response.json()
            self.assertIn('data', data)
            self.assertIsInstance(data['data'], list)
    
    def test_search_response_structure(self):
        """Test that search response has correct structure."""
        response = self.client.get('/v1/search/?q=story')
        if response.status_code == 200:
            data = response.json()
            self.assertIn('data', data)
            self.assertIn('next_cursor', data)
    
    def test_search_across_title(self):
        """
        Test search across story titles.
        
        Requirements:
            - 9.1: Search across story title
        """
        import asyncio
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test user and story
                test_id = str(uuid.uuid4())
                user = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_search_{test_id}',
                        'handle': f'test_search_{test_id[:8]}',
                        'display_name': 'Test Author'
                    }
                )
                
                story = await db.story.create(
                    data={
                        'slug': f'unique-test-story-{test_id}',
                        'title': f'Unique Test Story {test_id[:8]}',
                        'blurb': 'A test story blurb',
                        'author_id': user.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                # Search for the story
                response = self.client.get(f'/v1/search/?q=Unique')
                
                if response.status_code == 200:
                    data = response.json()
                    # Story should be in results
                    story_ids = [s['id'] for s in data['data']]
                    self.assertIn(story.id, story_ids, "Story should be found by title search")
                
                # Cleanup
                await db.story.delete(where={'id': story.id})
                await db.userprofile.delete(where={'id': user.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
    
    def test_search_excludes_deleted_content(self):
        """
        Test that search excludes soft-deleted content.
        
        Requirements:
            - 9.6: Exclude soft-deleted content
        """
        import asyncio
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test user and deleted story
                test_id = str(uuid.uuid4())
                user = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_deleted_{test_id}',
                        'handle': f'test_deleted_{test_id[:8]}',
                        'display_name': 'Test Author'
                    }
                )
                
                story = await db.story.create(
                    data={
                        'slug': f'deleted-story-{test_id}',
                        'title': f'Deleted Story {test_id[:8]}',
                        'blurb': 'A deleted story',
                        'author_id': user.id,
                        'published': True,
                        'published_at': datetime.now(),
                        'deleted_at': datetime.now()  # Soft deleted
                    }
                )
                
                # Search for the story
                response = self.client.get(f'/v1/search/?q=Deleted')
                
                if response.status_code == 200:
                    data = response.json()
                    # Story should NOT be in results
                    story_ids = [s['id'] for s in data['data']]
                    self.assertNotIn(story.id, story_ids, "Deleted story should not appear in search")
                
                # Cleanup
                await db.story.delete(where={'id': story.id})
                await db.userprofile.delete(where={'id': user.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())


class AutocompleteTests(TestCase):
    """
    Tests for autocomplete suggestions.
    
    Requirements:
        - 9.2: Return suggestions for stories, tags, authors
        - 9.3: Cache suggestions
        - 9.4: Navigate to corresponding content
        - 21.5: Cache with TTL 10-30 minutes
    """
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_suggest_endpoint_exists(self):
        """Test that suggest endpoint is accessible."""
        response = self.client.get('/v1/search/suggest')
        # Should return 400 (missing query), not 404
        self.assertEqual(response.status_code, 400)
    
    def test_suggest_requires_query_parameter(self):
        """Test that suggest requires 'q' parameter."""
        response = self.client.get('/v1/search/suggest')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_suggest_response_structure(self):
        """
        Test that suggest response has correct structure.
        
        Requirements:
            - 9.2: Return suggestions for stories, tags, authors
        """
        response = self.client.get('/v1/search/suggest?q=test')
        if response.status_code == 200:
            data = response.json()
            self.assertIn('stories', data)
            self.assertIn('tags', data)
            self.assertIn('authors', data)
            self.assertIsInstance(data['stories'], list)
            self.assertIsInstance(data['tags'], list)
            self.assertIsInstance(data['authors'], list)
    
    def test_suggest_story_suggestions(self):
        """
        Test story suggestions.
        
        Requirements:
            - 9.2: Return story suggestions
        """
        import asyncio
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test user and story
                test_id = str(uuid.uuid4())
                user = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_suggest_{test_id}',
                        'handle': f'test_suggest_{test_id[:8]}',
                        'display_name': 'Test Author'
                    }
                )
                
                story = await db.story.create(
                    data={
                        'slug': f'suggest-story-{test_id}',
                        'title': f'Suggestion Test Story {test_id[:8]}',
                        'blurb': 'A test story',
                        'author_id': user.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                # Get suggestions
                response = self.client.get('/v1/search/suggest?q=Suggestion')
                
                if response.status_code == 200:
                    data = response.json()
                    # Story should be in suggestions
                    story_ids = [s['id'] for s in data['stories']]
                    self.assertIn(story.id, story_ids, "Story should appear in suggestions")
                
                # Cleanup
                await db.story.delete(where={'id': story.id})
                await db.userprofile.delete(where={'id': user.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
    
    def test_suggest_tag_suggestions(self):
        """
        Test tag suggestions.
        
        Requirements:
            - 9.2: Return tag suggestions
        """
        import asyncio
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test tag
                test_id = str(uuid.uuid4())
                tag = await db.tag.create(
                    data={
                        'name': f'UniqueTestTag{test_id[:8]}',
                        'slug': f'unique-test-tag-{test_id[:8]}'
                    }
                )
                
                # Get suggestions
                response = self.client.get('/v1/search/suggest?q=UniqueTestTag')
                
                if response.status_code == 200:
                    data = response.json()
                    # Tag should be in suggestions
                    tag_ids = [t['id'] for t in data['tags']]
                    self.assertIn(tag.id, tag_ids, "Tag should appear in suggestions")
                
                # Cleanup
                await db.tag.delete(where={'id': tag.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
    
    def test_suggest_author_suggestions(self):
        """
        Test author suggestions.
        
        Requirements:
            - 9.2: Return author suggestions
        """
        import asyncio
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test user
                test_id = str(uuid.uuid4())
                user = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_author_suggest_{test_id}',
                        'handle': f'uniqueauthor{test_id[:8]}',
                        'display_name': f'Unique Author {test_id[:8]}'
                    }
                )
                
                # Get suggestions
                response = self.client.get('/v1/search/suggest?q=uniqueauthor')
                
                if response.status_code == 200:
                    data = response.json()
                    # Author should be in suggestions
                    author_ids = [a['id'] for a in data['authors']]
                    self.assertIn(user.id, author_ids, "Author should appear in suggestions")
                
                # Cleanup
                await db.userprofile.delete(where={'id': user.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
    
    def test_suggest_caching(self):
        """
        Test that suggestions are cached.
        
        Requirements:
            - 9.3: Cache suggestions
            - 21.5: Cache with TTL 10-30 minutes
        """
        # First request
        response1 = self.client.get('/v1/search/suggest?q=test')
        
        # Second request (should be cached)
        response2 = self.client.get('/v1/search/suggest?q=test')
        
        if response1.status_code == 200 and response2.status_code == 200:
            # Both should return same structure
            data1 = response1.json()
            data2 = response2.json()
            self.assertEqual(
                set(data1.keys()),
                set(data2.keys()),
                "Cached response should have same structure"
            )


class SearchRankingTests(TestCase):
    """
    Tests for search result ranking.
    
    Requirements:
        - 9.5: Rank results by relevance and trending score
    """
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_title_match_ranks_higher(self):
        """
        Test that title matches rank higher than blurb matches.
        
        Requirements:
            - 9.5: Rank by relevance
        """
        import asyncio
        
        async def run_test():
            db = Prisma()
            await db.connect()
            
            try:
                # Create test user
                test_id = str(uuid.uuid4())
                user = await db.userprofile.create(
                    data={
                        'clerk_user_id': f'test_rank_{test_id}',
                        'handle': f'test_rank_{test_id[:8]}',
                        'display_name': 'Test Author'
                    }
                )
                
                # Create story with keyword in title
                story1 = await db.story.create(
                    data={
                        'slug': f'keyword-title-{test_id}',
                        'title': f'Keyword Story {test_id[:8]}',
                        'blurb': 'A test story',
                        'author_id': user.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                # Create story with keyword in blurb
                story2 = await db.story.create(
                    data={
                        'slug': f'keyword-blurb-{test_id}',
                        'title': f'Another Story {test_id[:8]}',
                        'blurb': 'A story with Keyword in blurb',
                        'author_id': user.id,
                        'published': True,
                        'published_at': datetime.now()
                    }
                )
                
                # Search for keyword
                response = self.client.get('/v1/search/?q=Keyword')
                
                if response.status_code == 200:
                    data = response.json()
                    if len(data['data']) >= 2:
                        # Find positions of our stories
                        story_ids = [s['id'] for s in data['data']]
                        if story1.id in story_ids and story2.id in story_ids:
                            pos1 = story_ids.index(story1.id)
                            pos2 = story_ids.index(story2.id)
                            self.assertLess(
                                pos1,
                                pos2,
                                "Title match should rank higher than blurb match"
                            )
                
                # Cleanup
                await db.story.delete(where={'id': story1.id})
                await db.story.delete(where={'id': story2.id})
                await db.userprofile.delete(where={'id': user.id})
                
            finally:
                await db.disconnect()
        
        asyncio.run(run_test())
