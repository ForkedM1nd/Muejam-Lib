"""Views for media upload system."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .s3 import S3UploadManager
from .serializers import PresignUploadRequestSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def presign_upload(request):
    """
    Generate presigned URL for file upload.
    
    Request Body:
        - type: Upload type ('avatar', 'cover', 'whisper_media')
        - content_type: MIME type ('image/jpeg', 'image/png', 'image/webp', 'image/gif')
        
    Returns:
        Presigned URL, fields, object key, and max size
        
    Requirements:
        - 14.1: Generate presigned S3 URL with 15-minute expiration
        - 14.2: Enforce 2MB max for avatar uploads
        - 14.3: Enforce 5MB max for story cover uploads
        - 14.4: Enforce 10MB max for whisper media uploads
        - 14.5: Validate file type (JPEG, PNG, WebP, GIF)
        - 14.7: Generate unique object keys using UUID
    """
    # Validate input with serializer
    serializer = PresignUploadRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                'error': 'Validation failed',
                'details': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    upload_type = validated_data['type']
    content_type = validated_data['content_type']
    
    # Generate presigned URL
    try:
        s3_manager = S3UploadManager()
        presigned_data = s3_manager.generate_presigned_url(
            upload_type,
            content_type
        )
        
        return Response(presigned_data, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to generate presigned URL'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
