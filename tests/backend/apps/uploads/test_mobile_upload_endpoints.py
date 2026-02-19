"""
Unit tests for mobile upload endpoints.

Tests the REST API endpoints for mobile media uploads including:
- Single media upload with HEIC conversion and EXIF stripping
- Chunked upload initialization
- Chunk upload
- Chunked upload completion
"""
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from prisma import Prisma
import asyncio
import io
from PIL import Image
from unittest.mock import patch, MagicMock


class MobileUploadEndpointsTest(TestCase):
    """Test mobile upload endpoints."""
    
    def setUp(self):
        """Set up test client and mock authentication."""
        self.client = APIClient()
        self.user_id = 'test_user_123'
        
        # Mock JWT token
        self.mock_token = 'mock_jwt_token'
        
        # Mock user data that would come from JWT
        self.mock_user = {'sub': self.user_id}
    
    def _create_test_image(self, format='JPEG', size=(100, 100)):
        """Create a test image file."""
        image = Image.new('RGB', size, color='red')
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        buffer.seek(0)
        buffer.name = f'test.{format.lower()}'
        return buffer
    
    @patch('apps.uploads.views.request')
    def test_mobile_media_upload_success(self, mock_request):
        """Test successful mobile media upload."""
        # Create test image
        test_file = self._create_test_image()
        
        # Mock authentication
        mock_request.user = self.mock_user
        self.client.force_authenticate(user=self.mock_user)
        
        # Make request
        response = self.client.post(
            '/v1/uploads/media',
            {
                'file': test_file,
                'filename': 'test.jpg',
                'content_type': 'image/jpeg'
            },
            format='multipart'
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json())
        self.assertEqual(response.json()['status'], 'success')
    
    def test_mobile_media_upload_missing_file(self):
        """Test mobile media upload with missing file."""
        self.client.force_authenticate(user=self.mock_user)
        
        response = self.client.post(
            '/v1/uploads/media',
            {
                'filename': 'test.jpg',
                'content_type': 'image/jpeg'
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
    
    def test_mobile_media_upload_unauthenticated(self):
        """Test mobile media upload without authentication."""
        test_file = self._create_test_image()
        
        response = self.client.post(
            '/v1/uploads/media',
            {
                'file': test_file,
                'filename': 'test.jpg',
                'content_type': 'image/jpeg'
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 401)
    
    @patch('apps.uploads.views.MobileUploadService')
    def test_mobile_media_upload_file_too_large(self, mock_service):
        """Test mobile media upload with file exceeding size limit."""
        self.client.force_authenticate(user=self.mock_user)
        
        # Mock service to return size validation error
        mock_instance = mock_service.return_value
        mock_instance.validate_file_size.return_value = (False, 'File size exceeds maximum')
        
        test_file = self._create_test_image()
        
        response = self.client.post(
            '/v1/uploads/media',
            {
                'file': test_file,
                'filename': 'test.jpg',
                'content_type': 'image/jpeg'
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 413)
        self.assertIn('error', response.json())


class ChunkedUploadEndpointsTest(TestCase):
    """Test chunked upload endpoints."""
    
    def setUp(self):
        """Set up test client and database."""
        self.client = APIClient()
        self.user_id = 'test_user_123'
        self.mock_user = {'sub': self.user_id}
        
        # Initialize database
        self.db = Prisma()
        asyncio.run(self._async_setup())
    
    async def _async_setup(self):
        """Async setup for database connection."""
        await self.db.connect()
    
    def tearDown(self):
        """Clean up database."""
        asyncio.run(self._async_teardown())
    
    async def _async_teardown(self):
        """Async teardown for database cleanup."""
        # Clean up test upload sessions
        await self.db.uploadsession.delete_many(
            where={'user_id': self.user_id}
        )
        await self.db.disconnect()
    
    def test_chunked_upload_init_success(self):
        """Test successful chunked upload initialization."""
        self.client.force_authenticate(user=self.mock_user)
        
        response = self.client.post(
            '/v1/uploads/chunked/init',
            {
                'filename': 'large_video.mp4',
                'total_size': 10 * 1024 * 1024  # 10MB
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('session_id', data)
        self.assertIn('chunk_size', data)
        self.assertIn('chunks_total', data)
        self.assertIn('expires_at', data)
    
    def test_chunked_upload_init_missing_fields(self):
        """Test chunked upload init with missing required fields."""
        self.client.force_authenticate(user=self.mock_user)
        
        response = self.client.post(
            '/v1/uploads/chunked/init',
            {'filename': 'test.mp4'},
            format='json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
    
    def test_chunked_upload_init_invalid_size(self):
        """Test chunked upload init with invalid file size."""
        self.client.force_authenticate(user=self.mock_user)
        
        response = self.client.post(
            '/v1/uploads/chunked/init',
            {
                'filename': 'test.mp4',
                'total_size': 0  # Invalid size
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_chunked_upload_init_unauthenticated(self):
        """Test chunked upload init without authentication."""
        response = self.client.post(
            '/v1/uploads/chunked/init',
            {
                'filename': 'test.mp4',
                'total_size': 10 * 1024 * 1024
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_chunked_upload_chunk_success(self):
        """Test successful chunk upload."""
        self.client.force_authenticate(user=self.mock_user)
        
        # First initialize upload
        init_response = self.client.post(
            '/v1/uploads/chunked/init',
            {
                'filename': 'test.mp4',
                'total_size': 10 * 1024 * 1024
            },
            format='json'
        )
        
        session_id = init_response.json()['session_id']
        
        # Create chunk data
        chunk_data = io.BytesIO(b'x' * (5 * 1024 * 1024))  # 5MB chunk
        chunk_data.name = 'chunk_0'
        
        # Upload chunk
        response = self.client.post(
            '/v1/uploads/chunked/chunk',
            {
                'session_id': session_id,
                'chunk_number': 0,
                'chunk_data': chunk_data
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('chunks_uploaded', data)
        self.assertIn('chunks_remaining', data)
        self.assertIn('progress_percent', data)
    
    def test_chunked_upload_chunk_invalid_session(self):
        """Test chunk upload with invalid session ID."""
        self.client.force_authenticate(user=self.mock_user)
        
        chunk_data = io.BytesIO(b'x' * 1024)
        chunk_data.name = 'chunk_0'
        
        response = self.client.post(
            '/v1/uploads/chunked/chunk',
            {
                'session_id': 'invalid_session_id',
                'chunk_number': 0,
                'chunk_data': chunk_data
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
    
    def test_chunked_upload_complete_success(self):
        """Test successful chunked upload completion."""
        self.client.force_authenticate(user=self.mock_user)
        
        # Initialize upload
        init_response = self.client.post(
            '/v1/uploads/chunked/init',
            {
                'filename': 'test.mp4',
                'total_size': 5 * 1024 * 1024  # 5MB (1 chunk)
            },
            format='json'
        )
        
        session_id = init_response.json()['session_id']
        
        # Upload chunk
        chunk_data = io.BytesIO(b'x' * (5 * 1024 * 1024))
        chunk_data.name = 'chunk_0'
        
        self.client.post(
            '/v1/uploads/chunked/chunk',
            {
                'session_id': session_id,
                'chunk_number': 0,
                'chunk_data': chunk_data
            },
            format='multipart'
        )
        
        # Complete upload
        response = self.client.post(
            '/v1/uploads/chunked/complete',
            {'session_id': session_id},
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'completed')
        self.assertIn('filename', data)
        self.assertIn('total_size', data)
    
    def test_chunked_upload_complete_incomplete_chunks(self):
        """Test chunked upload completion with missing chunks."""
        self.client.force_authenticate(user=self.mock_user)
        
        # Initialize upload with 2 chunks
        init_response = self.client.post(
            '/v1/uploads/chunked/init',
            {
                'filename': 'test.mp4',
                'total_size': 10 * 1024 * 1024  # 10MB (2 chunks)
            },
            format='json'
        )
        
        session_id = init_response.json()['session_id']
        
        # Try to complete without uploading all chunks
        response = self.client.post(
            '/v1/uploads/chunked/complete',
            {'session_id': session_id},
            format='json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
    
    def test_chunked_upload_complete_invalid_session(self):
        """Test chunked upload completion with invalid session ID."""
        self.client.force_authenticate(user=self.mock_user)
        
        response = self.client.post(
            '/v1/uploads/chunked/complete',
            {'session_id': 'invalid_session_id'},
            format='json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())


class MobileUploadIntegrationTest(TestCase):
    """Integration tests for complete mobile upload flows."""
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.user_id = 'test_user_123'
        self.mock_user = {'sub': self.user_id}
        
        # Initialize database
        self.db = Prisma()
        asyncio.run(self._async_setup())
    
    async def _async_setup(self):
        """Async setup for database connection."""
        await self.db.connect()
    
    def tearDown(self):
        """Clean up database."""
        asyncio.run(self._async_teardown())
    
    async def _async_teardown(self):
        """Async teardown for database cleanup."""
        await self.db.uploadsession.delete_many(
            where={'user_id': self.user_id}
        )
        await self.db.disconnect()
    
    def test_complete_chunked_upload_flow(self):
        """Test complete chunked upload flow from init to completion."""
        self.client.force_authenticate(user=self.mock_user)
        
        # Step 1: Initialize upload
        init_response = self.client.post(
            '/v1/uploads/chunked/init',
            {
                'filename': 'video.mp4',
                'total_size': 10 * 1024 * 1024  # 10MB
            },
            format='json'
        )
        
        self.assertEqual(init_response.status_code, 200)
        session_id = init_response.json()['session_id']
        chunks_total = init_response.json()['chunks_total']
        
        # Step 2: Upload all chunks
        for i in range(chunks_total):
            chunk_size = 5 * 1024 * 1024  # 5MB
            chunk_data = io.BytesIO(b'x' * chunk_size)
            chunk_data.name = f'chunk_{i}'
            
            chunk_response = self.client.post(
                '/v1/uploads/chunked/chunk',
                {
                    'session_id': session_id,
                    'chunk_number': i,
                    'chunk_data': chunk_data
                },
                format='multipart'
            )
            
            self.assertEqual(chunk_response.status_code, 200)
            self.assertEqual(chunk_response.json()['chunks_uploaded'], i + 1)
        
        # Step 3: Complete upload
        complete_response = self.client.post(
            '/v1/uploads/chunked/complete',
            {'session_id': session_id},
            format='json'
        )
        
        self.assertEqual(complete_response.status_code, 200)
        self.assertEqual(complete_response.json()['status'], 'completed')
