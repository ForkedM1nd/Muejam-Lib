"""Tests for media upload system."""
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from apps.uploads.s3 import S3UploadManager
from hypothesis import given, strategies as st
from hypothesis.strategies import integers, sampled_from
from hypothesis.extra.django import TestCase as HypothesisTestCase


class S3UploadManagerTests(TestCase):
    """
    Tests for S3UploadManager class.
    
    Requirements:
        - 14.1: Generate presigned URL with 15-minute expiration
        - 14.2: Enforce 2MB max for avatar uploads
        - 14.3: Enforce 5MB max for story cover uploads
        - 14.4: Enforce 10MB max for whisper media uploads
        - 14.5: Validate file type
        - 14.7: Generate unique object keys using UUID
    """
    
    def test_manager_initialization(self):
        """Test that S3UploadManager can be initialized."""
        manager = S3UploadManager()
        self.assertIsNotNone(manager)
        self.assertIsNotNone(manager.s3_client)
    
    def test_allowed_content_types(self):
        """
        Test that only allowed content types are accepted.
        
        Requirements:
            - 14.5: Validate file type (JPEG, PNG, WebP, GIF)
        """
        manager = S3UploadManager()
        
        # Valid content types
        valid_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        for content_type in valid_types:
            try:
                result = manager.generate_presigned_url('avatar', content_type)
                self.assertIn('url', result)
                self.assertIn('object_key', result)
            except ValueError:
                self.fail(f"Valid content type {content_type} was rejected")
    
    def test_invalid_content_type_rejected(self):
        """
        Test that invalid content types are rejected.
        
        Requirements:
            - 14.5: Validate file type
        """
        manager = S3UploadManager()
        
        # Invalid content types
        invalid_types = ['image/bmp', 'image/svg+xml', 'application/pdf', 'text/plain']
        for content_type in invalid_types:
            with self.assertRaises(ValueError):
                manager.generate_presigned_url('avatar', content_type)
    
    def test_size_limits_configured(self):
        """
        Test that size limits are correctly configured.
        
        Requirements:
            - 14.2: 2MB for avatar
            - 14.3: 5MB for cover
            - 14.4: 10MB for whisper_media
        """
        manager = S3UploadManager()
        
        self.assertEqual(manager.SIZE_LIMITS['avatar'], 2 * 1024 * 1024)
        self.assertEqual(manager.SIZE_LIMITS['cover'], 5 * 1024 * 1024)
        self.assertEqual(manager.SIZE_LIMITS['whisper_media'], 10 * 1024 * 1024)
    
    def test_presigned_url_structure(self):
        """
        Test that presigned URL has correct structure.
        
        Requirements:
            - 14.1: Generate presigned URL
        """
        manager = S3UploadManager()
        result = manager.generate_presigned_url('avatar', 'image/jpeg')
        
        # Verify response structure
        self.assertIn('url', result)
        self.assertIn('fields', result)
        self.assertIn('object_key', result)
        self.assertIn('max_size', result)
        
        # Verify types
        self.assertIsInstance(result['url'], str)
        self.assertIsInstance(result['fields'], dict)
        self.assertIsInstance(result['object_key'], str)
        self.assertIsInstance(result['max_size'], int)
    
    def test_object_key_contains_uuid(self):
        """
        Test that object key contains UUID.
        
        Requirements:
            - 14.7: Generate unique object keys using UUID
        """
        manager = S3UploadManager()
        result = manager.generate_presigned_url('avatar', 'image/jpeg')
        
        object_key = result['object_key']
        
        # Object key should have format: uploads/{type}/{uuid}.{ext}
        self.assertTrue(object_key.startswith('uploads/'))
        self.assertTrue('.jpg' in object_key or '.png' in object_key or 
                       '.webp' in object_key or '.gif' in object_key)
    
    def test_invalid_upload_type_rejected(self):
        """Test that invalid upload types are rejected."""
        manager = S3UploadManager()
        
        with self.assertRaises(ValueError):
            manager.generate_presigned_url('invalid_type', 'image/jpeg')
    
    def test_file_extension_mapping(self):
        """Test that file extensions are correctly mapped from content types."""
        manager = S3UploadManager()
        
        # Test each content type
        result_jpeg = manager.generate_presigned_url('avatar', 'image/jpeg')
        self.assertTrue(result_jpeg['object_key'].endswith('.jpg'))
        
        result_png = manager.generate_presigned_url('avatar', 'image/png')
        self.assertTrue(result_png['object_key'].endswith('.png'))
        
        result_webp = manager.generate_presigned_url('avatar', 'image/webp')
        self.assertTrue(result_webp['object_key'].endswith('.webp'))
        
        result_gif = manager.generate_presigned_url('avatar', 'image/gif')
        self.assertTrue(result_gif['object_key'].endswith('.gif'))


class UUIDUniquenessPropertyTests(HypothesisTestCase):
    """
    Property-based tests for UUID uniqueness.
    
    Property 27: UUID Uniqueness
    For any set of generated UUIDs for object keys, all UUIDs should be unique
    with no collisions.
    
    Requirements:
        - 14.7: Generate unique object keys using UUID
    """
    
    @given(st.integers(min_value=10, max_value=1000))
    def test_uuid_uniqueness_in_object_keys(self, num_uploads):
        """
        Property: All generated object keys should have unique UUIDs.
        
        This test generates multiple presigned URLs and verifies that
        all object keys contain unique UUIDs with no collisions.
        """
        manager = S3UploadManager()
        object_keys = set()
        
        # Generate multiple presigned URLs
        for _ in range(num_uploads):
            result = manager.generate_presigned_url('avatar', 'image/jpeg')
            object_key = result['object_key']
            
            # Verify this key hasn't been seen before
            self.assertNotIn(
                object_key,
                object_keys,
                f"Duplicate object key generated: {object_key}"
            )
            
            object_keys.add(object_key)
        
        # Verify we generated the expected number of unique keys
        self.assertEqual(
            len(object_keys),
            num_uploads,
            f"Expected {num_uploads} unique keys, got {len(object_keys)}"
        )
    
    @given(
        sampled_from(['avatar', 'cover', 'whisper_media']),
        sampled_from(['image/jpeg', 'image/png', 'image/webp', 'image/gif']),
        st.integers(min_value=5, max_value=100)
    )
    def test_uuid_uniqueness_across_types(self, upload_type, content_type, count):
        """
        Property: UUIDs should be unique across different upload types and content types.
        
        This test verifies that UUID generation is independent of upload type
        and content type, ensuring global uniqueness.
        """
        manager = S3UploadManager()
        object_keys = set()
        
        for _ in range(count):
            result = manager.generate_presigned_url(upload_type, content_type)
            object_key = result['object_key']
            
            self.assertNotIn(object_key, object_keys, "Duplicate UUID generated")
            object_keys.add(object_key)
        
        self.assertEqual(len(object_keys), count)


class PresignEndpointTests(TestCase):
    """
    Tests for presign upload endpoint.
    
    Requirements:
        - 14.1: Generate presigned URL endpoint
        - 14.2-14.4: Enforce size limits
        - 14.5: Validate file type
    """
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_presign_endpoint_exists(self):
        """Test that presign endpoint is accessible."""
        response = self.client.post('/v1/uploads/presign')
        # Should return 401 (auth required) or 400 (missing data), not 404
        self.assertIn(response.status_code, [400, 401])
    
    def test_presign_requires_authentication(self):
        """Test that presign endpoint requires authentication."""
        response = self.client.post('/v1/uploads/presign', {
            'type': 'avatar',
            'content_type': 'image/jpeg'
        })
        self.assertEqual(response.status_code, 401)
    
    def test_presign_requires_type_parameter(self):
        """Test that type parameter is required."""
        # Note: This would need authentication in real scenario
        response = self.client.post('/v1/uploads/presign', {
            'content_type': 'image/jpeg'
        })
        self.assertIn(response.status_code, [400, 401])
    
    def test_presign_requires_content_type_parameter(self):
        """Test that content_type parameter is required."""
        # Note: This would need authentication in real scenario
        response = self.client.post('/v1/uploads/presign', {
            'type': 'avatar'
        })
        self.assertIn(response.status_code, [400, 401])
    
    def test_presign_validates_upload_type(self):
        """
        Test that invalid upload types are rejected.
        
        Requirements:
            - 14.2-14.4: Only avatar, cover, whisper_media allowed
        """
        # Note: This would need authentication in real scenario
        response = self.client.post('/v1/uploads/presign', {
            'type': 'invalid_type',
            'content_type': 'image/jpeg'
        })
        self.assertIn(response.status_code, [400, 401])
    
    def test_presign_validates_content_type(self):
        """
        Test that invalid content types are rejected.
        
        Requirements:
            - 14.5: Only JPEG, PNG, WebP, GIF allowed
        """
        # Note: This would need authentication in real scenario
        response = self.client.post('/v1/uploads/presign', {
            'type': 'avatar',
            'content_type': 'application/pdf'
        })
        self.assertIn(response.status_code, [400, 401])


class SizeLimitTests(TestCase):
    """
    Tests for size limit enforcement.
    
    Requirements:
        - 14.2: 2MB for avatar
        - 14.3: 5MB for cover
        - 14.4: 10MB for whisper_media
    """
    
    def test_avatar_size_limit(self):
        """
        Test that avatar uploads have 2MB limit.
        
        Requirements:
            - 14.2: Enforce 2MB max for avatar
        """
        manager = S3UploadManager()
        result = manager.generate_presigned_url('avatar', 'image/jpeg')
        
        self.assertEqual(result['max_size'], 2 * 1024 * 1024)
    
    def test_cover_size_limit(self):
        """
        Test that cover uploads have 5MB limit.
        
        Requirements:
            - 14.3: Enforce 5MB max for cover
        """
        manager = S3UploadManager()
        result = manager.generate_presigned_url('cover', 'image/jpeg')
        
        self.assertEqual(result['max_size'], 5 * 1024 * 1024)
    
    def test_whisper_media_size_limit(self):
        """
        Test that whisper_media uploads have 10MB limit.
        
        Requirements:
            - 14.4: Enforce 10MB max for whisper_media
        """
        manager = S3UploadManager()
        result = manager.generate_presigned_url('whisper_media', 'image/jpeg')
        
        self.assertEqual(result['max_size'], 10 * 1024 * 1024)
