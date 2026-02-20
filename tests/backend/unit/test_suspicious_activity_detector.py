"""
Unit tests for SuspiciousActivityDetector service.

Tests cover:
- Multiple accounts from same IP detection
- Rapid content creation detection
- Duplicate content detection
- Bot-like behavior detection
- Activity summary generation

Requirements: 5.10, 5.11
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../apps/backend'))

from apps.security.suspicious_activity_detector import SuspiciousActivityDetector


class TestSuspiciousActivityDetector:
    """Test suite for SuspiciousActivityDetector service."""
    
    @pytest.fixture
    def detector(self):
        """Create a SuspiciousActivityDetector instance."""
        return SuspiciousActivityDetector(
            max_accounts_per_ip=3,
            max_content_per_hour=20,
            content_similarity_threshold=0.9
        )
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock Prisma database client."""
        db = MagicMock()
        db.connect = AsyncMock()
        db.disconnect = AsyncMock()
        return db
    
    @pytest.mark.asyncio
    async def test_no_suspicious_activity(self, detector, mock_db):
        """Test that normal user activity returns no flags."""
        with patch('apps.security.suspicious_activity_detector.Prisma', return_value=mock_db):
            # Mock normal activity
            mock_db.userconsent.find_many = AsyncMock(return_value=[
                MagicMock(user_id='user1'),
                MagicMock(user_id='user2')
            ])
            mock_db.story.count = AsyncMock(return_value=2)
            mock_db.chapter.count = AsyncMock(return_value=3)
            mock_db.whisper.count = AsyncMock(return_value=5)
            mock_db.whisper.find_many = AsyncMock(return_value=[])
            mock_db.userprofile.find_unique = AsyncMock(return_value=MagicMock(
                created_at=datetime.now(timezone.utc) - timedelta(days=30)
            ))
            mock_db.whisper.find_first = AsyncMock(return_value=None)
            
            flags = await detector.check_user_activity('user1', '192.168.1.1')
            
            assert flags == []
    
    @pytest.mark.asyncio
    async def test_multiple_accounts_same_ip(self, detector, mock_db):
        """Test detection of multiple accounts from same IP."""
        with patch('apps.security.suspicious_activity_detector.Prisma', return_value=mock_db):
            # Mock 5 accounts from same IP (exceeds limit of 3)
            mock_db.userconsent.find_many = AsyncMock(return_value=[
                MagicMock(user_id='user1'),
                MagicMock(user_id='user2'),
                MagicMock(user_id='user3'),
                MagicMock(user_id='user4'),
                MagicMock(user_id='user5')
            ])
            mock_db.story.count = AsyncMock(return_value=0)
            mock_db.chapter.count = AsyncMock(return_value=0)
            mock_db.whisper.count = AsyncMock(return_value=0)
            mock_db.whisper.find_many = AsyncMock(return_value=[])
            mock_db.userprofile.find_unique = AsyncMock(return_value=MagicMock(
                created_at=datetime.now(timezone.utc) - timedelta(days=30)
            ))
            mock_db.whisper.find_first = AsyncMock(return_value=None)
            
            flags = await detector.check_user_activity('user1', '192.168.1.1')
            
            assert 'multiple_accounts_same_ip' in flags
    
    @pytest.mark.asyncio
    async def test_rapid_content_creation(self, detector, mock_db):
        """Test detection of rapid content creation."""
        with patch('apps.security.suspicious_activity_detector.Prisma', return_value=mock_db):
            # Mock 25 content items in last hour (exceeds limit of 20)
            mock_db.userconsent.find_many = AsyncMock(return_value=[
                MagicMock(user_id='user1')
            ])
            mock_db.story.count = AsyncMock(return_value=10)
            mock_db.chapter.count = AsyncMock(return_value=10)
            mock_db.whisper.count = AsyncMock(return_value=5)
            mock_db.whisper.find_many = AsyncMock(return_value=[])
            mock_db.userprofile.find_unique = AsyncMock(return_value=MagicMock(
                created_at=datetime.now(timezone.utc) - timedelta(days=30)
            ))
            mock_db.whisper.find_first = AsyncMock(return_value=None)
            
            flags = await detector.check_user_activity('user1', '192.168.1.1')
            
            assert 'rapid_content_creation' in flags
    
    @pytest.mark.asyncio
    async def test_duplicate_content_detection(self, detector, mock_db):
        """Test detection of duplicate content across accounts."""
        with patch('apps.security.suspicious_activity_detector.Prisma', return_value=mock_db):
            # Mock user whispers
            user_whispers = [
                MagicMock(content='This is duplicate content', user_id='user1')
            ]
            
            # Mock other user's whispers with same content
            other_whispers = [
                MagicMock(content='This is duplicate content', user_id='user2')
            ]
            
            # Mock for bot behavior check (empty list)
            bot_check_whispers = []
            
            mock_db.userconsent.find_many = AsyncMock(return_value=[
                MagicMock(user_id='user1')
            ])
            mock_db.story.count = AsyncMock(return_value=0)
            mock_db.chapter.count = AsyncMock(return_value=0)
            mock_db.whisper.count = AsyncMock(return_value=0)
            mock_db.whisper.find_many = AsyncMock(side_effect=[
                user_whispers,  # First call for user's whispers (duplicate check)
                other_whispers,  # Second call for other users' whispers (duplicate check)
                bot_check_whispers  # Third call for bot behavior check
            ])
            mock_db.userprofile.find_unique = AsyncMock(return_value=MagicMock(
                created_at=datetime.now(timezone.utc) - timedelta(days=30)
            ))
            mock_db.whisper.find_first = AsyncMock(return_value=None)
            
            flags = await detector.check_user_activity('user1', '192.168.1.1')
            
            assert 'duplicate_content' in flags
    
    @pytest.mark.asyncio
    async def test_bot_behavior_quick_first_post(self, detector, mock_db):
        """Test detection of bot behavior - quick first post after account creation."""
        with patch('apps.security.suspicious_activity_detector.Prisma', return_value=mock_db):
            account_created = datetime.now(timezone.utc) - timedelta(days=1)
            first_post = account_created + timedelta(seconds=30)  # 30 seconds after creation
            
            mock_db.userconsent.find_many = AsyncMock(return_value=[
                MagicMock(user_id='user1')
            ])
            mock_db.story.count = AsyncMock(return_value=0)
            mock_db.chapter.count = AsyncMock(return_value=0)
            mock_db.whisper.count = AsyncMock(return_value=0)
            mock_db.whisper.find_many = AsyncMock(return_value=[])
            mock_db.userprofile.find_unique = AsyncMock(return_value=MagicMock(
                created_at=account_created
            ))
            mock_db.whisper.find_first = AsyncMock(return_value=MagicMock(
                created_at=first_post
            ))
            
            flags = await detector.check_user_activity('user1', '192.168.1.1')
            
            assert 'bot_behavior' in flags
    
    @pytest.mark.asyncio
    async def test_bot_behavior_regular_intervals(self, detector, mock_db):
        """Test detection of bot behavior - too regular posting intervals."""
        with patch('apps.security.suspicious_activity_detector.Prisma', return_value=mock_db):
            # Create whispers with exactly 60 second intervals (too regular)
            base_time = datetime.now(timezone.utc)
            regular_whispers = [
                MagicMock(
                    content=f'Post {i}',
                    created_at=base_time - timedelta(seconds=60 * i)
                )
                for i in range(15)
            ]
            
            mock_db.userconsent.find_many = AsyncMock(return_value=[
                MagicMock(user_id='user1')
            ])
            mock_db.story.count = AsyncMock(return_value=0)
            mock_db.chapter.count = AsyncMock(return_value=0)
            mock_db.whisper.count = AsyncMock(return_value=0)
            mock_db.whisper.find_many = AsyncMock(return_value=regular_whispers)
            mock_db.userprofile.find_unique = AsyncMock(return_value=MagicMock(
                created_at=datetime.now(timezone.utc) - timedelta(days=30)
            ))
            mock_db.whisper.find_first = AsyncMock(return_value=None)
            
            flags = await detector.check_user_activity('user1', '192.168.1.1')
            
            assert 'bot_behavior' in flags
    
    @pytest.mark.asyncio
    async def test_bot_behavior_duplicate_content(self, detector, mock_db):
        """Test detection of bot behavior - high ratio of duplicate content."""
        with patch('apps.security.suspicious_activity_detector.Prisma', return_value=mock_db):
            # Create whispers where 80% are identical
            duplicate_whispers = [
                MagicMock(
                    content='Same message' if i < 8 else f'Different {i}',
                    created_at=datetime.now(timezone.utc) - timedelta(minutes=i)
                )
                for i in range(10)
            ]
            
            mock_db.userconsent.find_many = AsyncMock(return_value=[
                MagicMock(user_id='user1')
            ])
            mock_db.story.count = AsyncMock(return_value=0)
            mock_db.chapter.count = AsyncMock(return_value=0)
            mock_db.whisper.count = AsyncMock(return_value=0)
            mock_db.whisper.find_many = AsyncMock(return_value=duplicate_whispers)
            mock_db.userprofile.find_unique = AsyncMock(return_value=MagicMock(
                created_at=datetime.now(timezone.utc) - timedelta(days=30)
            ))
            mock_db.whisper.find_first = AsyncMock(return_value=None)
            
            flags = await detector.check_user_activity('user1', '192.168.1.1')
            
            assert 'bot_behavior' in flags
    
    @pytest.mark.asyncio
    async def test_multiple_flags(self, detector, mock_db):
        """Test that multiple suspicious patterns can be detected simultaneously."""
        with patch('apps.security.suspicious_activity_detector.Prisma', return_value=mock_db):
            # Mock multiple violations
            mock_db.userconsent.find_many = AsyncMock(return_value=[
                MagicMock(user_id=f'user{i}') for i in range(5)
            ])
            mock_db.story.count = AsyncMock(return_value=10)
            mock_db.chapter.count = AsyncMock(return_value=10)
            mock_db.whisper.count = AsyncMock(return_value=5)
            
            # Bot behavior - quick first post
            account_created = datetime.now(timezone.utc) - timedelta(days=1)
            first_post = account_created + timedelta(seconds=30)
            
            mock_db.whisper.find_many = AsyncMock(return_value=[])
            mock_db.userprofile.find_unique = AsyncMock(return_value=MagicMock(
                created_at=account_created
            ))
            mock_db.whisper.find_first = AsyncMock(return_value=MagicMock(
                created_at=first_post
            ))
            
            flags = await detector.check_user_activity('user1', '192.168.1.1')
            
            # Should detect multiple issues
            assert 'multiple_accounts_same_ip' in flags
            assert 'rapid_content_creation' in flags
            assert 'bot_behavior' in flags
    
    @pytest.mark.asyncio
    async def test_activity_summary(self, detector, mock_db):
        """Test generation of activity summary."""
        with patch('apps.security.suspicious_activity_detector.Prisma', return_value=mock_db):
            account_created = datetime.now(timezone.utc) - timedelta(days=10)
            
            mock_db.userprofile.find_unique = AsyncMock(return_value=MagicMock(
                id='user1',
                created_at=account_created
            ))
            mock_db.story.count = AsyncMock(side_effect=[2, 5, 10])  # hour, day, total
            mock_db.chapter.count = AsyncMock(side_effect=[3, 8, 15])
            mock_db.whisper.count = AsyncMock(side_effect=[5, 12, 25])
            
            summary = await detector.get_activity_summary('user1')
            
            assert summary['user_id'] == 'user1'
            assert summary['account_age_days'] == 10
            assert summary['content_last_hour'] == 10  # 2 + 3 + 5
            assert summary['content_last_day'] == 25  # 5 + 8 + 12
            assert summary['total_content'] == 50  # 10 + 15 + 25
    
    @pytest.mark.asyncio
    async def test_activity_summary_nonexistent_user(self, detector, mock_db):
        """Test activity summary for nonexistent user."""
        with patch('apps.security.suspicious_activity_detector.Prisma', return_value=mock_db):
            mock_db.userprofile.find_unique = AsyncMock(return_value=None)
            
            summary = await detector.get_activity_summary('nonexistent')
            
            assert summary == {}
    
    def test_content_hashing(self, detector):
        """Test content hashing for duplicate detection."""
        # Same content should produce same hash
        content1 = "This is a test message"
        content2 = "This is a test message"
        
        hash1 = detector._hash_content(content1)
        hash2 = detector._hash_content(content2)
        
        assert hash1 == hash2
    
    def test_content_hashing_normalization(self, detector):
        """Test that content hashing normalizes variations."""
        # Different formatting, same content
        content1 = "This is a test message"
        content2 = "THIS IS A TEST MESSAGE"
        content3 = "  this   is  a   test   message  "
        content4 = "This is a test message!!!"
        
        hash1 = detector._hash_content(content1)
        hash2 = detector._hash_content(content2)
        hash3 = detector._hash_content(content3)
        hash4 = detector._hash_content(content4)
        
        # All should produce the same hash after normalization
        assert hash1 == hash2 == hash3 == hash4
    
    def test_content_hashing_different_content(self, detector):
        """Test that different content produces different hashes."""
        content1 = "This is message one"
        content2 = "This is message two"
        
        hash1 = detector._hash_content(content1)
        hash2 = detector._hash_content(content2)
        
        assert hash1 != hash2
    
    @pytest.mark.asyncio
    async def test_no_ip_address_provided(self, detector, mock_db):
        """Test that IP-based checks are skipped when no IP provided."""
        with patch('apps.security.suspicious_activity_detector.Prisma', return_value=mock_db):
            mock_db.story.count = AsyncMock(return_value=0)
            mock_db.chapter.count = AsyncMock(return_value=0)
            mock_db.whisper.count = AsyncMock(return_value=0)
            mock_db.whisper.find_many = AsyncMock(return_value=[])
            mock_db.userprofile.find_unique = AsyncMock(return_value=MagicMock(
                created_at=datetime.now(timezone.utc) - timedelta(days=30)
            ))
            mock_db.whisper.find_first = AsyncMock(return_value=None)
            
            flags = await detector.check_user_activity('user1', ip_address=None)
            
            # Should not include IP-based flag
            assert 'multiple_accounts_same_ip' not in flags
    
    @pytest.mark.asyncio
    async def test_custom_thresholds(self):
        """Test detector with custom thresholds."""
        custom_detector = SuspiciousActivityDetector(
            max_accounts_per_ip=5,
            max_content_per_hour=50,
            content_similarity_threshold=0.95
        )
        
        assert custom_detector.max_accounts_per_ip == 5
        assert custom_detector.max_content_per_hour == 50
        assert custom_detector.content_similarity_threshold == 0.95
