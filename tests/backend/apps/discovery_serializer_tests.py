"""Tests for discovery serializers."""
import pytest
import sys
from pathlib import Path
import os
import django

# Add apps/backend to path
backend_path = Path(__file__).parent.parent.parent.parent / 'apps' / 'backend'
sys.path.insert(0, str(backend_path))

# Configure Django settings before importing serializers
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('SKIP_CONFIG_VALIDATION', 'True')  # Skip validation for tests
django.setup()

from apps.discovery.serializers import (
    DiscoverFeedQuerySerializer,
    GenreQuerySerializer,
    SimilarStoriesQuerySerializer
)


class TestDiscoverFeedQuerySerializer:
    """Tests for DiscoverFeedQuerySerializer."""
    
    def test_valid_trending_tab(self):
        """Test valid trending tab."""
        data = {'tab': 'trending'}
        serializer = DiscoverFeedQuerySerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['tab'] == 'trending'
    
    def test_valid_new_tab(self):
        """Test valid new tab."""
        data = {'tab': 'new'}
        serializer = DiscoverFeedQuerySerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['tab'] == 'new'
    
    def test_valid_for_you_tab(self):
        """Test valid for-you tab."""
        data = {'tab': 'for-you'}
        serializer = DiscoverFeedQuerySerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['tab'] == 'for-you'
    
    def test_default_tab(self):
        """Test default tab is trending."""
        data = {}
        serializer = DiscoverFeedQuerySerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['tab'] == 'trending'
    
    def test_invalid_tab(self):
        """Test invalid tab value."""
        data = {'tab': 'invalid'}
        serializer = DiscoverFeedQuerySerializer(data=data)
        assert not serializer.is_valid()
        assert 'tab' in serializer.errors
    
    def test_with_tag_filter(self):
        """Test with tag filter."""
        data = {
            'tab': 'trending',
            'tag': 'fantasy'
        }
        serializer = DiscoverFeedQuerySerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['tag'] == 'fantasy'
    
    def test_with_search_query(self):
        """Test with search query."""
        data = {
            'tab': 'new',
            'q': 'dragon'
        }
        serializer = DiscoverFeedQuerySerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['q'] == 'dragon'
    
    def test_with_cursor(self):
        """Test with pagination cursor."""
        data = {
            'tab': 'trending',
            'cursor': 'abc123'
        }
        serializer = DiscoverFeedQuerySerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['cursor'] == 'abc123'
    
    def test_valid_page_size(self):
        """Test valid page size."""
        data = {
            'tab': 'trending',
            'page_size': 50
        }
        serializer = DiscoverFeedQuerySerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['page_size'] == 50
    
    def test_page_size_too_small(self):
        """Test page size below minimum."""
        data = {
            'tab': 'trending',
            'page_size': 0
        }
        serializer = DiscoverFeedQuerySerializer(data=data)
        assert not serializer.is_valid()
        assert 'page_size' in serializer.errors
    
    def test_page_size_too_large(self):
        """Test page size above maximum."""
        data = {
            'tab': 'trending',
            'page_size': 101
        }
        serializer = DiscoverFeedQuerySerializer(data=data)
        assert not serializer.is_valid()
        assert 'page_size' in serializer.errors
    
    def test_default_page_size(self):
        """Test default page size is 20."""
        data = {'tab': 'trending'}
        serializer = DiscoverFeedQuerySerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['page_size'] == 20


class TestGenreQuerySerializer:
    """Tests for GenreQuerySerializer."""
    
    def test_valid_with_cursor(self):
        """Test valid query with cursor."""
        data = {'cursor': 'xyz789'}
        serializer = GenreQuerySerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['cursor'] == 'xyz789'
    
    def test_valid_with_page_size(self):
        """Test valid query with page size."""
        data = {'page_size': 30}
        serializer = GenreQuerySerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['page_size'] == 30
    
    def test_empty_query(self):
        """Test empty query uses defaults."""
        data = {}
        serializer = GenreQuerySerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['page_size'] == 20


class TestSimilarStoriesQuerySerializer:
    """Tests for SimilarStoriesQuerySerializer."""
    
    def test_valid_limit(self):
        """Test valid limit."""
        data = {'limit': 20}
        serializer = SimilarStoriesQuerySerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['limit'] == 20
    
    def test_default_limit(self):
        """Test default limit is 10."""
        data = {}
        serializer = SimilarStoriesQuerySerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['limit'] == 10
    
    def test_limit_too_small(self):
        """Test limit below minimum."""
        data = {'limit': 0}
        serializer = SimilarStoriesQuerySerializer(data=data)
        assert not serializer.is_valid()
        assert 'limit' in serializer.errors
    
    def test_limit_too_large(self):
        """Test limit above maximum."""
        data = {'limit': 51}
        serializer = SimilarStoriesQuerySerializer(data=data)
        assert not serializer.is_valid()
        assert 'limit' in serializer.errors
