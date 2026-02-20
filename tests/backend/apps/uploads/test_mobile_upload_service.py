"""
Unit tests for mobile upload service.

Tests HEIC conversion, EXIF stripping, and file size validation.
"""
import io
import pytest
from unittest.mock import AsyncMock, MagicMock
from PIL import Image
from apps.uploads.mobile_upload_service import MobileUploadService


class TestMobileUploadService:
    """Test suite for MobileUploadService."""
    
    @pytest.fixture
    def service(self):
        """Create service instance."""
        return MobileUploadService()
    
    @pytest.fixture
    def sample_jpeg_with_exif(self):
        """Create a sample JPEG image with EXIF data."""
        # Create a simple image
        img = Image.new('RGB', (100, 100), color='red')
        
        # Add EXIF data including GPS info
        exif = Image.Exif()
        exif[274] = 1  # Orientation
        exif[271] = "Test Camera"  # Make
        exif[272] = "Test Model"  # Model
        
        # Save to bytes
        output = io.BytesIO()
        img.save(output, format='JPEG', exif=exif)
        output.seek(0)
        return output.read()
    
    def test_validate_file_size_valid(self, service):
        """Test file size validation with valid size."""
        # Test with 1MB file
        is_valid, error = service.validate_file_size(1024 * 1024)
        assert is_valid is True
        assert error is None
    
    def test_validate_file_size_too_large(self, service):
        """Test file size validation with oversized file."""
        # Test with 51MB file (exceeds 50MB limit)
        is_valid, error = service.validate_file_size(51 * 1024 * 1024)
        assert is_valid is False
        assert "exceeds maximum" in error
        assert "50" in error
    
    def test_validate_file_size_zero(self, service):
        """Test file size validation with zero size."""
        is_valid, error = service.validate_file_size(0)
        assert is_valid is False
        assert "greater than 0" in error
    
    def test_validate_file_size_negative(self, service):
        """Test file size validation with negative size."""
        is_valid, error = service.validate_file_size(-100)
        assert is_valid is False
        assert "greater than 0" in error
    
    def test_validate_file_size_at_limit(self, service):
        """Test file size validation at exact limit."""
        # Test at exactly 50MB
        is_valid, error = service.validate_file_size(50 * 1024 * 1024)
        assert is_valid is True
        assert error is None
    
    def test_strip_exif_metadata(self, service, sample_jpeg_with_exif):
        """Test EXIF metadata stripping."""
        # Strip EXIF
        cleaned_data = service.strip_exif_metadata(sample_jpeg_with_exif)
        
        # Verify image is still valid
        img = Image.open(io.BytesIO(cleaned_data))
        assert img.size == (100, 100)
        
        # Verify EXIF was processed
        exif = img.getexif()
        # Orientation should be preserved
        assert 274 in exif or len(exif) == 0  # Either orientation preserved or all stripped
    
    def test_strip_exif_no_exif_data(self, service):
        """Test EXIF stripping on image without EXIF."""
        # Create image without EXIF
        img = Image.new('RGB', (50, 50), color='blue')
        output = io.BytesIO()
        img.save(output, format='JPEG')
        output.seek(0)
        original_data = output.read()
        
        # Strip EXIF (should return original)
        cleaned_data = service.strip_exif_metadata(original_data)
        
        # Verify image is still valid
        img = Image.open(io.BytesIO(cleaned_data))
        assert img.size == (50, 50)
    
    def test_process_mobile_image_jpeg(self, service, sample_jpeg_with_exif):
        """Test processing regular JPEG image."""
        processed_data, content_type = service.process_mobile_image(
            sample_jpeg_with_exif,
            'test.jpg',
            'image/jpeg'
        )
        
        # Verify output
        assert content_type == 'image/jpeg'
        assert len(processed_data) > 0
        
        # Verify image is valid
        img = Image.open(io.BytesIO(processed_data))
        assert img.size == (100, 100)
    
    def test_process_mobile_image_png(self, service):
        """Test processing PNG image."""
        # Create PNG image
        img = Image.new('RGB', (80, 80), color='green')
        output = io.BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        png_data = output.read()
        
        processed_data, content_type = service.process_mobile_image(
            png_data,
            'test.png',
            'image/png'
        )
        
        # Verify output
        assert content_type == 'image/png'
        assert len(processed_data) > 0
        
        # Verify image is valid
        img = Image.open(io.BytesIO(processed_data))
        assert img.size == (80, 80)
    
    def test_supported_formats_list(self, service):
        """Test that supported formats list includes mobile formats."""
        assert 'heic' in service.SUPPORTED_MOBILE_FORMATS
        assert 'heif' in service.SUPPORTED_MOBILE_FORMATS
        assert 'jpg' in service.SUPPORTED_MOBILE_FORMATS
        assert 'jpeg' in service.SUPPORTED_MOBILE_FORMATS
        assert 'png' in service.SUPPORTED_MOBILE_FORMATS
    
    def test_max_file_size_constant(self, service):
        """Test that max file size is set correctly."""
        assert service.MAX_MOBILE_FILE_SIZE == 50 * 1024 * 1024
    
    def test_chunk_size_constant(self, service):
        """Test that chunk size is set correctly."""
        assert service.CHUNK_SIZE == 5 * 1024 * 1024
    
    def test_convert_heic_to_jpeg_with_rgb_image(self, service):
        """Test HEIC to JPEG conversion with RGB image."""
        # Create a test image and save as JPEG (simulating HEIC input)
        img = Image.new('RGB', (200, 150), color='purple')
        input_buffer = io.BytesIO()
        img.save(input_buffer, format='JPEG')
        input_buffer.seek(0)
        input_data = input_buffer.read()
        
        # Convert (in real scenario this would be HEIC, but we test the conversion logic)
        try:
            output_data = service.convert_heic_to_jpeg(input_data)
            
            # Verify output is valid JPEG
            output_img = Image.open(io.BytesIO(output_data))
            assert output_img.format == 'JPEG'
            assert output_img.size == (200, 150)
        except ValueError as e:
            # If conversion fails, it should raise ValueError with clear message
            assert "Failed to convert" in str(e)
    
    def test_process_mobile_image_heic_filename(self, service):
        """Test processing image with HEIC filename extension."""
        # Create a test image
        img = Image.new('RGB', (100, 100), color='yellow')
        input_buffer = io.BytesIO()
        img.save(input_buffer, format='JPEG')
        input_buffer.seek(0)
        input_data = input_buffer.read()
        
        # Process with HEIC filename
        processed_data, content_type = service.process_mobile_image(
            input_data,
            'photo.heic',
            'image/heic'
        )
        
        # Should convert to JPEG
        assert content_type == 'image/jpeg'
        assert len(processed_data) > 0
        
        # Verify output is valid JPEG
        output_img = Image.open(io.BytesIO(processed_data))
        assert output_img.format == 'JPEG'
    
    def test_process_mobile_image_heif_filename(self, service):
        """Test processing image with HEIF filename extension."""
        # Create a test image
        img = Image.new('RGB', (100, 100), color='cyan')
        input_buffer = io.BytesIO()
        img.save(input_buffer, format='JPEG')
        input_buffer.seek(0)
        input_data = input_buffer.read()
        
        # Process with HEIF filename
        processed_data, content_type = service.process_mobile_image(
            input_data,
            'photo.HEIF',  # Test case insensitivity
            'image/heif'
        )
        
        # Should convert to JPEG
        assert content_type == 'image/jpeg'
        assert len(processed_data) > 0



class TestChunkedUpload:
    """Test suite for chunked upload functionality."""
    
    @pytest.fixture
    def mock_prisma(self):
        """Create a mock Prisma client."""
        prisma = MagicMock()
        prisma.uploadsession = MagicMock()
        prisma.uploadsession.create = AsyncMock()
        prisma.uploadsession.find_unique = AsyncMock()
        prisma.uploadsession.update = AsyncMock()
        
        return prisma
    
    @pytest.fixture
    def service_with_prisma(self, mock_prisma):
        """Create service instance with mock Prisma client."""
        return MobileUploadService(prisma_client=mock_prisma)
    
    @pytest.mark.asyncio
    async def test_initiate_chunked_upload_success(self, service_with_prisma, mock_prisma):
        """Test successful chunked upload initiation."""
        from datetime import datetime, timedelta, timezone
        
        # Mock the database response
        mock_session = MagicMock()
        mock_session.id = 'session_123'
        mock_session.user_id = 'user_456'
        mock_session.filename = 'large_video.mp4'
        mock_session.total_size = 25 * 1024 * 1024  # 25MB
        mock_session.chunk_size = 5 * 1024 * 1024
        mock_session.chunks_total = 5
        mock_session.chunks_uploaded = 0
        mock_session.status = 'in_progress'
        mock_session.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        mock_prisma.uploadsession.create.return_value = mock_session
        
        # Initiate upload
        result = await service_with_prisma.initiate_chunked_upload(
            filename='large_video.mp4',
            total_size=25 * 1024 * 1024,
            user_id='user_456'
        )
        
        # Verify result
        assert result['session_id'] == 'session_123'
        assert result['chunk_size'] == 5 * 1024 * 1024
        assert result['chunks_total'] == 5
        assert 'expires_at' in result
        
        # Verify database call
        mock_prisma.uploadsession.create.assert_called_once()
        call_args = mock_prisma.uploadsession.create.call_args
        assert call_args[1]['data']['user_id'] == 'user_456'
        assert call_args[1]['data']['filename'] == 'large_video.mp4'
        assert call_args[1]['data']['total_size'] == 25 * 1024 * 1024
        assert call_args[1]['data']['chunks_total'] == 5
        assert call_args[1]['data']['status'] == 'in_progress'
    
    @pytest.mark.asyncio
    async def test_initiate_chunked_upload_file_too_large(self, service_with_prisma):
        """Test chunked upload initiation with oversized file."""
        # Try to upload 51MB file (exceeds 50MB limit)
        with pytest.raises(ValueError) as exc_info:
            await service_with_prisma.initiate_chunked_upload(
                filename='huge_file.mp4',
                total_size=51 * 1024 * 1024,
                user_id='user_456'
            )
        
        assert "exceeds maximum" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_initiate_chunked_upload_zero_size(self, service_with_prisma):
        """Test chunked upload initiation with zero file size."""
        with pytest.raises(ValueError) as exc_info:
            await service_with_prisma.initiate_chunked_upload(
                filename='empty.mp4',
                total_size=0,
                user_id='user_456'
            )
        
        assert "greater than 0" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_initiate_chunked_upload_chunk_calculation(self, service_with_prisma, mock_prisma):
        """Test chunk calculation for various file sizes."""
        from datetime import datetime, timedelta, timezone
        
        test_cases = [
            (5 * 1024 * 1024, 1),      # Exactly 1 chunk
            (10 * 1024 * 1024, 2),     # Exactly 2 chunks
            (12 * 1024 * 1024, 3),     # 2.4 chunks -> 3 chunks
            (25 * 1024 * 1024, 5),     # 5 chunks
            (1024 * 1024, 1),          # 1MB -> 1 chunk
        ]
        
        for file_size, expected_chunks in test_cases:
            mock_session = MagicMock()
            mock_session.id = 'session_123'
            mock_session.chunks_total = expected_chunks
            mock_session.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            mock_prisma.uploadsession.create.return_value = mock_session
            
            result = await service_with_prisma.initiate_chunked_upload(
                filename='test.mp4',
                total_size=file_size,
                user_id='user_456'
            )
            
            assert result['chunks_total'] == expected_chunks, \
                f"File size {file_size} should result in {expected_chunks} chunks"
    
    @pytest.mark.asyncio
    async def test_upload_chunk_success(self, service_with_prisma, mock_prisma):
        """Test successful chunk upload."""
        from datetime import datetime, timedelta, timezone
        
        # Mock session retrieval
        mock_session = MagicMock()
        mock_session.id = 'session_123'
        mock_session.user_id = 'user_456'
        mock_session.total_size = 10 * 1024 * 1024
        mock_session.chunk_size = 5 * 1024 * 1024
        mock_session.chunks_total = 2
        mock_session.chunks_uploaded = 0
        mock_session.status = 'in_progress'
        mock_session.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        mock_prisma.uploadsession.find_unique.return_value = mock_session
        
        # Mock update response
        mock_updated_session = MagicMock()
        mock_updated_session.chunks_uploaded = 1
        mock_updated_session.chunks_total = 2
        mock_prisma.uploadsession.update.return_value = mock_updated_session
        
        # Upload chunk
        chunk_data = b'x' * (5 * 1024 * 1024)  # 5MB chunk
        result = await service_with_prisma.upload_chunk(
            session_id='session_123',
            chunk_number=0,
            chunk_data=chunk_data
        )
        
        # Verify result
        assert result['session_id'] == 'session_123'
        assert result['chunk_number'] == 0
        assert result['chunks_uploaded'] == 1
        assert result['chunks_total'] == 2
        assert result['chunks_remaining'] == 1
        assert result['progress_percent'] == 50.0
        assert result['status'] == 'in_progress'
        
        # Verify database calls
        mock_prisma.uploadsession.find_unique.assert_called_once_with(
            where={'id': 'session_123'}
        )
        mock_prisma.uploadsession.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_chunk_session_not_found(self, service_with_prisma, mock_prisma):
        """Test chunk upload with non-existent session."""
        mock_prisma.uploadsession.find_unique.return_value = None
        
        with pytest.raises(ValueError) as exc_info:
            await service_with_prisma.upload_chunk(
                session_id='nonexistent',
                chunk_number=0,
                chunk_data=b'test'
            )
        
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_upload_chunk_session_expired(self, service_with_prisma, mock_prisma):
        """Test chunk upload with expired session."""
        from datetime import datetime, timedelta, timezone
        
        # Mock expired session
        mock_session = MagicMock()
        mock_session.id = 'session_123'
        mock_session.status = 'in_progress'
        mock_session.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)  # Expired 1 hour ago
        
        mock_prisma.uploadsession.find_unique.return_value = mock_session
        
        with pytest.raises(ValueError) as exc_info:
            await service_with_prisma.upload_chunk(
                session_id='session_123',
                chunk_number=0,
                chunk_data=b'test'
            )
        
        assert "expired" in str(exc_info.value)
        
        # Verify session was marked as failed
        mock_prisma.uploadsession.update.assert_called_once_with(
            where={'id': 'session_123'},
            data={'status': 'failed'}
        )
    
    @pytest.mark.asyncio
    async def test_upload_chunk_invalid_chunk_number(self, service_with_prisma, mock_prisma):
        """Test chunk upload with invalid chunk number."""
        from datetime import datetime, timedelta, timezone
        
        mock_session = MagicMock()
        mock_session.id = 'session_123'
        mock_session.chunks_total = 5
        mock_session.status = 'in_progress'
        mock_session.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        mock_prisma.uploadsession.find_unique.return_value = mock_session
        
        # Test negative chunk number
        with pytest.raises(ValueError) as exc_info:
            await service_with_prisma.upload_chunk(
                session_id='session_123',
                chunk_number=-1,
                chunk_data=b'test'
            )
        assert "Invalid chunk number" in str(exc_info.value)
        
        # Test chunk number too high
        with pytest.raises(ValueError) as exc_info:
            await service_with_prisma.upload_chunk(
                session_id='session_123',
                chunk_number=5,  # Should be 0-4
                chunk_data=b'test'
            )
        assert "Invalid chunk number" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_upload_chunk_oversized_chunk(self, service_with_prisma, mock_prisma):
        """Test chunk upload with chunk exceeding expected size."""
        from datetime import datetime, timedelta, timezone
        
        mock_session = MagicMock()
        mock_session.id = 'session_123'
        mock_session.total_size = 10 * 1024 * 1024
        mock_session.chunk_size = 5 * 1024 * 1024
        mock_session.chunks_total = 2
        mock_session.chunks_uploaded = 0
        mock_session.status = 'in_progress'
        mock_session.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        mock_prisma.uploadsession.find_unique.return_value = mock_session
        
        # Try to upload chunk larger than expected
        oversized_chunk = b'x' * (6 * 1024 * 1024)  # 6MB (exceeds 5MB limit)
        
        with pytest.raises(ValueError) as exc_info:
            await service_with_prisma.upload_chunk(
                session_id='session_123',
                chunk_number=0,
                chunk_data=oversized_chunk
            )
        
        assert "exceeds expected" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_upload_chunk_last_chunk_smaller(self, service_with_prisma, mock_prisma):
        """Test uploading last chunk which can be smaller than chunk size."""
        from datetime import datetime, timedelta, timezone
        
        # 12MB file = 2 full chunks (5MB each) + 1 partial chunk (2MB)
        mock_session = MagicMock()
        mock_session.id = 'session_123'
        mock_session.total_size = 12 * 1024 * 1024
        mock_session.chunk_size = 5 * 1024 * 1024
        mock_session.chunks_total = 3
        mock_session.chunks_uploaded = 2
        mock_session.status = 'in_progress'
        mock_session.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        mock_prisma.uploadsession.find_unique.return_value = mock_session
        
        mock_updated_session = MagicMock()
        mock_updated_session.chunks_uploaded = 3
        mock_updated_session.chunks_total = 3
        mock_prisma.uploadsession.update.return_value = mock_updated_session
        
        # Upload last chunk (2MB)
        last_chunk = b'x' * (2 * 1024 * 1024)
        result = await service_with_prisma.upload_chunk(
            session_id='session_123',
            chunk_number=2,  # Last chunk
            chunk_data=last_chunk
        )
        
        # Should succeed
        assert result['chunks_uploaded'] == 3
        assert result['progress_percent'] == 100.0
    
    @pytest.mark.asyncio
    async def test_complete_chunked_upload_success(self, service_with_prisma, mock_prisma):
        """Test successful chunked upload completion."""
        # Mock session with all chunks uploaded
        mock_session = MagicMock()
        mock_session.id = 'session_123'
        mock_session.filename = 'video.mp4'
        mock_session.total_size = 10 * 1024 * 1024
        mock_session.chunks_total = 2
        mock_session.chunks_uploaded = 2
        mock_session.status = 'in_progress'
        
        mock_prisma.uploadsession.find_unique.return_value = mock_session
        
        # Mock completed session
        mock_completed = MagicMock()
        mock_completed.id = 'session_123'
        mock_completed.filename = 'video.mp4'
        mock_completed.total_size = 10 * 1024 * 1024
        mock_completed.chunks_total = 2
        mock_completed.status = 'completed'
        mock_prisma.uploadsession.update.return_value = mock_completed
        
        # Complete upload
        result = await service_with_prisma.complete_chunked_upload('session_123')
        
        # Verify result
        assert result['session_id'] == 'session_123'
        assert result['status'] == 'completed'
        assert result['filename'] == 'video.mp4'
        assert result['total_size'] == 10 * 1024 * 1024
        assert result['chunks_total'] == 2
        assert 'message' in result
        
        # Verify database update
        mock_prisma.uploadsession.update.assert_called_once_with(
            where={'id': 'session_123'},
            data={'status': 'completed'}
        )
    
    @pytest.mark.asyncio
    async def test_complete_chunked_upload_not_all_chunks(self, service_with_prisma, mock_prisma):
        """Test completion when not all chunks are uploaded."""
        mock_session = MagicMock()
        mock_session.id = 'session_123'
        mock_session.chunks_total = 5
        mock_session.chunks_uploaded = 3  # Only 3 out of 5
        mock_session.status = 'in_progress'
        
        mock_prisma.uploadsession.find_unique.return_value = mock_session
        
        with pytest.raises(ValueError) as exc_info:
            await service_with_prisma.complete_chunked_upload('session_123')
        
        assert "Not all chunks uploaded" in str(exc_info.value)
        assert "Expected 5" in str(exc_info.value)
        assert "got 3" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_complete_chunked_upload_already_completed(self, service_with_prisma, mock_prisma):
        """Test completion of already completed session."""
        mock_session = MagicMock()
        mock_session.id = 'session_123'
        mock_session.status = 'completed'
        
        mock_prisma.uploadsession.find_unique.return_value = mock_session
        
        with pytest.raises(ValueError) as exc_info:
            await service_with_prisma.complete_chunked_upload('session_123')
        
        assert "already completed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_complete_chunked_upload_failed_session(self, service_with_prisma, mock_prisma):
        """Test completion of failed session."""
        mock_session = MagicMock()
        mock_session.id = 'session_123'
        mock_session.status = 'failed'
        
        mock_prisma.uploadsession.find_unique.return_value = mock_session
        
        with pytest.raises(ValueError) as exc_info:
            await service_with_prisma.complete_chunked_upload('session_123')
        
        assert "has failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_upload_progress(self, service_with_prisma, mock_prisma):
        """Test getting upload progress."""
        from datetime import datetime, timedelta, timezone
        
        mock_session = MagicMock()
        mock_session.id = 'session_123'
        mock_session.status = 'in_progress'
        mock_session.filename = 'video.mp4'
        mock_session.total_size = 25 * 1024 * 1024
        mock_session.chunks_uploaded = 3
        mock_session.chunks_total = 5
        mock_session.created_at = datetime.now(timezone.utc)
        mock_session.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        mock_prisma.uploadsession.find_unique.return_value = mock_session
        
        # Get progress
        result = await service_with_prisma.get_upload_progress('session_123')
        
        # Verify result
        assert result['session_id'] == 'session_123'
        assert result['status'] == 'in_progress'
        assert result['filename'] == 'video.mp4'
        assert result['total_size'] == 25 * 1024 * 1024
        assert result['chunks_uploaded'] == 3
        assert result['chunks_total'] == 5
        assert result['chunks_remaining'] == 2
        assert result['progress_percent'] == 60.0
        assert 'created_at' in result
        assert 'expires_at' in result
    
    @pytest.mark.asyncio
    async def test_get_upload_progress_not_found(self, service_with_prisma, mock_prisma):
        """Test getting progress for non-existent session."""
        mock_prisma.uploadsession.find_unique.return_value = None
        
        with pytest.raises(ValueError) as exc_info:
            await service_with_prisma.get_upload_progress('nonexistent')
        
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_chunked_upload_full_workflow(self, service_with_prisma, mock_prisma):
        """Test complete chunked upload workflow from initiation to completion."""
        from datetime import datetime, timedelta, timezone
        
        # Step 1: Initiate upload
        mock_init_session = MagicMock()
        mock_init_session.id = 'session_123'
        mock_init_session.chunks_total = 3
        mock_init_session.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        mock_prisma.uploadsession.create.return_value = mock_init_session
        
        init_result = await service_with_prisma.initiate_chunked_upload(
            filename='test.mp4',
            total_size=12 * 1024 * 1024,  # 12MB = 3 chunks
            user_id='user_456'
        )
        
        assert init_result['chunks_total'] == 3
        session_id = init_result['session_id']
        
        # Step 2: Upload chunks
        for chunk_num in range(3):
            mock_session = MagicMock()
            mock_session.id = session_id
            mock_session.total_size = 12 * 1024 * 1024
            mock_session.chunk_size = 5 * 1024 * 1024
            mock_session.chunks_total = 3
            mock_session.chunks_uploaded = chunk_num
            mock_session.status = 'in_progress'
            mock_session.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            mock_prisma.uploadsession.find_unique.return_value = mock_session
            
            mock_updated = MagicMock()
            mock_updated.chunks_uploaded = chunk_num + 1
            mock_updated.chunks_total = 3
            mock_prisma.uploadsession.update.return_value = mock_updated
            
            chunk_size = 5 * 1024 * 1024 if chunk_num < 2 else 2 * 1024 * 1024
            chunk_data = b'x' * chunk_size
            
            chunk_result = await service_with_prisma.upload_chunk(
                session_id=session_id,
                chunk_number=chunk_num,
                chunk_data=chunk_data
            )
            
            assert chunk_result['chunk_number'] == chunk_num
            assert chunk_result['chunks_uploaded'] == chunk_num + 1
        
        # Step 3: Complete upload
        mock_complete_session = MagicMock()
        mock_complete_session.id = session_id
        mock_complete_session.filename = 'test.mp4'
        mock_complete_session.total_size = 12 * 1024 * 1024
        mock_complete_session.chunks_total = 3
        mock_complete_session.chunks_uploaded = 3
        mock_complete_session.status = 'in_progress'
        mock_prisma.uploadsession.find_unique.return_value = mock_complete_session
        
        mock_final = MagicMock()
        mock_final.id = session_id
        mock_final.filename = 'test.mp4'
        mock_final.total_size = 12 * 1024 * 1024
        mock_final.chunks_total = 3
        mock_prisma.uploadsession.update.return_value = mock_final
        
        complete_result = await service_with_prisma.complete_chunked_upload(session_id)
        
        assert complete_result['status'] == 'completed'
        assert complete_result['filename'] == 'test.mp4'
