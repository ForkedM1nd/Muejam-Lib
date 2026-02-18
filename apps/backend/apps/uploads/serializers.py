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
