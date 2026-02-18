"""NSFW content detection service using AWS Rekognition."""
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class NSFWDetector:
    """Service for detecting NSFW content in images using AWS Rekognition."""
    
    # Labels that indicate explicit NSFW content
    EXPLICIT_LABELS = [
        'Explicit Nudity',
        'Graphic Violence Or Gore',
        'Sexual Activity'
    ]
    
    # Confidence threshold for automatic NSFW flagging
    NSFW_CONFIDENCE_THRESHOLD = 80.0
    
    # Minimum confidence for Rekognition API
    MIN_CONFIDENCE = 60.0
    
    def __init__(self):
        """Initialize AWS Rekognition client."""
        try:
            self.rekognition = boto3.client(
                'rekognition',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=getattr(settings, 'AWS_REGION', 'us-east-1'),
                config=Config(
                    signature_version='v4',
                    retries={'max_attempts': 3, 'mode': 'standard'}
                )
            )
        except Exception as e:
            logger.error(f"Failed to initialize AWS Rekognition client: {e}")
            raise
    
    def parse_s3_url(self, s3_url: str) -> tuple[str, str]:
        """
        Parse S3 URL to extract bucket and key.
        
        Args:
            s3_url: S3 URL in format s3://bucket/key or https://bucket.s3.region.amazonaws.com/key
            
        Returns:
            Tuple of (bucket, key)
        """
        if s3_url.startswith('s3://'):
            # Format: s3://bucket/key
            parts = s3_url[5:].split('/', 1)
            bucket = parts[0]
            key = parts[1] if len(parts) > 1 else ''
        elif 's3.amazonaws.com' in s3_url or 's3-' in s3_url:
            # Format: https://bucket.s3.region.amazonaws.com/key
            # or https://s3.region.amazonaws.com/bucket/key
            from urllib.parse import urlparse
            parsed = urlparse(s3_url)
            path_parts = parsed.path.lstrip('/').split('/', 1)
            
            if parsed.netloc.startswith('s3'):
                # Format: https://s3.region.amazonaws.com/bucket/key
                bucket = path_parts[0]
                key = path_parts[1] if len(path_parts) > 1 else ''
            else:
                # Format: https://bucket.s3.region.amazonaws.com/key
                bucket = parsed.netloc.split('.')[0]
                key = parsed.path.lstrip('/')
        else:
            raise ValueError(f"Invalid S3 URL format: {s3_url}")
        
        return bucket, key
    
    def analyze_image(self, image_url: str) -> Dict:
        """
        Analyze an image for NSFW content using AWS Rekognition.
        
        Args:
            image_url: S3 URL of the image to analyze
            
        Returns:
            Dictionary containing:
                - is_nsfw: Boolean indicating if content is NSFW
                - confidence: Highest confidence score from detected labels
                - labels: List of detected moderation labels
                - error: Error message if analysis failed (optional)
        """
        try:
            # Parse S3 URL
            s3_bucket, s3_key = self.parse_s3_url(image_url)
            
            logger.info(f"Analyzing image for NSFW content: s3://{s3_bucket}/{s3_key}")
            
            # Call AWS Rekognition
            response = self.rekognition.detect_moderation_labels(
                Image={
                    'S3Object': {
                        'Bucket': s3_bucket,
                        'Name': s3_key
                    }
                },
                MinConfidence=self.MIN_CONFIDENCE
            )
            
            # Analyze results
            is_nsfw = False
            confidence = 0.0
            labels = []
            
            for label in response.get('ModerationLabels', []):
                label_name = label['Name']
                label_confidence = label['Confidence']
                
                labels.append({
                    'name': label_name,
                    'confidence': label_confidence,
                    'parent_name': label.get('ParentName', '')
                })
                
                # Track highest confidence
                if label_confidence > confidence:
                    confidence = label_confidence
                
                # Check if this is an explicit NSFW label with high confidence
                if (label_confidence > self.NSFW_CONFIDENCE_THRESHOLD and 
                    label_name in self.EXPLICIT_LABELS):
                    is_nsfw = True
                    logger.info(
                        f"NSFW content detected: {label_name} "
                        f"(confidence: {label_confidence:.2f}%)"
                    )
            
            result = {
                'is_nsfw': is_nsfw,
                'confidence': confidence,
                'labels': labels
            }
            
            logger.info(
                f"NSFW analysis complete: is_nsfw={is_nsfw}, "
                f"confidence={confidence:.2f}%, labels_count={len(labels)}"
            )
            
            return result
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(
                f"AWS Rekognition API error: {error_code} - {error_message}"
            )
            return {
                'is_nsfw': False,
                'confidence': 0.0,
                'labels': [],
                'error': f"AWS Rekognition error: {error_code}"
            }
            
        except ValueError as e:
            logger.error(f"Invalid S3 URL: {e}")
            return {
                'is_nsfw': False,
                'confidence': 0.0,
                'labels': [],
                'error': str(e)
            }
            
        except Exception as e:
            logger.error(f"Unexpected error during NSFW analysis: {e}")
            return {
                'is_nsfw': False,
                'confidence': 0.0,
                'labels': [],
                'error': f"Unexpected error: {str(e)}"
            }
    
    def analyze_image_bytes(self, image_bytes: bytes) -> Dict:
        """
        Analyze image bytes for NSFW content using AWS Rekognition.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Dictionary containing analysis results (same format as analyze_image)
        """
        try:
            logger.info("Analyzing image bytes for NSFW content")
            
            # Call AWS Rekognition with image bytes
            response = self.rekognition.detect_moderation_labels(
                Image={'Bytes': image_bytes},
                MinConfidence=self.MIN_CONFIDENCE
            )
            
            # Analyze results (same logic as analyze_image)
            is_nsfw = False
            confidence = 0.0
            labels = []
            
            for label in response.get('ModerationLabels', []):
                label_name = label['Name']
                label_confidence = label['Confidence']
                
                labels.append({
                    'name': label_name,
                    'confidence': label_confidence,
                    'parent_name': label.get('ParentName', '')
                })
                
                if label_confidence > confidence:
                    confidence = label_confidence
                
                if (label_confidence > self.NSFW_CONFIDENCE_THRESHOLD and 
                    label_name in self.EXPLICIT_LABELS):
                    is_nsfw = True
            
            return {
                'is_nsfw': is_nsfw,
                'confidence': confidence,
                'labels': labels
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(
                f"AWS Rekognition API error: {error_code} - {error_message}"
            )
            return {
                'is_nsfw': False,
                'confidence': 0.0,
                'labels': [],
                'error': f"AWS Rekognition error: {error_code}"
            }
            
        except Exception as e:
            logger.error(f"Unexpected error during NSFW analysis: {e}")
            return {
                'is_nsfw': False,
                'confidence': 0.0,
                'labels': [],
                'error': f"Unexpected error: {str(e)}"
            }


# Singleton instance
_nsfw_detector_instance: Optional[NSFWDetector] = None


def get_nsfw_detector() -> NSFWDetector:
    """Get or create the singleton NSFWDetector instance."""
    global _nsfw_detector_instance
    if _nsfw_detector_instance is None:
        _nsfw_detector_instance = NSFWDetector()
    return _nsfw_detector_instance
