"""Service for content discovery features including trending, recommendations, and filtering."""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from prisma import Prisma
from prisma.models import Story


class DiscoveryService:
    """Service for content discovery and recommendations."""
    
    @staticmethod
    async def get_trending_stories(limit: int = 20, days: int = 7) -> List[Story]:
        """
        Get trending stories based on recent engagement.
        
        Requirements:
            - 25.1, 25.2: Calculate trending score based on engagement and recency
        
        NOTE: Simplified version - returns recently published stories.
        Full trending calculation requires Like and Comment models which are not yet implemented.
        
        Args:
            limit: Maximum number of stories to return
            days: Number of days to consider for trending calculation
        
        Returns:
            List of Story objects sorted by publication date
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get published stories with recent activity
            # Simplified: just return recent stories ordered by publication date
            stories = await db.story.find_many(
                where={
                    'published': True,
                    'deleted_at': None,
                    'published_at': {'gte': cutoff_date}
                },
                include={
                    'author': True,
                    'tags': {'include': {'tag': True}},
                },
                order={'published_at': 'desc'},
                take=limit
            )
            
            await db.disconnect()
            return stories
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def get_stories_by_genre(
        genre: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict] = None
    ) -> tuple[List[Story], int]:
        """
        Get stories by genre with optional filters.
        
        Requirements:
            - 25.3: Genre-based browsing
            - 25.4: Filtering by status, word count, update frequency
        
        Args:
            genre: Genre to filter by
            limit: Maximum number of stories to return
            offset: Offset for pagination
            filters: Optional filters (status, word_count_min, word_count_max, update_frequency)
        
        Returns:
            Tuple of (stories list, total count)
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Build where clause
            where_clause = {
                'published': True,
                'deleted_at': None,
            }
            
            # Add genre filter
            if genre and genre != 'all':
                where_clause['tags'] = {
                    'some': {
                        'tag': {
                            'name': {'equals': genre, 'mode': 'insensitive'}
                        }
                    }
                }
            
            # Add completion status filter
            if filters and 'status' in filters:
                if filters['status'] == 'completed':
                    where_clause['completed'] = True
                elif filters['status'] == 'ongoing':
                    where_clause['completed'] = False
            
            # Add word count filter (requires aggregation, simplified here)
            # Note: This would need a word_count field on Story model
            
            # Get stories
            stories = await db.story.find_many(
                where=where_clause,
                include={
                    'author': True,
                    'tags': {'include': {'tag': True}},
                },
                order={'published_at': 'desc'},
                take=limit,
                skip=offset
            )
            
            # Get total count
            total = await db.story.count(where=where_clause)
            
            await db.disconnect()
            return stories, total
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def get_recommended_stories(user_id: str, limit: int = 10) -> List[Story]:
        """
        Get recommended stories for a user based on reading history and followed authors.
        
        Requirements:
            - 25.5: Recommendations based on reading history and followed authors
        
        Args:
            user_id: User ID to get recommendations for
            limit: Maximum number of stories to return
        
        Returns:
            List of recommended Story objects
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Get user's reading history
            reading_history = await db.readingprogress.find_many(
                where={'user_id': user_id},
                include={'chapter': {'include': {'story': True}}},
                take=50,
                order={'updated_at': 'desc'}
            )
            
            # Get followed authors
            follows = await db.follow.find_many(
                where={'follower_id': user_id},
                include={'following': {'include': {'stories': True}}}
            )
            
            # Collect genres from reading history
            read_genres = set()
            read_story_ids = set()
            for progress in reading_history:
                if progress.chapter and progress.chapter.story:
                    read_story_ids.add(progress.chapter.story.id)
                    # Get story tags/genres
                    story_tags = await db.storytag.find_many(
                        where={'story_id': progress.chapter.story.id},
                        include={'tag': True}
                    )
                    for tag in story_tags:
                        read_genres.add(tag.tag.name)
            
            # Get stories from followed authors (not already read)
            followed_author_stories = []
            for follow in follows:
                for story in follow.following.stories:
                    if story.id not in read_story_ids and story.published and not story.deleted_at:
                        followed_author_stories.append(story)
            
            # Get stories with similar genres (not already read)
            similar_genre_stories = []
            if read_genres:
                for genre in list(read_genres)[:3]:  # Top 3 genres
                    stories = await db.story.find_many(
                        where={
                            'published': True,
                            'deleted_at': None,
                            'id': {'notIn': list(read_story_ids)},
                            'tags': {
                                'some': {
                                    'tag': {
                                        'name': {'equals': genre, 'mode': 'insensitive'}
                                    }
                                }
                            }
                        },
                        include={
                            'author': True,
                            'tags': {'include': {'tag': True}},
                        },
                        take=5
                    )
                    similar_genre_stories.extend(stories)
            
            # Combine and deduplicate recommendations
            recommendations = followed_author_stories + similar_genre_stories
            seen_ids = set()
            unique_recommendations = []
            for story in recommendations:
                if story.id not in seen_ids:
                    seen_ids.add(story.id)
                    unique_recommendations.append(story)
            
            await db.disconnect()
            return unique_recommendations[:limit]
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def get_similar_stories(story_id: str, limit: int = 5) -> List[Story]:
        """
        Get stories similar to a given story based on genre and tags.
        
        Requirements:
            - 25.6: Similar stories based on genre, tags, and reader overlap
        
        Args:
            story_id: Story ID to find similar stories for
            limit: Maximum number of stories to return
        
        Returns:
            List of similar Story objects
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Get the source story with tags
            source_story = await db.story.find_unique(
                where={'id': story_id},
                include={'tags': {'include': {'tag': True}}}
            )
            
            if not source_story:
                await db.disconnect()
                return []
            
            # Get tag names
            tag_names = [tag.tag.name for tag in source_story.tags]
            
            if not tag_names:
                await db.disconnect()
                return []
            
            # Find stories with overlapping tags
            similar_stories = await db.story.find_many(
                where={
                    'published': True,
                    'deleted_at': None,
                    'id': {'not': story_id},
                    'tags': {
                        'some': {
                            'tag': {
                                'name': {'in': tag_names}
                            }
                        }
                    }
                },
                include={
                    'author': True,
                    'tags': {'include': {'tag': True}},
                },
                take=limit * 2  # Get more to score and filter
            )
            
            # Score by tag overlap
            scored_stories = []
            for story in similar_stories:
                story_tag_names = [tag.tag.name for tag in story.tags]
                overlap = len(set(tag_names) & set(story_tag_names))
                scored_stories.append({
                    'story': story,
                    'score': overlap
                })
            
            # Sort by score and return top stories
            scored_stories.sort(key=lambda x: x['score'], reverse=True)
            top_stories = [item['story'] for item in scored_stories[:limit]]
            
            await db.disconnect()
            return top_stories
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def get_new_and_noteworthy(limit: int = 10, days: int = 30) -> List[Story]:
        """
        Get recently published stories with quality signals.
        
        Requirements:
            - 25.7: New and noteworthy featuring recent stories with quality signals
        
        NOTE: Simplified version - returns recently published stories.
        Full quality scoring requires Like and Comment models which are not yet implemented.
        
        Args:
            limit: Maximum number of stories to return
            days: Number of days to consider as "new"
        
        Returns:
            List of Story objects
        """
        db = Prisma()
        await db.connect()
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get recent stories
            stories = await db.story.find_many(
                where={
                    'published': True,
                    'deleted_at': None,
                    'published_at': {'gte': cutoff_date}
                },
                include={
                    'author': {'include': {'followers': True}},
                    'tags': {'include': {'tag': True}},
                },
                order={'published_at': 'desc'},
                take=limit
            )
            
            await db.disconnect()
            return stories
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def get_staff_picks(limit: int = 10) -> List[Story]:
        """
        Get staff-curated stories.
        
        Requirements:
            - 25.10: Staff picks curated by moderators
        
        NOTE: Simplified version - returns recently published stories.
        Full staff picks requires a staff_pick flag or StaffPick model which is not yet implemented.
        
        Args:
            limit: Maximum number of stories to return
        
        Returns:
            List of Story objects
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Return recently published stories as placeholder
            stories = await db.story.find_many(
                where={
                    'published': True,
                    'deleted_at': None,
                },
                include={
                    'author': True,
                    'tags': {'include': {'tag': True}},
                },
                order={'published_at': 'desc'},
                take=limit
            )
            
            await db.disconnect()
            return stories
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def get_rising_authors(limit: int = 10, days: int = 30) -> List[Dict]:
        """
        Get new authors with growing followings.
        
        Requirements:
            - 25.12: Rising authors featuring new authors with growing followings
        
        Args:
            limit: Maximum number of authors to return
            days: Number of days to consider for "new" authors
        
        Returns:
            List of author profiles with growth metrics
        """
        db = Prisma()
        await db.connect()
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get authors who joined recently
            authors = await db.userprofile.find_many(
                where={
                    'created_at': {'gte': cutoff_date},
                },
                include={
                    'stories': {
                        'where': {'published': True, 'deleted_at': None}
                    },
                    'followers': True,
                },
                take=limit * 3
            )
            
            # Score by growth indicators
            scored_authors = []
            for author in authors:
                if len(author.stories) == 0:
                    continue  # Skip authors with no published stories
                
                follower_count = len(author.followers)
                story_count = len(author.stories)
                
                # Calculate growth score
                growth_score = (follower_count * 2) + (story_count * 5)
                
                if growth_score >= 5:  # Minimum threshold
                    scored_authors.append({
                        'author': author,
                        'score': growth_score,
                        'follower_count': follower_count,
                        'story_count': story_count
                    })
            
            # Sort by score
            scored_authors.sort(key=lambda x: x['score'], reverse=True)
            
            await db.disconnect()
            return scored_authors[:limit]
            
        except Exception as e:
            await db.disconnect()
            raise e
