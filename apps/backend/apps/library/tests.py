"""Tests for library and shelf management."""
import pytest


class TestShelfOperations:
    """Test shelf CRUD operations."""
    
    def test_shelf_name_validation(self):
        """Test shelf name validation."""
        from apps.library.serializers import ShelfCreateSerializer
        
        # Valid name
        serializer = ShelfCreateSerializer(data={'name': 'My Reading List'})
        assert serializer.is_valid()
        
        # Empty name should fail
        serializer = ShelfCreateSerializer(data={'name': ''})
        assert not serializer.is_valid()
        assert 'name' in serializer.errors
        
        # Whitespace-only name should fail
        serializer = ShelfCreateSerializer(data={'name': '   '})
        assert not serializer.is_valid()
        assert 'name' in serializer.errors
    
    def test_shelf_update_validation(self):
        """Test shelf update validation."""
        from apps.library.serializers import ShelfUpdateSerializer
        
        # Valid name
        serializer = ShelfUpdateSerializer(data={'name': 'Updated Name'})
        assert serializer.is_valid()
        
        # Empty name should fail
        serializer = ShelfUpdateSerializer(data={'name': ''})
        assert not serializer.is_valid()


class TestShelfItemOperations:
    """Test shelf item operations."""
    
    def test_shelf_item_create_validation(self):
        """Test shelf item creation validation."""
        from apps.library.serializers import ShelfItemCreateSerializer
        
        # Valid story_id
        serializer = ShelfItemCreateSerializer(data={'story_id': 'story-123'})
        assert serializer.is_valid()
        
        # Missing story_id should fail
        serializer = ShelfItemCreateSerializer(data={})
        assert not serializer.is_valid()
        assert 'story_id' in serializer.errors


# Note: Full integration tests would require database setup and authentication
# These are basic unit tests to verify serializer validation
