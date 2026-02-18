"""Service for enhanced profile features including statistics and badges."""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from prisma import Prisma
from prisma.models import UserProfile, UserBadge


class ProfileService:
    """Service for managing enhanced profile features."""
    
    @staticmethod
    async def get_user_statistics(user_id: str) -> Dict:
        """
        Get user statistics for profile display.
        
        Requirements:
            - 24.4: Display user statistics
        
        Returns:
            Dictionary with:
            - total_stories: Total published stories
            - total_chapters: Total published chapters
            - total_whispers: Total whispers posted
            - total_likes_received: Total likes on all content
            - follower_count: Number of followers
            - following_count: Number of users following
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Get profile with counts
            profile = await db.userprofile.find_unique(
                where={'id': user_id},
                include={
                    'stories': {'where': {'published': True, 'deleted_at': None}},
                    'whispers': True,
                    'followers': True,
                    'following': True,
                }
            )
            
            if not profile:
                await db.disconnect()
                return {}
            
            # Count chapters across all published stories
            total_chapters = 0
            for story in profile.stories:
                chapters = await db.chapter.count(
                    where={
                        'story_id': story.id,
                        'published': True,
                        'deleted_at': None
                    }
                )
                total_chapters += chapters
            
            # Count total likes received (stories + whispers)
            # Note: Assuming Like model exists with story_id and whisper_id fields
            story_likes = 0
            for story in profile.stories:
                likes = await db.like.count(where={'story_id': story.id})
                story_likes += likes
            
            whisper_likes = await db.whisperlike.count(
                where={'whisper_id': {'in': [w.id for w in profile.whispers]}}
            )
            
            stats = {
                'total_stories': len(profile.stories),
                'total_chapters': total_chapters,
                'total_whispers': len(profile.whispers),
                'total_likes_received': story_likes + whisper_likes,
                'follower_count': len(profile.followers),
                'following_count': len(profile.following),
            }
            
            await db.disconnect()
            return stats
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def get_pinned_stories(user_id: str) -> List[Dict]:
        """
        Get pinned stories for a user profile.
        
        Requirements:
            - 24.5: Display pinned stories
        
        Returns:
            List of story objects for pinned stories (up to 3)
        """
        db = Prisma()
        await db.connect()
        
        try:
            profile = await db.userprofile.find_unique(
                where={'id': user_id}
            )
            
            if not profile:
                await db.disconnect()
                return []
            
            pinned_ids = []
            if profile.pinned_story_1:
                pinned_ids.append(profile.pinned_story_1)
            if profile.pinned_story_2:
                pinned_ids.append(profile.pinned_story_2)
            if profile.pinned_story_3:
                pinned_ids.append(profile.pinned_story_3)
            
            if not pinned_ids:
                await db.disconnect()
                return []
            
            # Fetch pinned stories
            stories = await db.story.find_many(
                where={
                    'id': {'in': pinned_ids},
                    'published': True,
                    'deleted_at': None
                }
            )
            
            # Sort stories by pinned order
            sorted_stories = []
            for story_id in pinned_ids:
                story = next((s for s in stories if s.id == story_id), None)
                if story:
                    sorted_stories.append(story)
            
            await db.disconnect()
            return sorted_stories
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def get_user_badges(user_id: str) -> List[UserBadge]:
        """
        Get all badges earned by a user.
        
        Requirements:
            - 24.6: Display user badges
        
        Returns:
            List of UserBadge objects
        """
        db = Prisma()
        await db.connect()
        
        try:
            badges = await db.userbadge.find_many(
                where={'user_id': user_id},
                order={'earned_at': 'desc'}
            )
            
            await db.disconnect()
            return badges
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def award_badge(user_id: str, badge_type: str, metadata: Optional[Dict] = None) -> UserBadge:
        """
        Award a badge to a user.
        
        Requirements:
            - 24.6: Badge system for achievements
        
        Args:
            user_id: User to award badge to
            badge_type: Type of badge (VERIFIED_AUTHOR, TOP_CONTRIBUTOR, etc.)
            metadata: Optional metadata about the badge
        
        Returns:
            Created UserBadge object
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Check if user already has this badge
            existing = await db.userbadge.find_first(
                where={
                    'user_id': user_id,
                    'badge_type': badge_type
                }
            )
            
            if existing:
                await db.disconnect()
                return existing
            
            # Create new badge
            badge = await db.userbadge.create(
                data={
                    'user_id': user_id,
                    'badge_type': badge_type,
                    'metadata': metadata or {}
                }
            )
            
            await db.disconnect()
            return badge
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def check_and_award_badges(user_id: str):
        """
        Check user achievements and award appropriate badges.
        
        This should be called periodically or after significant user actions.
        
        Requirements:
            - 24.6: Automatic badge awarding based on achievements
        """
        db = Prisma()
        await db.connect()
        
        try:
            profile = await db.userprofile.find_unique(
                where={'id': user_id},
                include={
                    'stories': {'where': {'published': True, 'deleted_at': None}},
                    'followers': True,
                }
            )
            
            if not profile:
                await db.disconnect()
                return
            
            # Early Adopter: Joined in first month (example logic)
            if profile.created_at < datetime(2024, 2, 1):
                await ProfileService.award_badge(user_id, 'EARLY_ADOPTER')
            
            # Prolific Writer: 10+ published stories
            if len(profile.stories) >= 10:
                await ProfileService.award_badge(user_id, 'PROLIFIC_WRITER')
            
            # Popular Author: 100+ followers
            if len(profile.followers) >= 100:
                await ProfileService.award_badge(user_id, 'POPULAR_AUTHOR')
            
            # Top Contributor: 50+ stories or 500+ whispers
            whisper_count = await db.whisper.count(where={'author_id': user_id})
            if len(profile.stories) >= 50 or whisper_count >= 500:
                await ProfileService.award_badge(user_id, 'TOP_CONTRIBUTOR')
            
            await db.disconnect()
            
        except Exception as e:
            await db.disconnect()
            raise e
