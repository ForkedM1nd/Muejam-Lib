"""Tests for text highlighting system."""
import pytest


class TestHighlightValidation:
    """Test highlight validation."""
    
    def test_valid_highlight_offsets(self):
        """Test valid highlight offsets."""
        from apps.highlights.serializers import HighlightCreateSerializer
        
        # Valid offsets
        serializer = HighlightCreateSerializer(data={
            'start_offset': 10,
            'end_offset': 50
        })
        assert serializer.is_valid()
    
    def test_start_offset_must_be_less_than_end_offset(self):
        """Test that start_offset must be less than end_offset."""
        from apps.highlights.serializers import HighlightCreateSerializer
        
        # start_offset >= end_offset should fail
        serializer = HighlightCreateSerializer(data={
            'start_offset': 50,
            'end_offset': 50
        })
        assert not serializer.is_valid()
        
        serializer = HighlightCreateSerializer(data={
            'start_offset': 60,
            'end_offset': 50
        })
        assert not serializer.is_valid()
    
    def test_negative_offsets_not_allowed(self):
        """Test that negative offsets are not allowed."""
        from apps.highlights.serializers import HighlightCreateSerializer
        
        # Negative start_offset
        serializer = HighlightCreateSerializer(data={
            'start_offset': -1,
            'end_offset': 50
        })
        assert not serializer.is_valid()
        assert 'start_offset' in serializer.errors
        
        # Negative end_offset
        serializer = HighlightCreateSerializer(data={
            'start_offset': 10,
            'end_offset': -1
        })
        assert not serializer.is_valid()
        assert 'end_offset' in serializer.errors
    
    def test_missing_offsets(self):
        """Test that both offsets are required."""
        from apps.highlights.serializers import HighlightCreateSerializer
        
        # Missing start_offset
        serializer = HighlightCreateSerializer(data={
            'end_offset': 50
        })
        assert not serializer.is_valid()
        assert 'start_offset' in serializer.errors
        
        # Missing end_offset
        serializer = HighlightCreateSerializer(data={
            'start_offset': 10
        })
        assert not serializer.is_valid()
        assert 'end_offset' in serializer.errors
        
        # Missing both
        serializer = HighlightCreateSerializer(data={})
        assert not serializer.is_valid()
        assert 'start_offset' in serializer.errors
        assert 'end_offset' in serializer.errors
    
    def test_zero_offsets_valid(self):
        """Test that zero offsets are valid (start of chapter)."""
        from apps.highlights.serializers import HighlightCreateSerializer
        
        # Zero start_offset is valid
        serializer = HighlightCreateSerializer(data={
            'start_offset': 0,
            'end_offset': 50
        })
        assert serializer.is_valid()
    
    def test_single_character_highlight(self):
        """Test that single character highlights are valid."""
        from apps.highlights.serializers import HighlightCreateSerializer
        
        # Highlight a single character (offset 10 to 11)
        serializer = HighlightCreateSerializer(data={
            'start_offset': 10,
            'end_offset': 11
        })
        assert serializer.is_valid()


# Note: Full integration tests would require database setup and authentication
# These are basic unit tests to verify serializer validation
