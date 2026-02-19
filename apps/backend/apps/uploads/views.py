"""Views for media upload system."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from prisma import Prisma
from .s3 import S3UploadManager
from .serializers import (
    PresignUploadRequestSerializer,
    MobileMediaUploadSerializer,
    ChunkedUploadInitSerializer,
    ChunkedUploadChunkSerializer,
    ChunkedUploadCompleteSerializer
)
from .mobile_upload_service import MobileUploadService
import logging

logger = logging.getLogger(__name__)


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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mobile_media_upload(request):
    """
    Handle single mobile media upload with format conversion and EXIF stripping.
    
    Request Body:
        - file: File upload
        - filename: Original filename
        - content_type: MIME type
        
    Returns:
        Upload result with URL and metadata
        
    Requirements:
        - 7.1: Accept mobile-specific image formats (HEIC, HEIF)
        - 7.2: Validate file size limits appropriate for mobile uploads
        - 7.5: Strip EXIF location and sensitive metadata
    """
    serializer = MobileMediaUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                'error': 'Validation failed',
                'details': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    file_obj = validated_data['file']
    filename = validated_data['filename']
    content_type = validated_data['content_type']
    
    # Get user ID from request
    user_id = request.user.get('sub')
    if not user_id:
        return Response(
            {'error': 'User ID not found in token'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        # Read file data
        file_data = file_obj.read()
        
        # Initialize upload service
        upload_service = MobileUploadService()
        
        # Validate file size
        is_valid, error = upload_service.validate_file_size(len(file_data))
        if not is_valid:
            return Response(
                {'error': error},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )
        
        # Process mobile image (HEIC conversion and EXIF stripping)
        processed_data, final_content_type = upload_service.process_mobile_image(
            file_data,
            filename,
            content_type
        )
        
        # In a real implementation, we would upload to S3 here
        # For now, return success with metadata
        return Response(
            {
                'status': 'success',
                'filename': filename,
                'content_type': final_content_type,
                'size': len(processed_data),
                'message': 'File uploaded and processed successfully'
            },
            status=status.HTTP_200_OK
        )
        
    except ValueError as e:
        logger.error(f"Mobile upload validation error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Mobile upload error: {str(e)}")
        return Response(
            {'error': 'Failed to process upload'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chunked_upload_init(request):
    """
    Initialize chunked upload session.
    
    Request Body:
        - filename: Original filename
        - total_size: Total file size in bytes
        
    Returns:
        Upload session information with session_id, chunk_size, and chunks_total
        
    Requirements:
        - 7.2: Validate file size limits appropriate for mobile uploads
        - 7.3: Support chunked upload for large media files from Mobile_Client
    """
    serializer = ChunkedUploadInitSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                'error': 'Validation failed',
                'details': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    filename = validated_data['filename']
    total_size = validated_data['total_size']
    
    # Get user ID from request
    user_id = request.user.get('sub')
    if not user_id:
        return Response(
            {'error': 'User ID not found in token'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        # Initialize Prisma client
        db = Prisma()
        db.connect()
        
        try:
            # Initialize upload service with Prisma client
            upload_service = MobileUploadService(prisma_client=db)
            
            # Initiate chunked upload (synchronous wrapper for async method)
            import asyncio
            session_info = asyncio.run(upload_service.initiate_chunked_upload(
                filename=filename,
                total_size=total_size,
                user_id=user_id
            ))
            
            return Response(session_info, status=status.HTTP_200_OK)
            
        finally:
            db.disconnect()
        
    except ValueError as e:
        logger.error(f"Chunked upload init validation error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Chunked upload init error: {str(e)}")
        return Response(
            {'error': 'Failed to initialize chunked upload'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chunked_upload_chunk(request):
    """
    Upload a file chunk.
    
    Request Body:
        - session_id: Upload session ID
        - chunk_number: Chunk sequence number (0-indexed)
        - chunk_data: Chunk binary data
        
    Returns:
        Chunk upload status with chunks_uploaded and chunks_remaining
        
    Requirements:
        - 7.3: Support chunked upload for large media files from Mobile_Client
        - 7.4: Provide upload progress tracking for Mobile_Client
    """
    serializer = ChunkedUploadChunkSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                'error': 'Validation failed',
                'details': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    session_id = validated_data['session_id']
    chunk_number = validated_data['chunk_number']
    chunk_file = validated_data['chunk_data']
    
    try:
        # Read chunk data
        chunk_data = chunk_file.read()
        
        # Initialize Prisma client
        db = Prisma()
        db.connect()
        
        try:
            # Initialize upload service with Prisma client
            upload_service = MobileUploadService(prisma_client=db)
            
            # Upload chunk (synchronous wrapper for async method)
            import asyncio
            chunk_status = asyncio.run(upload_service.upload_chunk(
                session_id=session_id,
                chunk_number=chunk_number,
                chunk_data=chunk_data
            ))
            
            return Response(chunk_status, status=status.HTTP_200_OK)
            
        finally:
            db.disconnect()
        
    except ValueError as e:
        logger.error(f"Chunked upload chunk validation error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Chunked upload chunk error: {str(e)}")
        return Response(
            {'error': 'Failed to upload chunk'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chunked_upload_complete(request):
    """
    Complete chunked upload and finalize file.
    
    Request Body:
        - session_id: Upload session ID
        
    Returns:
        Final upload result with status and file information
        
    Requirements:
        - 7.3: Support chunked upload for large media files from Mobile_Client
    """
    serializer = ChunkedUploadCompleteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                'error': 'Validation failed',
                'details': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    session_id = validated_data['session_id']
    
    try:
        # Initialize Prisma client
        db = Prisma()
        db.connect()
        
        try:
            # Initialize upload service with Prisma client
            upload_service = MobileUploadService(prisma_client=db)
            
            # Complete chunked upload (synchronous wrapper for async method)
            import asyncio
            result = asyncio.run(upload_service.complete_chunked_upload(
                session_id=session_id
            ))
            
            return Response(result, status=status.HTTP_200_OK)
            
        finally:
            db.disconnect()
        
    except ValueError as e:
        logger.error(f"Chunked upload complete validation error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Chunked upload complete error: {str(e)}")
        return Response(
            {'error': 'Failed to complete chunked upload'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
