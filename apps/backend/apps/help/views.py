from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.core.decorators import async_api_view
from apps.admin.permissions import IsAdministrator
from .serializers import (
    HelpArticleSerializer,
    HelpArticleCreateSerializer,
    HelpArticleFeedbackSerializer,
    SupportRequestSerializer,
    HelpSearchSerializer
)
from .service import HelpService


class HelpCategoriesView(APIView):
    """Get all help article categories"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        categories = [
            {'value': 'GETTING_STARTED', 'label': 'Getting Started'},
            {'value': 'READING_STORIES', 'label': 'Reading Stories'},
            {'value': 'WRITING_CONTENT', 'label': 'Writing Content'},
            {'value': 'ACCOUNT_SETTINGS', 'label': 'Account Settings'},
            {'value': 'PRIVACY_SAFETY', 'label': 'Privacy & Safety'},
            {'value': 'TROUBLESHOOTING', 'label': 'Troubleshooting'},
        ]
        return Response(categories)


class HelpArticleListView(APIView):
    """List help articles by category"""
    permission_classes = [AllowAny]
    
    @async_api_view
    async def get(self, request):
        category = request.query_params.get('category')
        
        if category:
            articles = await HelpService.get_articles_by_category(category)
        else:
            # Get most viewed articles
            articles = await HelpService.get_most_viewed_articles(limit=20)
        
        serializer = HelpArticleSerializer(articles, many=True)
        return Response(serializer.data)


class HelpArticleDetailView(APIView):
    """Get help article by slug"""
    permission_classes = [AllowAny]
    
    @async_api_view
    async def get(self, request, slug):
        article = await HelpService.get_article_by_slug(slug)
        
        if not article:
            return Response(
                {'error': 'Article not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = HelpArticleSerializer(article)
        return Response(serializer.data)


class HelpSearchView(APIView):
    """Search help articles"""
    permission_classes = [AllowAny]
    
    @async_api_view
    async def get(self, request):
        query = request.query_params.get('q', '')
        
        if not query:
            return Response(
                {'error': 'Query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = getattr(request, 'user_profile_id', None)
        articles = await HelpService.search_articles(query, user_id)
        
        serializer = HelpArticleSerializer(articles, many=True)
        return Response(serializer.data)


class HelpArticleFeedbackView(APIView):
    """Submit feedback for help article"""
    permission_classes = [AllowAny]
    
    @async_api_view
    async def post(self, request, article_id):
        serializer = HelpArticleFeedbackSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = getattr(request, 'user_profile_id', None)
        
        feedback = await HelpService.submit_feedback(
            article_id=article_id,
            helpful=serializer.validated_data['helpful'],
            user_id=user_id,
            comment=serializer.validated_data.get('comment')
        )
        
        return Response({'message': 'Feedback submitted successfully'})


class SupportRequestView(APIView):
    """Submit support request"""
    permission_classes = [AllowAny]
    
    @async_api_view
    async def post(self, request):
        serializer = SupportRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = getattr(request, 'user_profile_id', None)
        
        support_request = await HelpService.create_support_request(
            email=serializer.validated_data['email'],
            name=serializer.validated_data['name'],
            subject=serializer.validated_data['subject'],
            message=serializer.validated_data['message'],
            user_id=user_id
        )
        
        return Response(
            {'message': 'Support request submitted successfully'},
            status=status.HTTP_201_CREATED
        )


# Admin views
class AdminHelpArticleListView(APIView):
    """Admin: List all help articles"""
    permission_classes = [IsAuthenticated, IsAdministrator]
    
    @async_api_view
    async def get(self, request):
        category = request.query_params.get('category')
        
        if category:
            articles = await HelpService.get_articles_by_category(
                category,
                published_only=False
            )
        else:
            # Get all articles for admin
            articles = await HelpService.get_most_viewed_articles(limit=100)
        
        serializer = HelpArticleSerializer(articles, many=True)
        return Response(serializer.data)
    
    @async_api_view
    async def post(self, request):
        """Create new help article"""
        serializer = HelpArticleCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        article = await HelpService.create_article(
            title=serializer.validated_data['title'],
            slug=serializer.validated_data['slug'],
            category=serializer.validated_data['category'],
            content=serializer.validated_data['content'],
            author_id=request.user_profile_id,
            excerpt=serializer.validated_data.get('excerpt')
        )
        
        response_serializer = HelpArticleSerializer(article)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class AdminHelpArticleDetailView(APIView):
    """Admin: Manage individual help article"""
    permission_classes = [IsAuthenticated, IsAdministrator]
    
    @async_api_view
    async def put(self, request, article_id):
        """Update help article"""
        serializer = HelpArticleCreateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        article = await HelpService.update_article(
            article_id=article_id,
            title=serializer.validated_data.get('title'),
            content=serializer.validated_data.get('content'),
            category=serializer.validated_data.get('category'),
            excerpt=serializer.validated_data.get('excerpt')
        )
        
        response_serializer = HelpArticleSerializer(article)
        return Response(response_serializer.data)
    
    @async_api_view
    async def delete(self, request, article_id):
        """Delete help article"""
        await HelpService.delete_article(article_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminHelpArticlePublishView(APIView):
    """Admin: Publish help article"""
    permission_classes = [IsAuthenticated, IsAdministrator]
    
    @async_api_view
    async def post(self, request, article_id):
        article = await HelpService.publish_article(article_id)
        serializer = HelpArticleSerializer(article)
        return Response(serializer.data)


class AdminHelpAnalyticsView(APIView):
    """Admin: Get help analytics"""
    permission_classes = [IsAuthenticated, IsAdministrator]
    
    @async_api_view
    async def get(self, request):
        popular_searches = await HelpService.get_popular_searches(limit=20)
        most_viewed = await HelpService.get_most_viewed_articles(limit=10)
        
        return Response({
            'popular_searches': popular_searches,
            'most_viewed_articles': HelpArticleSerializer(most_viewed, many=True).data
        })
