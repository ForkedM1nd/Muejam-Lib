"""Personalization engine for For You feed."""
from datetime import datetime
from prisma import Prisma
from typing import List, Dict
import math


class PersonalizationEngine:
    """
    Personalization engine for generating For You feed recommendations.
    
    Requirements:
        - 2.4: Return personalized story recommendations based on Interest_Score
        - 2.5: Fallback to trending when insufficient user history
        - 10.5: Calculate For_You_Feed ranking using weighted scores
    """
    
    # Weight factors for different signals
    WEIGHTS = {
        'save': 3.0,
        'complete_read': 2.5,
        'partial_read': 1.0,
        'like': 1.5,
        'follow': 4.0,
    }
    
    DAILY_DECAY = 0.98
    
    async def update_interests(self, user_id: str, event: str, story_id: str):
        """
        Update user interest scores based on behavioral signals.
        
        Args:
            user_id: ID of the user
            event: Type of event (save, complete_read, partial_read, like, follow)
            story_id: ID of the story
            
        Requirements:
            - 10.1: Increment Interest_Score when user saves a story
            - 10.2: Increment Interest_Score when user completes reading
            - 10.3: Increment Interest_Score when user likes a whisper
            - 10.4: Increment Interest_Score when user follows an author
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Get story with tags and author
            story = await db.story.find_unique(
                where={'id': story_id},
                include={
                    'tags': {
                        'include': {
                            'tag': True
                        }
                    },
                    'author': True
                }
            )
            
            if not story:
                return
            
            weight = self.WEIGHTS.get(event, 1.0)
            
            # Update tag interests
            for story_tag in story.tags:
                await db.userinterest.upsert(
                    where={
                        'user_id_tag_id': {
                            'user_id': user_id,
                            'tag_id': story_tag.tag.id
                        }
                    },
                    data={
                        'create': {
                            'user_id': user_id,
                            'tag_id': story_tag.tag.id,
                            'score': weight
                        },
                        'update': {
                            'score': {
                                'increment': weight
                            }
                        }
                    }
                )
            
            # Update author interest
            await db.userinterest.upsert(
                where={
                    'user_id_author_id': {
                        'user_id': user_id,
                        'author_id': story.author_id
                    }
                },
                data={
                    'create': {
                        'user_id': user_id,
                        'author_id': story.author_id,
                        'score': weight
                    },
                    'update': {
                        'score': {
                            'increment': weight
                        }
                    }
                }
            )
            
        finally:
            await db.disconnect()
    
    async def calculate_story_score(self, user_id: str, story: Dict) -> float:
        """
        Calculate personalized score for a story.
        
        Args:
            user_id: ID of the user
            story: Story data dictionary
            
        Returns:
            Calculated personalized score
            
        Requirements:
            - 10.5: Weighted combination of Interest_Score, Trending_Score, freshness
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Get user interests
            interests = await db.userinterest.find_many(
                where={'user_id': user_id}
            )
            
            interest_map = {}
            for i in interests:
                if i.tag_id:
                    interest_map[f"tag_{i.tag_id}"] = i.score
                if i.author_id:
                    interest_map[f"author_{i.author_id}"] = i.score
            
            # Calculate interest score
            interest_score = 0.0
            
            # Tag affinity
            for tag in story.get('tags', []):
                tag_id = tag.get('tag_id') or tag.get('id')
                interest_score += interest_map.get(f"tag_{tag_id}", 0)
            
            # Author affinity
            author_score = interest_map.get(f"author_{story['author_id']}", 0)
            interest_score += author_score
            
            # Get trending score
            trending_score = story.get('trending_score', 0)
            
            # Freshness score (days since publication)
            if story.get('published_at'):
                days_old = (datetime.now() - story['published_at']).days
                freshness_score = math.exp(-0.1 * days_old)
            else:
                freshness_score = 0
            
            # Combined score with weights
            final_score = (
                0.5 * interest_score +
                0.3 * trending_score +
                0.2 * freshness_score
            )
            
            return final_score
            
        finally:
            await db.disconnect()
    
    async def get_for_you_feed(
        self,
        user_id: str,
        blocked_user_ids: List[str],
        limit: int = 20
    ) -> List[Dict]:
        """
        Generate personalized For You feed.
        
        Args:
            user_id: ID of the user
            blocked_user_ids: List of blocked user IDs to exclude
            limit: Number of stories to return
            
        Returns:
            List of story dictionaries with scores
            
        Requirements:
            - 2.4: Return personalized recommendations
            - 2.5: Cold start fallback to trending
            - 10.7: Exclude blocked authors and soft-deleted content
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Check if user has sufficient interaction history
            interest_count = await db.userinterest.count(
                where={'user_id': user_id}
            )
            
            # Cold start: return empty to signal fallback needed
            if interest_count < 3:
                return None
            
            # Get candidate stories (published, not deleted, not blocked)
            today = datetime.now().date()
            
            stories = await db.story.find_many(
                where={
                    'published': True,
                    'deleted_at': None,
                    'author_id': {
                        'not_in': blocked_user_ids
                    } if blocked_user_ids else {}
                },
                include={
                    'tags': {
                        'include': {
                            'tag': True
                        }
                    },
                    'author': True,
                    'stats': {
                        'where': {
                            'date': today
                        },
                        'take': 1
                    }
                },
                take=100  # Get larger candidate set for scoring
            )
            
            # Score each story
            scored_stories = []
            for story in stories:
                # Convert story to dict format
                story_dict = {
                    'id': story.id,
                    'slug': story.slug,
                    'title': story.title,
                    'blurb': story.blurb,
                    'cover_key': story.cover_key,
                    'author_id': story.author_id,
                    'published': story.published,
                    'published_at': story.published_at,
                    'created_at': story.created_at,
                    'updated_at': story.updated_at,
                    'tags': [{'tag_id': st.tag.id, 'name': st.tag.name} for st in story.tags],
                    'trending_score': story.stats[0].trending_score if story.stats else 0
                }
                
                score = await self.calculate_story_score(user_id, story_dict)
                scored_stories.append((score, story_dict))
            
            # Sort by score descending
            scored_stories.sort(key=lambda x: x[0], reverse=True)
            
            # Return top N stories
            result = [story for score, story in scored_stories[:limit]]
            
            return result
            
        finally:
            await db.disconnect()
