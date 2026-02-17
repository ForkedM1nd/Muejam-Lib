"""Trending score calculation for stories."""
from datetime import datetime, timedelta
from prisma import Prisma


class TrendingCalculator:
    """
    Calculate trending scores for stories based on recent engagement.
    
    Requirements:
        - 2.2: Return stories ordered by Trending_Score within last 24 hours
        - 16.1: Calculate Trending_Score using weighted engagement metrics
        - 16.2: Apply time decay factor of 0.98 per hour
    """
    
    # Weight factors for engagement types
    ENGAGEMENT_WEIGHTS = {
        'save': 3.0,
        'read': 1.0,
        'like': 2.0,
        'whisper': 2.5,
    }
    
    HOURLY_DECAY = 0.98
    
    async def calculate_trending_score(self, story_id: str) -> float:
        """
        Calculate trending score for a story based on 24h engagement.
        
        Args:
            story_id: ID of the story
            
        Returns:
            Calculated trending score
            
        Requirements:
            - 16.1: Weighted combination of saves, reads, likes, whispers
            - 16.2: Apply time decay factor
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Get today's stats
            today = datetime.now().date()
            stats = await db.story_stats_daily.find_unique(
                where={
                    'story_id_date': {
                        'story_id': story_id,
                        'date': today
                    }
                }
            )
            
            if not stats:
                return 0.0
            
            # Calculate weighted engagement
            raw_score = (
                stats.saves_count * self.ENGAGEMENT_WEIGHTS['save'] +
                stats.reads_count * self.ENGAGEMENT_WEIGHTS['read'] +
                stats.likes_count * self.ENGAGEMENT_WEIGHTS['like'] +
                stats.whispers_count * self.ENGAGEMENT_WEIGHTS['whisper']
            )
            
            # Apply time decay (assuming uniform distribution over 24h)
            # Use average of 12 hours elapsed
            hours_elapsed = 12
            decayed_score = raw_score * (self.HOURLY_DECAY ** hours_elapsed)
            
            return decayed_score
            
        finally:
            await db.disconnect()
    
    async def update_all_trending_scores(self):
        """
        Background task to recompute all trending scores.
        
        Requirements:
            - 16.3: Recompute trending scores as background job
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Get all published, non-deleted stories
            stories = await db.story.find_many(
                where={
                    'published': True,
                    'deleted_at': None
                }
            )
            
            today = datetime.now().date()
            
            for story in stories:
                score = await self.calculate_trending_score(story.id)
                
                # Update or create today's stats
                await db.story_stats_daily.upsert(
                    where={
                        'story_id_date': {
                            'story_id': story.id,
                            'date': today
                        }
                    },
                    data={
                        'create': {
                            'story_id': story.id,
                            'date': today,
                            'trending_score': score
                        },
                        'update': {
                            'trending_score': score
                        }
                    }
                )
                
        finally:
            await db.disconnect()
