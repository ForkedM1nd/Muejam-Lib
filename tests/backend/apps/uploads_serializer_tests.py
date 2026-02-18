"""Tests for uploads serializers."""
import pytest
import sys
from pathlib import Path

# Add apps/backend to path
backend_path = Path(__file__).parent.parent.parent.parent / 'apps' / 'backend'
sys.path.insert(0, str(backend_path))

from apps.uploads.serializers import PresignUploadRequestSerializer


class TestPresignUploadRequestSerializer:
    """Tests for PresignUploadRequestSerializer."""
    
    def test_valid_avatar_upload(self):
        """Test valid avatar upload request."""
        data = {
            'type': 'avatar',
            'content_type': 'image/jpeg'
        }
        serializer = PresignUploadRequestSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['type'] == 'avatar'
        assert serializer.validated_data['content_type'] == 'image/jpeg'
    
    def test_valid_cover_upload(self):
        """Test valid cover upload request."""
        data = {
            'type': 'cover',
            'content_type': 'image/png'
        }
        serializer = PresignUploadRequestSerializer(data=data)
        assert serializer.is_valid()
    
    def test_valid_whisper_media_upload(self):
        """Test valid whisper media upload request."""
        data = {
            'type': 'whisper_media',
            'content_type': 'image/webp'
        }
        serializer = PresignUploadRequestSerializer(data=data)
        assert serializer.is_valid()
    
    def test_missing_type(self):
        """Test missing upload type."""
        data = {
            'content_type': 'image/jpeg'
        }
        serializer = PresignUploadRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'type' in serializer.errors
    
    def test_missing_content_type(self):
        """Test missing content type."""
        data = {
            'type': 'avatar'
        }
        serializer = PresignUploadRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'content_type' in serializer.errors
    
    def test_invalid_upload_type(self):
        """Test invalid upload type."""
        data = {
            'type': 'invalid_type',
            'content_type': 'image/jpeg'
        }
        serializer = PresignUploadRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'type' in serializer.errors
    
    def test_invalid_content_type(self):
        """Test invalid content type."""
        data = {
            'type': 'avatar',
            'content_type': 'application/pdf'
        }
        serializer = PresignUploadRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'content_type' in serializer.errors
    
    def test_all_valid_content_types(self):
        """Test all valid content types."""
        valid_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        for content_type in valid_types:
            data = {
                'type': 'avatar',
                'content_type': content_type
            }
            serializer = PresignUploadRequestSerializer(data=data)
            assert serializer.is_valid(), f"Failed for {content_type}"
