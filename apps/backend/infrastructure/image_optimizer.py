"""
Image Optimizer Service.

Provides image optimization, resizing, and format conversion.
Implements Requirements 27.7, 27.8.
"""
import os
import logging
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image
import boto3
from io import BytesIO
from django.conf import settings

logger = logging.getLogger(__name__)


class ImageOptimizer:
    """
    Service for optimizing and processing images.
    
    Implements Requirements:
    - 27.7: Image optimization (format conversion, resizing, compression)
    - 27.8: Generate multiple image sizes (thumbnail, small, medium, large)
    """
    
    # Image size configurations
    SIZES = {
        'thumbnail': (150, 150),
        'small': (400, 400),
        'medium': (800, 800),
        'large': (1200, 1200),
        'original': None  # Keep original size
    }
    
    # Supported formats
    SUPPORTED_FORMATS = ['JPEG', 'PNG', 'GIF', 'WEBP']
    
    # Quality settings
    JPEG_QUALITY = 85
    WEBP_QUALITY = 85
    PNG_COMPRESSION = 6
    
    def __init__(self):
        """Initialize S3 client for uploading optimized images."""
        self.s3_client = boto3.client(
            's3',
            region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
        )
        self.bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'muejam-uploads')
    
    def optimize_image(self, image_path: str, output_format: str = 'JPEG') -> Dict[str, Any]:
        """
        Optimize a single image.
        
        Implements Requirement 27.7: Image optimization.
        
        Args:
            image_path: Path to the image file
            output_format: Output format (JPEG, PNG, WEBP)
        
        Returns:
            Dict containing:
            - optimized_path: Path to optimized image
            - original_size: Original file size in bytes
            - optimized_size: Optimized file size in bytes
            - compression_ratio: Compression ratio percentage
        """
        try:
            # Open image
            img = Image.open(image_path)
            
            # Get original size
            original_size = os.path.getsize(image_path)
            
            # Convert RGBA to RGB if saving as JPEG
            if output_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Generate output path
            base_name = os.path.splitext(image_path)[0]
            extension = self._get_extension(output_format)
            output_path = f"{base_name}_optimized{extension}"
            
            # Save optimized image
            save_kwargs = self._get_save_kwargs(output_format)
            img.save(output_path, format=output_format, **save_kwargs)
            
            # Get optimized size
            optimized_size = os.path.getsize(output_path)
            
            # Calculate compression ratio
            compression_ratio = ((original_size - optimized_size) / original_size) * 100
            
            logger.info(f"Optimized image: {image_path} -> {output_path} ({compression_ratio:.1f}% reduction)")
            
            return {
                'status': 'success',
                'optimized_path': output_path,
                'original_size': original_size,
                'optimized_size': optimized_size,
                'compression_ratio': round(compression_ratio, 2),
                'format': output_format
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize image {image_path}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def generate_responsive_images(self, image_path: str, 
                                   formats: List[str] = ['JPEG', 'WEBP']) -> Dict[str, Any]:
        """
        Generate multiple image sizes for responsive images.
        
        Implements Requirement 27.8: Generate multiple image sizes.
        
        Args:
            image_path: Path to the original image
            formats: List of output formats to generate
        
        Returns:
            Dict containing:
            - sizes: Dict of size variants with their paths
            - formats: Dict of format variants with their paths
            - total_variants: Total number of variants generated
        """
        try:
            # Open original image
            img = Image.open(image_path)
            original_format = img.format
            
            variants = {}
            
            # Generate size variants
            for size_name, dimensions in self.SIZES.items():
                if dimensions is None:
                    # Keep original size
                    variants[size_name] = {}
                    for fmt in formats:
                        variant_path = self._generate_variant(
                            img, image_path, size_name, dimensions, fmt
                        )
                        if variant_path:
                            variants[size_name][fmt.lower()] = variant_path
                else:
                    # Generate resized variants
                    variants[size_name] = {}
                    for fmt in formats:
                        variant_path = self._generate_variant(
                            img, image_path, size_name, dimensions, fmt
                        )
                        if variant_path:
                            variants[size_name][fmt.lower()] = variant_path
            
            total_variants = sum(len(v) for v in variants.values())
            
            logger.info(f"Generated {total_variants} image variants for {image_path}")
            
            return {
                'status': 'success',
                'original_path': image_path,
                'variants': variants,
                'total_variants': total_variants,
                'sizes': list(self.SIZES.keys()),
                'formats': [f.lower() for f in formats]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate responsive images for {image_path}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def upload_to_s3(self, file_path: str, s3_key: str, 
                     content_type: str = None) -> Dict[str, Any]:
        """
        Upload optimized image to S3.
        
        Implements Requirement 27.7: Upload optimized images to S3.
        
        Args:
            file_path: Local file path
            s3_key: S3 object key
            content_type: Content type (optional, auto-detected)
        
        Returns:
            Dict containing upload details
        """
        try:
            # Auto-detect content type if not provided
            if not content_type:
                extension = os.path.splitext(file_path)[1].lower()
                content_type_map = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                content_type = content_type_map.get(extension, 'application/octet-stream')
            
            # Upload to S3
            with open(file_path, 'rb') as f:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=f,
                    ContentType=content_type,
                    CacheControl='public, max-age=31536000',  # 1 year cache
                    Metadata={
                        'optimized': 'true'
                    }
                )
            
            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            
            logger.info(f"Uploaded {file_path} to S3: {s3_key}")
            
            return {
                'status': 'success',
                's3_key': s3_key,
                's3_url': s3_url,
                'bucket': self.bucket_name,
                'content_type': content_type
            }
            
        except Exception as e:
            logger.error(f"Failed to upload {file_path} to S3: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def process_and_upload(self, image_path: str, s3_prefix: str = 'images') -> Dict[str, Any]:
        """
        Process image (optimize and generate variants) and upload to S3.
        
        Complete workflow: optimize -> generate variants -> upload all to S3.
        
        Args:
            image_path: Path to original image
            s3_prefix: S3 key prefix (folder)
        
        Returns:
            Dict containing all uploaded variants
        """
        try:
            # Generate responsive images
            result = self.generate_responsive_images(image_path, formats=['JPEG', 'WEBP'])
            
            if result['status'] != 'success':
                return result
            
            # Upload all variants to S3
            uploaded_variants = {}
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            
            for size_name, formats in result['variants'].items():
                uploaded_variants[size_name] = {}
                for fmt, variant_path in formats.items():
                    # Generate S3 key
                    s3_key = f"{s3_prefix}/{base_name}_{size_name}.{fmt}"
                    
                    # Upload to S3
                    upload_result = self.upload_to_s3(variant_path, s3_key)
                    
                    if upload_result['status'] == 'success':
                        uploaded_variants[size_name][fmt] = upload_result['s3_url']
                    
                    # Clean up local file
                    try:
                        os.remove(variant_path)
                    except:
                        pass
            
            logger.info(f"Processed and uploaded {len(uploaded_variants)} variants for {image_path}")
            
            return {
                'status': 'success',
                'original_path': image_path,
                'variants': uploaded_variants,
                'total_uploaded': sum(len(v) for v in uploaded_variants.values())
            }
            
        except Exception as e:
            logger.error(f"Failed to process and upload {image_path}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def convert_to_webp(self, image_path: str) -> Dict[str, Any]:
        """
        Convert image to WebP format for better compression.
        
        Implements Requirement 27.7: Automatic format conversion (WebP).
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Dict containing conversion details
        """
        try:
            img = Image.open(image_path)
            
            # Generate WebP path
            base_name = os.path.splitext(image_path)[0]
            webp_path = f"{base_name}.webp"
            
            # Convert and save as WebP
            img.save(webp_path, 'WEBP', quality=self.WEBP_QUALITY, method=6)
            
            # Get file sizes
            original_size = os.path.getsize(image_path)
            webp_size = os.path.getsize(webp_path)
            
            # Calculate savings
            savings = ((original_size - webp_size) / original_size) * 100
            
            logger.info(f"Converted to WebP: {image_path} -> {webp_path} ({savings:.1f}% smaller)")
            
            return {
                'status': 'success',
                'original_path': image_path,
                'webp_path': webp_path,
                'original_size': original_size,
                'webp_size': webp_size,
                'savings_percent': round(savings, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to convert to WebP: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    # Private helper methods
    
    def _generate_variant(self, img: Image.Image, original_path: str,
                         size_name: str, dimensions: Optional[Tuple[int, int]],
                         output_format: str) -> Optional[str]:
        """Generate a single image variant."""
        try:
            # Copy image
            img_copy = img.copy()
            
            # Resize if dimensions provided
            if dimensions:
                img_copy.thumbnail(dimensions, Image.Resampling.LANCZOS)
            
            # Convert RGBA to RGB if saving as JPEG
            if output_format == 'JPEG' and img_copy.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img_copy.size, (255, 255, 255))
                if img_copy.mode == 'P':
                    img_copy = img_copy.convert('RGBA')
                background.paste(img_copy, mask=img_copy.split()[-1] if img_copy.mode == 'RGBA' else None)
                img_copy = background
            
            # Generate output path
            base_name = os.path.splitext(original_path)[0]
            extension = self._get_extension(output_format)
            output_path = f"{base_name}_{size_name}{extension}"
            
            # Save variant
            save_kwargs = self._get_save_kwargs(output_format)
            img_copy.save(output_path, format=output_format, **save_kwargs)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate variant {size_name} in {output_format}: {str(e)}")
            return None
    
    def _get_extension(self, format: str) -> str:
        """Get file extension for format."""
        extensions = {
            'JPEG': '.jpg',
            'PNG': '.png',
            'GIF': '.gif',
            'WEBP': '.webp'
        }
        return extensions.get(format, '.jpg')
    
    def _get_save_kwargs(self, format: str) -> Dict[str, Any]:
        """Get save kwargs for format."""
        if format == 'JPEG':
            return {
                'quality': self.JPEG_QUALITY,
                'optimize': True,
                'progressive': True
            }
        elif format == 'PNG':
            return {
                'compress_level': self.PNG_COMPRESSION,
                'optimize': True
            }
        elif format == 'WEBP':
            return {
                'quality': self.WEBP_QUALITY,
                'method': 6  # Best compression
            }
        elif format == 'GIF':
            return {
                'optimize': True
            }
        else:
            return {}
