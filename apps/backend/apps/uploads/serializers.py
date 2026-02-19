"""Serializers for upload endpoints."""
from rest_framework import serializers


class PresignUploadRequestSerializer(serializers.Serializer):
    """
    Serializer for presigned upload request.
    
    Validates upload type and content type for S3 presigned URL generation.
    """
    
    VALID_UPLOAD_TYPES = ['avatar', 'cover', 'whisper_media']
    VALID_CONTENT_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    
    type = serializers.ChoiceField(
        choices=VALID_UPLOAD_TYPES,
        required=True,
        error_messages={
            'required': 'Upload type is required',
            'invalid_choice': f'Upload type must be one of: {", ".join(VALID_UPLOAD_TYPES)}'
        }
    )
    
    content_type = serializers.ChoiceField(
        choices=VALID_CONTENT_TYPES,
        required=True,
        error_messages={
            'required': 'Content type is required',
            'invalid_choice': f'Content type must be one of: {", ".join(VALID_CONTENT_TYPES)}'
        }
    )


class PresignUploadResponseSerializer(serializers.Serializer):
    """Serializer for presigned upload response."""
    
    url = serializers.URLField()
    fields = serializers.DictField()
    object_key = serializers.CharField()
    max_size = serializers.IntegerField()


class MobileMediaUploadSerializer(serializers.Serializer):
    """Serializer for mobile media upload request."""
    
    file = serializers.FileField(required=True)
    filename = serializers.CharField(required=True, max_length=255)
    content_type = serializers.CharField(required=True, max_length=100)


class ChunkedUploadInitSerializer(serializers.Serializer):
    """Serializer for chunked upload initialization request."""
    
    filename = serializers.CharField(required=True, max_length=255)
    total_size = serializers.IntegerField(required=True, min_value=1)


class ChunkedUploadChunkSerializer(serializers.Serializer):
    """Serializer for chunked upload chunk request."""
    
    session_id = serializers.CharField(required=True)
    chunk_number = serializers.IntegerField(required=True, min_value=0)
    chunk_data = serializers.FileField(required=True)


class ChunkedUploadCompleteSerializer(serializers.Serializer):
    """Serializer for chunked upload completion request."""
    
    session_id = serializers.CharField(required=True)
