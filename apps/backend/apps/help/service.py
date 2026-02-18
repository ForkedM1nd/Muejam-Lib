from datetime import datetime
from typing import List, Optional
from prisma import Prisma
from prisma.models import HelpArticle, HelpSearchQuery, HelpArticleFeedback, SupportRequest


class HelpService:
    """Service for managing help articles and support"""
    
    @staticmethod
    async def get_articles_by_category(category: str, published_only: bool = True) -> List[HelpArticle]:
        """Get all articles in a category"""
        db = Prisma()
        await db.connect()
        
        try:
            where_clause = {'category': category}
            if published_only:
                where_clause['status'] = 'PUBLISHED'
            
            articles = await db.helparticle.find_many(
                where=where_clause,
                order={'published_at': 'desc'}
            )
            return articles
        finally:
            await db.disconnect()
    
    @staticmethod
    async def get_article_by_slug(slug: str) -> Optional[HelpArticle]:
        """Get article by slug and increment view count"""
        db = Prisma()
        await db.connect()
        
        try:
            article = await db.helparticle.find_unique(
                where={'slug': slug}
            )
            
            if article:
                # Increment view count
                await db.helparticle.update(
                    where={'id': article.id},
                    data={'view_count': article.view_count + 1}
                )
                # Fetch updated article
                article = await db.helparticle.find_unique(
                    where={'slug': slug}
                )
            
            return article
        finally:
            await db.disconnect()
    
    @staticmethod
    async def get_most_viewed_articles(limit: int = 10) -> List[HelpArticle]:
        """Get most viewed published articles"""
        db = Prisma()
        await db.connect()
        
        try:
            articles = await db.helparticle.find_many(
                where={'status': 'PUBLISHED'},
                order={'view_count': 'desc'},
                take=limit
            )
            return articles
        finally:
            await db.disconnect()
    
    @staticmethod
    async def search_articles(query: str, user_id: Optional[str] = None) -> List[HelpArticle]:
        """Search articles by title and content"""
        db = Prisma()
        await db.connect()
        
        try:
            # Log search query
            await db.helpsearchquery.create(
                data={
                    'query': query,
                    'user_id': user_id
                }
            )
            
            # Search in title and content (case-insensitive)
            # Note: This is a simple implementation. For production, consider using
            # PostgreSQL full-text search or Elasticsearch
            articles = await db.helparticle.find_many(
                where={
                    'status': 'PUBLISHED',
                    'OR': [
                        {'title': {'contains': query, 'mode': 'insensitive'}},
                        {'content': {'contains': query, 'mode': 'insensitive'}}
                    ]
                },
                order={'view_count': 'desc'}
            )
            
            return articles
        finally:
            await db.disconnect()
    
    @staticmethod
    async def create_article(
        title: str,
        slug: str,
        category: str,
        content: str,
        author_id: str,
        excerpt: Optional[str] = None
    ) -> HelpArticle:
        """Create a new help article"""
        db = Prisma()
        await db.connect()
        
        try:
            article = await db.helparticle.create(
                data={
                    'title': title,
                    'slug': slug,
                    'category': category,
                    'content': content,
                    'excerpt': excerpt,
                    'author_id': author_id,
                    'status': 'DRAFT'
                }
            )
            return article
        finally:
            await db.disconnect()
    
    @staticmethod
    async def update_article(
        article_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        excerpt: Optional[str] = None
    ) -> HelpArticle:
        """Update a help article"""
        db = Prisma()
        await db.connect()
        
        try:
            update_data = {}
            if title is not None:
                update_data['title'] = title
            if content is not None:
                update_data['content'] = content
            if category is not None:
                update_data['category'] = category
            if excerpt is not None:
                update_data['excerpt'] = excerpt
            
            article = await db.helparticle.update(
                where={'id': article_id},
                data=update_data
            )
            return article
        finally:
            await db.disconnect()
    
    @staticmethod
    async def publish_article(article_id: str) -> HelpArticle:
        """Publish a help article"""
        db = Prisma()
        await db.connect()
        
        try:
            article = await db.helparticle.update(
                where={'id': article_id},
                data={
                    'status': 'PUBLISHED',
                    'published_at': datetime.utcnow()
                }
            )
            return article
        finally:
            await db.disconnect()
    
    @staticmethod
    async def delete_article(article_id: str) -> bool:
        """Delete a help article"""
        db = Prisma()
        await db.connect()
        
        try:
            await db.helparticle.delete(
                where={'id': article_id}
            )
            return True
        finally:
            await db.disconnect()
    
    @staticmethod
    async def submit_feedback(
        article_id: str,
        helpful: bool,
        user_id: Optional[str] = None,
        comment: Optional[str] = None
    ) -> HelpArticleFeedback:
        """Submit feedback for an article"""
        db = Prisma()
        await db.connect()
        
        try:
            # Create feedback
            feedback = await db.helparticlefeedback.create(
                data={
                    'article_id': article_id,
                    'user_id': user_id,
                    'helpful': helpful,
                    'comment': comment
                }
            )
            
            # Update article helpful counts
            article = await db.helparticle.find_unique(
                where={'id': article_id}
            )
            
            if article:
                if helpful:
                    await db.helparticle.update(
                        where={'id': article_id},
                        data={'helpful_yes': article.helpful_yes + 1}
                    )
                else:
                    await db.helparticle.update(
                        where={'id': article_id},
                        data={'helpful_no': article.helpful_no + 1}
                    )
            
            return feedback
        finally:
            await db.disconnect()
    
    @staticmethod
    async def create_support_request(
        email: str,
        name: str,
        subject: str,
        message: str,
        user_id: Optional[str] = None
    ) -> SupportRequest:
        """Create a support request"""
        db = Prisma()
        await db.connect()
        
        try:
            request = await db.supportrequest.create(
                data={
                    'user_id': user_id,
                    'email': email,
                    'name': name,
                    'subject': subject,
                    'message': message
                }
            )
            return request
        finally:
            await db.disconnect()
    
    @staticmethod
    async def get_popular_searches(limit: int = 10) -> List[dict]:
        """Get most popular search queries"""
        db = Prisma()
        await db.connect()
        
        try:
            # Group by query and count
            # Note: This is a simplified version. For production, use raw SQL
            # or aggregate queries for better performance
            queries = await db.helpsearchquery.find_many(
                order={'created_at': 'desc'},
                take=1000
            )
            
            # Count occurrences
            query_counts = {}
            for q in queries:
                query_counts[q.query] = query_counts.get(q.query, 0) + 1
            
            # Sort by count and return top results
            sorted_queries = sorted(
                query_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            return [{'query': q, 'count': c} for q, c in sorted_queries]
        finally:
            await db.disconnect()
