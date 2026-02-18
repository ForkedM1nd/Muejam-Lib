"""
Admin Dashboard API Views.

Provides REST API endpoints for the admin dashboard.
Implements Requirements 17.1-17.5.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .dashboard_service import AdminDashboardService
from .permissions import IsAdministrator


class AdminDashboardView(APIView):
    """
    Main admin dashboard endpoint.
    
    Implements Requirement 17.1: Admin dashboard accessible only to Administrator role.
    
    GET /api/admin/dashboard
    Returns comprehensive dashboard data including all metrics.
    """
    permission_classes = [IsAuthenticated, IsAdministrator]
    
    def get(self, request):
        """
        Get complete dashboard data.
        
        Returns:
            - system_health: System health indicators
            - real_time_metrics: Real-time platform metrics
            - business_metrics: Business metrics (30 days)
            - moderation_metrics: Content moderation metrics
        """
        try:
            dashboard_data = {
                'system_health': AdminDashboardService.get_system_health(),
                'real_time_metrics': AdminDashboardService.get_real_time_metrics(),
                'business_metrics': AdminDashboardService.get_business_metrics(days=30),
                'moderation_metrics': AdminDashboardService.get_moderation_metrics()
            }
            
            return Response(dashboard_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch dashboard data', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RealTimeMetricsView(APIView):
    """
    Real-time metrics endpoint.
    
    Implements Requirement 17.2: Display real-time metrics.
    
    GET /api/admin/metrics/real-time
    Returns real-time platform metrics.
    """
    permission_classes = [IsAuthenticated, IsAdministrator]
    
    @method_decorator(cache_page(60))  # Cache for 60 seconds
    def get(self, request):
        """
        Get real-time metrics.
        
        Returns:
            - active_users: Count of active users
            - requests_per_minute: Current request rate
            - error_rate: Current error rate
            - api_response_times: Response time percentiles
        """
        try:
            metrics = AdminDashboardService.get_real_time_metrics()
            return Response(metrics, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch real-time metrics', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BusinessMetricsView(APIView):
    """
    Business metrics endpoint.
    
    Implements Requirement 17.3: Display business metrics.
    
    GET /api/admin/metrics/business?days=30
    Returns business metrics for specified time period.
    """
    permission_classes = [IsAuthenticated, IsAdministrator]
    
    def get(self, request):
        """
        Get business metrics.
        
        Query Parameters:
            days: Number of days to look back (default 30)
        
        Returns:
            - new_signups: User signup metrics
            - stories_published: Story publication metrics
            - whispers_posted: Whisper posting metrics
            - engagement_rates: Engagement metrics
            - user_retention: Retention metrics
        """
        try:
            days = int(request.query_params.get('days', 30))
            
            # Validate days parameter
            if days < 1 or days > 365:
                return Response(
                    {'error': 'Days parameter must be between 1 and 365'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            metrics = AdminDashboardService.get_business_metrics(days=days)
            return Response(metrics, status=status.HTTP_200_OK)
        except ValueError:
            return Response(
                {'error': 'Invalid days parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch business metrics', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SystemHealthView(APIView):
    """
    System health endpoint.
    
    Implements Requirement 17.5: Display system health indicators.
    
    GET /api/admin/health
    Returns system health status.
    """
    permission_classes = [IsAuthenticated, IsAdministrator]
    
    @method_decorator(cache_page(60))  # Cache for 60 seconds
    def get(self, request):
        """
        Get system health indicators.
        
        Returns:
            - database_status: Database health status
            - cache_status: Cache health status
            - external_services: External service statuses
            - disk_space: Disk usage percentage
            - memory_usage: Memory usage percentage
        """
        try:
            health = AdminDashboardService.get_system_health()
            return Response(health, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch system health', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ModerationMetricsView(APIView):
    """
    Moderation metrics endpoint.
    
    Implements Requirement 17.4: Display content moderation metrics.
    
    GET /api/admin/metrics/moderation
    Returns content moderation metrics.
    """
    permission_classes = [IsAuthenticated, IsAdministrator]
    
    @method_decorator(cache_page(60))  # Cache for 60 seconds
    def get(self, request):
        """
        Get moderation metrics.
        
        Returns:
            - pending_reports: Count of pending reports
            - reports_resolved_today: Count of reports resolved today
            - average_resolution_time: Average resolution time in hours
            - actions_by_type: Breakdown of moderation actions
        """
        try:
            metrics = AdminDashboardService.get_moderation_metrics()
            return Response(metrics, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch moderation metrics', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
