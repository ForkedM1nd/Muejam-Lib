"""Service for author analytics dashboard."""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from prisma import Prisma
from prisma.models import Story, Chapter
import csv
import io
from apps.analytics.mobile_analytics_service import get_mobile_analytics_service


class AnalyticsService:
    """Service for author analytics and metrics."""
    
    @staticmethod
    async def get_story_metrics(story_id: str) -> Dict:
        """
        Get comprehensive metrics for a story.
        
        Requirements:
            - 26.2: Story-level metrics (views, readers, likes, comments, completion rate)
        
        Returns:
            Dictionary with story metrics
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Get story
            story = await db.story.find_unique(
                where={'id': story_id},
                include={'chapters': True}
            )
            
            if not story:
                await db.disconnect()
                return {}
            
            # Get total stats from daily aggregates
            stats = await db.storystats.aggregate(
                where={'story_id': story_id},
                _sum={
                    'saves_count': True,
                    'reads_count': True,
                    'likes_count': True,
                    'whispers_count': True
                }
            )
            
            # Get unique readers (count distinct users with reading progress)
            unique_readers = await db.readingprogress.group_by(
                by=['user_id'],
                where={
                    'chapter': {
                        'story_id': story_id
                    }
                }
            )
            
            # Get likes count
            likes = await db.like.count(where={'story_id': story_id})
            
            # Get comments count
            comments = await db.comment.count(where={'story_id': story_id})
            
            # Calculate completion rate
            total_chapters = len(story.chapters)
            if total_chapters > 0:
                # Count users who read the last chapter
                last_chapter = max(story.chapters, key=lambda c: c.chapter_number)
                completed_readers = await db.readingprogress.count(
                    where={'chapter_id': last_chapter.id}
                )
                completion_rate = (completed_readers / len(unique_readers) * 100) if unique_readers else 0
            else:
                completion_rate = 0
            
            metrics = {
                'story_id': story_id,
                'title': story.title,
                'total_views': stats._sum.reads_count or 0,
                'unique_readers': len(unique_readers),
                'total_likes': likes,
                'total_comments': comments,
                'total_saves': stats._sum.saves_count or 0,
                'completion_rate': round(completion_rate, 2),
                'total_chapters': total_chapters,
                'published_at': story.published_at
            }
            
            await db.disconnect()
            return metrics
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def get_chapter_metrics(story_id: str) -> List[Dict]:
        """
        Get metrics for each chapter in a story.
        
        Requirements:
            - 26.3: Chapter-level metrics showing engagement
        
        Returns:
            List of chapter metrics
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Get all chapters for the story
            chapters = await db.chapter.find_many(
                where={'story_id': story_id, 'deleted_at': None},
                order={'chapter_number': 'asc'}
            )
            
            chapter_metrics = []
            for chapter in chapters:
                # Get reading progress count (views)
                views = await db.readingprogress.count(
                    where={'chapter_id': chapter.id}
                )
                
                # Get unique readers
                unique_readers = await db.readingprogress.group_by(
                    by=['user_id'],
                    where={'chapter_id': chapter.id}
                )
                
                # Get comments
                comments = await db.comment.count(
                    where={'chapter_id': chapter.id}
                )
                
                # Get likes (assuming likes can be on chapters)
                likes = await db.like.count(
                    where={'chapter_id': chapter.id}
                )
                
                chapter_metrics.append({
                    'chapter_id': chapter.id,
                    'chapter_number': chapter.chapter_number,
                    'title': chapter.title,
                    'views': views,
                    'unique_readers': len(unique_readers),
                    'comments': comments,
                    'likes': likes,
                    'published_at': chapter.published_at
                })
            
            await db.disconnect()
            return chapter_metrics
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def get_reader_demographics(story_id: str) -> Dict:
        """
        Get reader demographics for a story.
        
        Requirements:
            - 26.4: Reader demographics (top countries, reading times, device types)
        
        Note: This is a placeholder implementation. Full demographics would require
        additional tracking of user location, device type, and reading times.
        
        Returns:
            Dictionary with demographic data
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Get unique readers
            readers = await db.readingprogress.find_many(
                where={
                    'chapter': {
                        'story_id': story_id
                    }
                },
                include={'user': True},
                distinct=['user_id']
            )
            
            # Placeholder demographics
            # In production, this would aggregate actual tracking data
            demographics = {
                'total_readers': len(readers),
                'top_countries': [
                    {'country': 'United States', 'count': int(len(readers) * 0.4)},
                    {'country': 'United Kingdom', 'count': int(len(readers) * 0.2)},
                    {'country': 'Canada', 'count': int(len(readers) * 0.15)},
                    {'country': 'Australia', 'count': int(len(readers) * 0.1)},
                    {'country': 'Other', 'count': int(len(readers) * 0.15)}
                ],
                'reading_times': {
                    'morning': int(len(readers) * 0.2),
                    'afternoon': int(len(readers) * 0.3),
                    'evening': int(len(readers) * 0.4),
                    'night': int(len(readers) * 0.1)
                },
                'device_types': {
                    'mobile': int(len(readers) * 0.6),
                    'desktop': int(len(readers) * 0.3),
                    'tablet': int(len(readers) * 0.1)
                }
            }
            
            await db.disconnect()
            return demographics
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def get_traffic_sources(story_id: str) -> Dict:
        """
        Get traffic sources for a story.
        
        Requirements:
            - 26.6: Traffic sources (direct, search, recommendations, social shares)
        
        Note: This is a placeholder. Full implementation would require tracking
        referrer data and UTM parameters.
        
        Returns:
            Dictionary with traffic source data
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Get total views
            stats = await db.storystats.aggregate(
                where={'story_id': story_id},
                _sum={'reads_count': True}
            )
            
            total_views = stats._sum.reads_count or 0
            
            # Placeholder traffic sources
            # In production, this would aggregate actual referrer tracking
            sources = {
                'direct': int(total_views * 0.4),
                'search': int(total_views * 0.2),
                'recommendations': int(total_views * 0.25),
                'social': int(total_views * 0.1),
                'other': int(total_views * 0.05)
            }
            
            await db.disconnect()
            return sources
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def get_engagement_trends(story_id: str, days: int = 30) -> List[Dict]:
        """
        Get engagement trends over time.
        
        Requirements:
            - 26.5: Engagement trends over time with interactive charts
        
        Args:
            story_id: Story ID
            days: Number of days to include
        
        Returns:
            List of daily engagement metrics
        """
        db = Prisma()
        await db.connect()
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get daily stats
            daily_stats = await db.storystats.find_many(
                where={
                    'story_id': story_id,
                    'date': {'gte': cutoff_date}
                },
                order={'date': 'asc'}
            )
            
            trends = [
                {
                    'date': stat.date.isoformat(),
                    'views': stat.reads_count,
                    'saves': stat.saves_count,
                    'likes': stat.likes_count,
                    'comments': stat.whispers_count,
                    'trending_score': stat.trending_score
                }
                for stat in daily_stats
            ]
            
            await db.disconnect()
            return trends
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def get_reader_retention(story_id: str) -> Dict:
        """
        Get reader retention metrics.
        
        Requirements:
            - 26.7: Reader retention (percentage continuing to next chapter)
        
        Returns:
            Dictionary with retention metrics per chapter
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Get chapters in order
            chapters = await db.chapter.find_many(
                where={'story_id': story_id, 'deleted_at': None},
                order={'chapter_number': 'asc'}
            )
            
            retention_data = []
            for i, chapter in enumerate(chapters):
                # Count readers of this chapter
                current_readers = await db.readingprogress.count(
                    where={'chapter_id': chapter.id}
                )
                
                # Count readers who continued to next chapter
                if i < len(chapters) - 1:
                    next_chapter = chapters[i + 1]
                    next_readers = await db.readingprogress.count(
                        where={'chapter_id': next_chapter.id}
                    )
                    retention_rate = (next_readers / current_readers * 100) if current_readers > 0 else 0
                else:
                    retention_rate = None  # Last chapter has no next
                
                retention_data.append({
                    'chapter_number': chapter.chapter_number,
                    'chapter_title': chapter.title,
                    'readers': current_readers,
                    'retention_rate': round(retention_rate, 2) if retention_rate is not None else None
                })
            
            await db.disconnect()
            return {'chapters': retention_data}
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def get_follower_growth(author_id: str, days: int = 90) -> List[Dict]:
        """
        Get follower growth over time.
        
        Requirements:
            - 26.8: Follower growth over time
        
        Args:
            author_id: Author user ID
            days: Number of days to include
        
        Returns:
            List of daily follower counts
        """
        db = Prisma()
        await db.connect()
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get all follows for this author
            follows = await db.follow.find_many(
                where={
                    'following_id': author_id,
                    'created_at': {'gte': cutoff_date}
                },
                order={'created_at': 'asc'}
            )
            
            # Aggregate by date
            daily_growth = {}
            for follow in follows:
                date_key = follow.created_at.date().isoformat()
                daily_growth[date_key] = daily_growth.get(date_key, 0) + 1
            
            # Create cumulative growth data
            growth_data = []
            cumulative = 0
            current_date = cutoff_date.date()
            end_date = datetime.utcnow().date()
            
            while current_date <= end_date:
                date_key = current_date.isoformat()
                daily_new = daily_growth.get(date_key, 0)
                cumulative += daily_new
                
                growth_data.append({
                    'date': date_key,
                    'new_followers': daily_new,
                    'total_followers': cumulative
                })
                
                current_date += timedelta(days=1)
            
            await db.disconnect()
            return growth_data
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def get_author_dashboard(author_id: str) -> Dict:
        """
        Get comprehensive analytics dashboard for an author.
        
        Requirements:
            - 26.1: Analytics dashboard accessible to users with published content
            - 26.9: Most popular stories and chapters by engagement
        
        Returns:
            Dictionary with dashboard data
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Get author's published stories
            stories = await db.story.find_many(
                where={
                    'author_id': author_id,
                    'published': True,
                    'deleted_at': None
                }
            )
            
            # Get metrics for each story
            story_metrics = []
            for story in stories:
                metrics = await AnalyticsService.get_story_metrics(story.id)
                story_metrics.append(metrics)
            
            # Sort by total views to find most popular
            story_metrics.sort(key=lambda x: x.get('total_views', 0), reverse=True)
            
            # Calculate totals
            total_views = sum(s.get('total_views', 0) for s in story_metrics)
            total_likes = sum(s.get('total_likes', 0) for s in story_metrics)
            total_comments = sum(s.get('total_comments', 0) for s in story_metrics)
            
            # Get follower count
            follower_count = await db.follow.count(
                where={'following_id': author_id}
            )
            
            dashboard = {
                'author_id': author_id,
                'total_stories': len(stories),
                'total_views': total_views,
                'total_likes': total_likes,
                'total_comments': total_comments,
                'follower_count': follower_count,
                'stories': story_metrics[:10],  # Top 10 stories
                'most_popular_story': story_metrics[0] if story_metrics else None
            }
            
            await db.disconnect()
            return dashboard
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    async def get_comparative_metrics(story_id: str, author_id: str) -> Dict:
        """
        Get comparative metrics for a story.
        
        Requirements:
            - 26.12: Comparative metrics vs. author's other stories and platform averages
        
        Returns:
            Dictionary with comparative data
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Get this story's metrics
            story_metrics = await AnalyticsService.get_story_metrics(story_id)
            
            # Get author's other stories
            other_stories = await db.story.find_many(
                where={
                    'author_id': author_id,
                    'published': True,
                    'deleted_at': None,
                    'id': {'not': story_id}
                }
            )
            
            # Calculate author averages
            if other_stories:
                author_metrics = []
                for story in other_stories:
                    metrics = await AnalyticsService.get_story_metrics(story.id)
                    author_metrics.append(metrics)
                
                avg_views = sum(m.get('total_views', 0) for m in author_metrics) / len(author_metrics)
                avg_likes = sum(m.get('total_likes', 0) for m in author_metrics) / len(author_metrics)
                avg_completion = sum(m.get('completion_rate', 0) for m in author_metrics) / len(author_metrics)
            else:
                avg_views = 0
                avg_likes = 0
                avg_completion = 0
            
            # Calculate platform averages (simplified)
            all_stories = await db.story.find_many(
                where={'published': True, 'deleted_at': None},
                take=100  # Sample for performance
            )
            
            if all_stories:
                platform_metrics = []
                for story in all_stories[:20]:  # Limit for performance
                    metrics = await AnalyticsService.get_story_metrics(story.id)
                    platform_metrics.append(metrics)
                
                platform_avg_views = sum(m.get('total_views', 0) for m in platform_metrics) / len(platform_metrics)
                platform_avg_likes = sum(m.get('total_likes', 0) for m in platform_metrics) / len(platform_metrics)
            else:
                platform_avg_views = 0
                platform_avg_likes = 0
            
            comparative = {
                'story_metrics': story_metrics,
                'author_averages': {
                    'avg_views': round(avg_views, 2),
                    'avg_likes': round(avg_likes, 2),
                    'avg_completion_rate': round(avg_completion, 2)
                },
                'platform_averages': {
                    'avg_views': round(platform_avg_views, 2),
                    'avg_likes': round(platform_avg_likes, 2)
                },
                'performance_vs_author': {
                    'views': round((story_metrics.get('total_views', 0) / avg_views * 100) if avg_views > 0 else 0, 2),
                    'likes': round((story_metrics.get('total_likes', 0) / avg_likes * 100) if avg_likes > 0 else 0, 2)
                },
                'performance_vs_platform': {
                    'views': round((story_metrics.get('total_views', 0) / platform_avg_views * 100) if platform_avg_views > 0 else 0, 2),
                    'likes': round((story_metrics.get('total_likes', 0) / platform_avg_likes * 100) if platform_avg_likes > 0 else 0, 2)
                }
            }
            
            await db.disconnect()
            return comparative
            
        except Exception as e:
            await db.disconnect()
            raise e
    
    @staticmethod
    def export_to_csv(data: List[Dict], filename: str = 'analytics.csv') -> str:
        """
        Export analytics data to CSV format.
        
        Requirements:
            - 26.10: Export analytics data as CSV
        
        Args:
            data: List of dictionaries to export
            filename: Name for the CSV file
        
        Returns:
            CSV string
        """
        if not data:
            return ''
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()

    @staticmethod
    def get_mobile_analytics() -> Dict:
        """
        Get mobile-specific analytics metrics.
        
        Returns mobile analytics including:
        - API response times per client type
        - Push notification delivery rates
        - Media upload success rates
        
        Requirements:
            - 14.2: Track API response times per client type
            - 14.3: Track push notification delivery rates
            - 14.4: Track media upload success rates
        
        Returns:
            Dictionary with mobile analytics data
        """
        mobile_analytics = get_mobile_analytics_service()
        return mobile_analytics.get_all_mobile_metrics()
