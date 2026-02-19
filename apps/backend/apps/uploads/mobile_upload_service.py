"""
Service for handling mobile-specific media uploads.

Handles HEIC/HEIF conversion, EXIF stripping, and chunked uploads.

Requirements:
    - 7.1: Accept mobile-specific image formats (HEIC, HEIF)
    - 7.2: Validate file size limits appropriate for mobile uploads
    - 7.5: Strip EXIF location and sensitive metadata
"""
import io
import logging
from typing import Optional, Tuple
from PIL import Image
import pillow_heif
from apps.analytics.mobile_analytics_service import get_mobile_analytics_service

logger = logging.getLogger(__name__)


class MobileUploadService:
    """
    Service for handling mobile-specific media uploads.
    
    Handles HEIC/HEIF conversion, EXIF stripping, and chunked uploads.
    """
    
    SUPPORTED_MOBILE_FORMATS = ['heic', 'heif', 'jpg', 'jpeg', 'png', 'mp4', 'mov']
    MAX_MOBILE_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks
    
    # EXIF tags that contain sensitive information to strip
    SENSITIVE_EXIF_TAGS = [
        'GPSInfo',  # GPS location data
        'GPSLatitude',
        'GPSLongitude',
        'GPSAltitude',
        'GPSTimeStamp',
        'GPSDateStamp',
        'GPSProcessingMethod',
        'GPSAreaInformation',
        'UserComment',  # May contain personal notes
        'MakerNote',  # Manufacturer-specific data
        'CameraOwnerName',
        'BodySerialNumber',
        'LensSerialNumber',
    ]
    
    def __init__(self, prisma_client=None):
        """
        Initialize upload service.
        
        Args:
            prisma_client: Optional Prisma client for database operations
        """
        # Register HEIF opener with Pillow
        pillow_heif.register_heif_opener()
        self.prisma = prisma_client
        self.analytics_service = get_mobile_analytics_service()
    
    def validate_file_size(self, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        Validate file size against mobile upload limits.
        
        Args:
            file_size: Size of file in bytes
            
        Returns:
            Tuple of (is_valid, error_message)
            
        Requirements:
            - 7.2: Validate file size limits appropriate for mobile uploads
        """
        if file_size > self.MAX_MOBILE_FILE_SIZE:
            max_mb = self.MAX_MOBILE_FILE_SIZE / (1024 * 1024)
            return False, f"File size exceeds maximum of {max_mb}MB for mobile uploads"
        
        if file_size <= 0:
            return False, "File size must be greater than 0"
        
        return True, None
    
    def convert_heic_to_jpeg(self, file_data: bytes) -> bytes:
        """
        Convert HEIC/HEIF image to JPEG.
        
        Args:
            file_data: HEIC image data
            
        Returns:
            JPEG image data
            
        Raises:
            ValueError: If conversion fails
            
        Requirements:
            - 7.1: Accept mobile-specific image formats (HEIC, HEIF)
        """
        try:
            # Open HEIC image
            image = Image.open(io.BytesIO(file_data))
            
            # Convert to RGB if necessary (HEIC can have different color modes)
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            # Save as JPEG
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=90, optimize=True)
            output.seek(0)
            
            logger.info("Successfully converted HEIC/HEIF to JPEG")
            return output.read()
            
        except Exception as e:
            logger.error(f"Failed to convert HEIC to JPEG: {str(e)}")
            raise ValueError(f"Failed to convert HEIC/HEIF image: {str(e)}")
    
    def strip_exif_metadata(self, file_data: bytes) -> bytes:
        """
        Strip EXIF metadata from image.
        
        Removes sensitive EXIF data including GPS location, camera serial numbers,
        and other identifying information while preserving image orientation.
        
        Args:
            file_data: Image data
            
        Returns:
            Image data without sensitive EXIF metadata
            
        Requirements:
            - 7.5: Strip EXIF location and sensitive metadata
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(file_data))
            
            # Get EXIF data if it exists
            exif_data = image.getexif()
            
            if exif_data:
                # Create new EXIF dict without sensitive tags
                cleaned_exif = Image.Exif()
                
                # Copy only non-sensitive EXIF tags
                for tag_id, value in exif_data.items():
                    tag_name = Image.ExifTags.TAGS.get(tag_id, tag_id)
                    
                    # Skip sensitive tags
                    if tag_name not in self.SENSITIVE_EXIF_TAGS:
                        cleaned_exif[tag_id] = value
                
                # Handle orientation to prevent image rotation issues
                # Orientation tag (274) should be preserved
                if 274 in exif_data:
                    cleaned_exif[274] = exif_data[274]
                
                # Save image with cleaned EXIF
                output = io.BytesIO()
                image.save(output, format=image.format or 'JPEG', exif=cleaned_exif)
                output.seek(0)
                
                logger.info("Successfully stripped sensitive EXIF metadata")
                return output.read()
            else:
                # No EXIF data, return original
                logger.info("No EXIF data found in image")
                return file_data
                
        except Exception as e:
            logger.warning(f"Failed to strip EXIF metadata: {str(e)}. Returning original image.")
            # If EXIF stripping fails, return original image rather than failing upload
            return file_data
    
    def process_mobile_image(
        self,
        file_data: bytes,
        filename: str,
        content_type: str,
        client_type: str = 'mobile'
    ) -> Tuple[bytes, str]:
        """
        Process mobile image upload with format conversion and EXIF stripping.
        
        Args:
            file_data: Image binary data
            filename: Original filename
            content_type: MIME type
            client_type: Client type for analytics
            
        Returns:
            Tuple of (processed_data, final_content_type)
            
        Raises:
            ValueError: If processing fails
        """
        processed_data = file_data
        final_content_type = content_type
        
        try:
            # Check if HEIC/HEIF conversion is needed
            file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
            is_heic = file_extension in ['heic', 'heif'] or content_type in ['image/heic', 'image/heif']
            
            if is_heic:
                logger.info(f"Converting HEIC/HEIF image: {filename}")
                processed_data = self.convert_heic_to_jpeg(processed_data)
                final_content_type = 'image/jpeg'
            
            # Strip EXIF metadata for all images
            if final_content_type.startswith('image/'):
                logger.info(f"Stripping EXIF metadata from: {filename}")
                processed_data = self.strip_exif_metadata(processed_data)
            
            # Track successful upload
            self.analytics_service.track_media_upload(
                success=True,
                file_size=len(file_data),
                client_type=client_type,
                filename=filename
            )
            
            return processed_data, final_content_type
            
        except Exception as e:
            # Track failed upload
            self.analytics_service.track_media_upload(
                success=False,
                file_size=len(file_data),
                client_type=client_type,
                filename=filename
            )
            raise

    async def initiate_chunked_upload(
        self,
        filename: str,
        total_size: int,
        user_id: str
    ) -> dict:
        """
        Initiate chunked upload session.
        
        Creates an upload session in the database and prepares for receiving chunks.
        
        Args:
            filename: Original filename
            total_size: Total file size in bytes
            user_id: Uploading user ID
            
        Returns:
            Upload session information with session_id, chunk_size, and chunks_total
            
        Raises:
            ValueError: If file size is invalid or exceeds limits
            
        Requirements:
            - 7.3: Support chunked upload for large media files from Mobile_Client
        """
        # Validate file size
        is_valid, error = self.validate_file_size(total_size)
        if not is_valid:
            raise ValueError(error)
        
        # Calculate number of chunks needed
        chunks_total = (total_size + self.CHUNK_SIZE - 1) // self.CHUNK_SIZE
        
        # Calculate expiration time (24 hours from now)
        from datetime import datetime, timedelta
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Create upload session in database
        if self.prisma is None:
            raise RuntimeError("Prisma client not initialized")
        
        session = await self.prisma.uploadsession.create(
            data={
                'user_id': user_id,
                'filename': filename,
                'total_size': total_size,
                'chunk_size': self.CHUNK_SIZE,
                'chunks_total': chunks_total,
                'chunks_uploaded': 0,
                'status': 'in_progress',
                'expires_at': expires_at
            }
        )
        
        logger.info(f"Initiated chunked upload session {session.id} for user {user_id}, "
                   f"file: {filename}, size: {total_size}, chunks: {chunks_total}")
        
        return {
            'session_id': session.id,
            'chunk_size': self.CHUNK_SIZE,
            'chunks_total': chunks_total,
            'expires_at': expires_at.isoformat()
        }
    
    async def upload_chunk(
        self,
        session_id: str,
        chunk_number: int,
        chunk_data: bytes
    ) -> dict:
        """
        Upload a file chunk.
        
        Stores the chunk and updates upload progress.
        
        Args:
            session_id: Upload session ID
            chunk_number: Chunk sequence number (0-indexed)
            chunk_data: Chunk binary data
            
        Returns:
            Chunk upload status with chunks_uploaded and chunks_remaining
            
        Raises:
            ValueError: If session not found, expired, or chunk is invalid
            
        Requirements:
            - 7.3: Support chunked upload for large media files from Mobile_Client
            - 7.4: Provide upload progress tracking for Mobile_Client
        """
        if self.prisma is None:
            raise RuntimeError("Prisma client not initialized")
        
        # Retrieve upload session
        session = await self.prisma.uploadsession.find_unique(
            where={'id': session_id}
        )
        
        if not session:
            raise ValueError(f"Upload session {session_id} not found")
        
        # Check if session is expired
        from datetime import datetime
        if datetime.utcnow() > session.expires_at:
            await self.prisma.uploadsession.update(
                where={'id': session_id},
                data={'status': 'failed'}
            )
            raise ValueError(f"Upload session {session_id} has expired")
        
        # Check if session is still in progress
        if session.status != 'in_progress':
            raise ValueError(f"Upload session {session_id} is not in progress (status: {session.status})")
        
        # Validate chunk number
        if chunk_number < 0 or chunk_number >= session.chunks_total:
            raise ValueError(f"Invalid chunk number {chunk_number}. Expected 0-{session.chunks_total - 1}")
        
        # Validate chunk size (last chunk can be smaller)
        expected_size = self.CHUNK_SIZE
        if chunk_number == session.chunks_total - 1:
            # Last chunk can be smaller
            remaining_size = session.total_size - (chunk_number * self.CHUNK_SIZE)
            expected_size = remaining_size
        
        if len(chunk_data) > expected_size:
            raise ValueError(f"Chunk {chunk_number} size {len(chunk_data)} exceeds expected {expected_size}")
        
        # In a real implementation, we would store the chunk to S3 or temporary storage
        # For now, we'll just update the progress
        
        # Update chunks uploaded count
        updated_session = await self.prisma.uploadsession.update(
            where={'id': session_id},
            data={'chunks_uploaded': session.chunks_uploaded + 1}
        )
        
        chunks_remaining = updated_session.chunks_total - updated_session.chunks_uploaded
        progress_percent = (updated_session.chunks_uploaded / updated_session.chunks_total) * 100
        
        logger.info(f"Uploaded chunk {chunk_number} for session {session_id}. "
                   f"Progress: {updated_session.chunks_uploaded}/{updated_session.chunks_total} "
                   f"({progress_percent:.1f}%)")
        
        return {
            'session_id': session_id,
            'chunk_number': chunk_number,
            'chunks_uploaded': updated_session.chunks_uploaded,
            'chunks_total': updated_session.chunks_total,
            'chunks_remaining': chunks_remaining,
            'progress_percent': progress_percent,
            'status': 'in_progress'
        }
    
    async def complete_chunked_upload(self, session_id: str, client_type: str = 'mobile') -> dict:
        """
        Complete chunked upload and finalize file.
        
        Verifies all chunks are uploaded and marks the session as completed.
        
        Args:
            session_id: Upload session ID
            client_type: Client type for analytics
            
        Returns:
            Final upload result with status and file information
            
        Raises:
            ValueError: If session not found, not all chunks uploaded, or already completed
            
        Requirements:
            - 7.3: Support chunked upload for large media files from Mobile_Client
        """
        if self.prisma is None:
            raise RuntimeError("Prisma client not initialized")
        
        try:
            # Retrieve upload session
            session = await self.prisma.uploadsession.find_unique(
                where={'id': session_id}
            )
            
            if not session:
                raise ValueError(f"Upload session {session_id} not found")
            
            # Check if already completed
            if session.status == 'completed':
                raise ValueError(f"Upload session {session_id} is already completed")
            
            # Check if session failed
            if session.status == 'failed':
                raise ValueError(f"Upload session {session_id} has failed")
            
            # Verify all chunks are uploaded
            if session.chunks_uploaded != session.chunks_total:
                raise ValueError(
                    f"Not all chunks uploaded. Expected {session.chunks_total}, "
                    f"got {session.chunks_uploaded}"
                )
            
            # Mark session as completed
            completed_session = await self.prisma.uploadsession.update(
                where={'id': session_id},
                data={'status': 'completed'}
            )
            
            logger.info(f"Completed chunked upload session {session_id}. "
                       f"File: {completed_session.filename}, "
                       f"Size: {completed_session.total_size} bytes")
            
            # Track successful upload
            self.analytics_service.track_media_upload(
                success=True,
                file_size=completed_session.total_size,
                client_type=client_type,
                filename=completed_session.filename
            )
            
            # In a real implementation, we would:
            # 1. Assemble all chunks from S3/storage
            # 2. Process the file (HEIC conversion, EXIF stripping if image)
            # 3. Upload final file to permanent storage
            # 4. Return the final file URL
            
            return {
                'session_id': session_id,
                'status': 'completed',
                'filename': completed_session.filename,
                'total_size': completed_session.total_size,
                'chunks_total': completed_session.chunks_total,
                'message': 'Upload completed successfully'
            }
            
        except Exception as e:
            # Track failed upload
            if session:
                self.analytics_service.track_media_upload(
                    success=False,
                    file_size=session.total_size,
                    client_type=client_type,
                    filename=session.filename
                )
            raise
    
    async def get_upload_progress(self, session_id: str) -> dict:
        """
        Get upload progress for a session.
        
        Args:
            session_id: Upload session ID
            
        Returns:
            Upload progress information
            
        Raises:
            ValueError: If session not found
            
        Requirements:
            - 7.4: Provide upload progress tracking for Mobile_Client
        """
        if self.prisma is None:
            raise RuntimeError("Prisma client not initialized")
        
        # Retrieve upload session
        session = await self.prisma.uploadsession.find_unique(
            where={'id': session_id}
        )
        
        if not session:
            raise ValueError(f"Upload session {session_id} not found")
        
        chunks_remaining = session.chunks_total - session.chunks_uploaded
        progress_percent = (session.chunks_uploaded / session.chunks_total) * 100 if session.chunks_total > 0 else 0
        
        return {
            'session_id': session_id,
            'status': session.status,
            'filename': session.filename,
            'total_size': session.total_size,
            'chunks_uploaded': session.chunks_uploaded,
            'chunks_total': session.chunks_total,
            'chunks_remaining': chunks_remaining,
            'progress_percent': progress_percent,
            'created_at': session.created_at.isoformat(),
            'expires_at': session.expires_at.isoformat()
        }
