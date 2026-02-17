"""S3 upload manager for presigned URL generation."""
import boto3
from botocore.config import Config
from django.conf import settings
import uuid


class S3UploadManager:
    """
    Manager for S3 upload operations using presigned URLs.
    
    Requirements:
        - 14.1: Generate presigned S3 URL with 15-minute expiration
        - 14.2: Enforce 2MB max for avatar uploads
        - 14.3: Enforce 5MB max for story cover uploads
        - 14.4: Enforce 10MB max for whisper media uploads
        - 14.5: Validate file type (JPEG, PNG, WebP, GIF)
        - 14.7: Generate unique object keys using UUID
    """
    
    # File size limits in bytes
    SIZE_LIMITS = {
        'avatar': 2 * 1024 * 1024,      # 2MB
        'cover': 5 * 1024 * 1024,       # 5MB
        'whisper_media': 10 * 1024 * 1024  # 10MB
    }
    
    # Allowed content types
    ALLOWED_CONTENT_TYPES = [
        'image/jpeg',
        'image/png',
        'image/webp',
        'image/gif'
    ]
    
    def __init__(self):
        """Initialize S3 client with configuration."""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            config=Config(signature_version='s3v4')
        )
        self.bucket = settings.AWS_S3_BUCKET
    
    def generate_presigned_url(
        self,
        upload_type: str,
        content_type: str
    ) -> dict:
        """
        Generate presigned POST URL for direct S3 upload.
        
        Args:
            upload_type: Type of upload ('avatar', 'cover', 'whisper_media')
            content_type: MIME type of the file
            
        Returns:
            Dictionary with presigned URL, fields, and object key
            
        Raises:
            ValueError: If upload_type or content_type is invalid
            
        Requirements:
            - 14.1: Generate presigned URL with 15-minute expiration
            - 14.2-14.4: Enforce size limits based on upload type
            - 14.5: Validate file type
            - 14.7: Generate unique object keys using UUID
        """
        # Validate upload type
        if upload_type not in self.SIZE_LIMITS:
            raise ValueError(
                f"Invalid upload type. Must be one of: {', '.join(self.SIZE_LIMITS.keys())}"
            )
        
        # Validate content type
        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValueError(
                f"Invalid content type. Must be one of: {', '.join(self.ALLOWED_CONTENT_TYPES)}"
            )
        
        # Get size limit for this upload type
        max_size = self.SIZE_LIMITS[upload_type]
        
        # Generate unique object key using UUID
        file_extension = self._get_file_extension(content_type)
        object_key = f"uploads/{upload_type}/{uuid.uuid4()}.{file_extension}"
        
        # Define upload conditions
        conditions = [
            {'bucket': self.bucket},
            {'key': object_key},
            {'Content-Type': content_type},
            ['content-length-range', 1, max_size]
        ]
        
        # Generate presigned POST
        presigned_post = self.s3_client.generate_presigned_post(
            Bucket=self.bucket,
            Key=object_key,
            Fields={'Content-Type': content_type},
            Conditions=conditions,
            ExpiresIn=900  # 15 minutes
        )
        
        return {
            'url': presigned_post['url'],
            'fields': presigned_post['fields'],
            'object_key': object_key,
            'max_size': max_size
        }
    
    def _get_file_extension(self, content_type: str) -> str:
        """
        Get file extension from content type.
        
        Args:
            content_type: MIME type
            
        Returns:
            File extension without dot
        """
        extension_map = {
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'image/webp': 'webp',
            'image/gif': 'gif'
        }
        return extension_map.get(content_type, 'jpg')
