"""Views for author analytics dashboard."""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from apps.core.decorators import async_api_view
from .analytics_service import AnalyticsService


@api_view(['GET'])
@async_api_view
async def author_dashboard(request):
    """
    GET /v1/analytics/dashboard - Get author analytics dashboard
    
    Requirements:
        - 26.1: Analytics dashboard accessible to users with published content
        - 26.9: Most popular stories and chapters by engagement
    
    Returns comprehensive analytics for the authenticated author
    """
    if not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Check if user has published content
    from prisma import Prisma
    db = Prisma()
    await db.connect()
    
    try:
        has_published = await db.story.count(
            where={
                'author_id': request.user_profile.id,
                'published': True,
                'deleted_at': None
            }
        )
        
        if has_published == 0:
            await db.disconnect()
            return Response(
                {'error': {'code': 'NO_CONTENT', 'message': 'No published content found'}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        await db.disconnect()
    except Exception as e:
        await db.disconnect()
        raise e
    
    # Get dashboard data
    dashboard = await AnalyticsService.get_author_dashboard(request.user_profile.id)
    
    return Response(dashboard)


@api_view(['GET'])
@async_api_view
async def story_analytics(request, story_id):
    """
    GET /v1/analytics/stories/{story_id} - Get detailed analytics for a story
    
    Requirements:
        - 26.2: Story-level metrics
        - 26.3: Chapter-level metrics
        - 26.4: Reader demographics
        - 26.5: Engagement trends
        - 26.6: Traffic sources
        - 26.7: Reader retention
        - 26.12: Comparative metrics
    
    Query params:
        - include: Comma-separated list of sections to include
          (metrics, chapters, demographics, trends, sources, retention, comparative)
    """
    if not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Verify story belongs to author
    from prisma import Prisma
    db = Prisma()
    await db.connect()
    
    try:
        story = await db.story.find_unique(
            where={'id': story_id}
        )
        
        if not story:
            await db.disconnect()
            return Response(
                {'error': {'code': 'NOT_FOUND', 'message': 'Story not found'}},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if story.author_id != request.user_profile.id:
            await db.disconnect()
            return Response(
                {'error': {'code': 'FORBIDDEN', 'message': 'Not authorized to view this story\'s analytics'}},
                status=status.HTTP_403_FORBIDDEN
            )
        
        await db.disconnect()
    except Exception as e:
        await db.disconnect()
        raise e
    
    # Parse include parameter
    include_param = request.query_params.get('include', 'metrics,chapters,trends')
    include_sections = [s.strip() for s in include_param.split(',')]
    
    # Build response
    analytics = {}
    
    if 'metrics' in include_sections:
        analytics['metrics'] = await AnalyticsService.get_story_metrics(story_id)
    
    if 'chapters' in include_sections:
        analytics['chapters'] = await AnalyticsService.get_chapter_metrics(story_id)
    
    if 'demographics' in include_sections:
        analytics['demographics'] = await AnalyticsService.get_reader_demographics(story_id)
    
    if 'trends' in include_sections:
        days = int(request.query_params.get('days', 30))
        analytics['trends'] = await AnalyticsService.get_engagement_trends(story_id, days)
    
    if 'sources' in include_sections:
        analytics['traffic_sources'] = await AnalyticsService.get_traffic_sources(story_id)
    
    if 'retention' in include_sections:
        analytics['retention'] = await AnalyticsService.get_reader_retention(story_id)
    
    if 'comparative' in include_sections:
        analytics['comparative'] = await AnalyticsService.get_comparative_metrics(
            story_id,
            request.user_profile.id
        )
    
    return Response(analytics)


@api_view(['GET'])
@async_api_view
async def follower_growth(request):
    """
    GET /v1/analytics/follower-growth - Get follower growth over time
    
    Requirements:
        - 26.8: Follower growth over time
    
    Query params:
        - days: Number of days to include (default: 90)
    """
    if not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    days = int(request.query_params.get('days', 90))
    
    growth_data = await AnalyticsService.get_follower_growth(
        request.user_profile.id,
        days
    )
    
    return Response({'growth': growth_data})


@api_view(['GET'])
@async_api_view
async def export_analytics(request, story_id):
    """
    GET /v1/analytics/stories/{story_id}/export - Export analytics as CSV
    
    Requirements:
        - 26.10: Export analytics data as CSV
    
    Query params:
        - type: Type of data to export (metrics, chapters, trends)
    """
    if not request.user_profile:
        return Response(
            {'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Verify story belongs to author
    from prisma import Prisma
    db = Prisma()
    await db.connect()
    
    try:
        story = await db.story.find_unique(
            where={'id': story_id}
        )
        
        if not story or story.author_id != request.user_profile.id:
            await db.disconnect()
            return Response(
                {'error': {'code': 'FORBIDDEN', 'message': 'Not authorized'}},
                status=status.HTTP_403_FORBIDDEN
            )
        
        await db.disconnect()
    except Exception as e:
        await db.disconnect()
        raise e
    
    # Get export type
    export_type = request.query_params.get('type', 'metrics')
    
    # Get data based on type
    if export_type == 'metrics':
        data = [await AnalyticsService.get_story_metrics(story_id)]
    elif export_type == 'chapters':
        data = await AnalyticsService.get_chapter_metrics(story_id)
    elif export_type == 'trends':
        days = int(request.query_params.get('days', 30))
        data = await AnalyticsService.get_engagement_trends(story_id, days)
    else:
        return Response(
            {'error': {'code': 'INVALID_TYPE', 'message': 'Invalid export type'}},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Export to CSV
    csv_content = AnalyticsService.export_to_csv(data)
    
    # Return as downloadable file
    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="analytics_{export_type}_{story_id}.csv"'
    
    return response
