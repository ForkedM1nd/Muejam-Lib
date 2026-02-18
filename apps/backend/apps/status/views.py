"""
Status Page API Views.

Provides public REST API endpoints for the status page.
Implements Requirements 18.1-18.12.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.http import HttpResponse
from django.utils.feedgenerator import Rss201rev2Feed
from django.utils import timezone

from .status_service import StatusPageService
from .health_check_service import HealthCheckService
from apps.admin.permissions import IsAdministrator


class StatusPageView(APIView):
    """
    Main status page endpoint.
    
    Implements Requirement 18.1: Public status page accessible without authentication.
    
    GET /api/status
    Returns current platform status.
    """
    permission_classes = [AllowAny]  # Public endpoint
    
    def get(self, request):
        """
        Get current platform status.
        
        Returns:
            - components: List of component statuses
            - overall_status: Overall platform status
            - incidents: Recent incidents
            - maintenance: Scheduled maintenance
            - last_updated: Timestamp
        """
        try:
            current_status = StatusPageService.get_current_status()
            incidents = StatusPageService.get_incident_history(days=7)
            maintenance = StatusPageService.get_scheduled_maintenance()
            
            return Response({
                **current_status,
                'recent_incidents': incidents[:5],  # Last 5 incidents
                'scheduled_maintenance': maintenance
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch status', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ComponentStatusView(APIView):
    """
    Individual component status endpoint.
    
    GET /api/status/components/{component_id}
    Returns detailed status for a specific component.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, component_id):
        """
        Get detailed component status including uptime.
        
        Returns:
            - component: Component details
            - uptime: Uptime percentages for 30, 60, 90 days
        """
        try:
            current_status = StatusPageService.get_current_status()
            
            # Find the component
            component = next(
                (c for c in current_status['components'] if c.get('id') == component_id),
                None
            )
            
            if not component:
                return Response(
                    {'error': 'Component not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get uptime percentages
            uptime = StatusPageService.get_uptime_percentages(component_id)
            
            return Response({
                'component': component,
                'uptime': uptime
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch component status', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IncidentHistoryView(APIView):
    """
    Incident history endpoint.
    
    Implements Requirement 18.5: Display incident history.
    
    GET /api/status/incidents?days=90
    Returns incident history.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Get incident history.
        
        Query Parameters:
            days: Number of days to look back (default 90)
        
        Returns:
            List of incidents with details
        """
        try:
            days = int(request.query_params.get('days', 90))
            
            if days < 1 or days > 365:
                return Response(
                    {'error': 'Days parameter must be between 1 and 365'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            incidents = StatusPageService.get_incident_history(days=days)
            
            return Response({
                'incidents': incidents,
                'period_days': days
            }, status=status.HTTP_200_OK)
        except ValueError:
            return Response(
                {'error': 'Invalid days parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch incident history', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IncidentManagementView(APIView):
    """
    Incident management endpoint (admin only).
    
    Implements Requirements 18.6, 18.7, 18.8.
    
    POST /api/status/incidents - Create incident
    """
    permission_classes = [IsAuthenticated, IsAdministrator]
    
    def post(self, request):
        """
        Create a new incident.
        
        Request Body:
            - title: Incident title
            - description: Incident description
            - severity: Severity level (minor, major, critical)
            - affected_components: List of component IDs
        
        Returns:
            Created incident data
        """
        try:
            title = request.data.get('title')
            description = request.data.get('description')
            severity = request.data.get('severity')
            affected_components = request.data.get('affected_components', [])
            
            if not all([title, description, severity]):
                return Response(
                    {'error': 'Missing required fields'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if severity not in ['minor', 'major', 'critical']:
                return Response(
                    {'error': 'Invalid severity level'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            incident = StatusPageService.create_incident(
                title=title,
                description=description,
                severity=severity,
                affected_component_ids=affected_components
            )
            
            if incident:
                return Response(incident, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': 'Failed to create incident'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            return Response(
                {'error': 'Failed to create incident', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IncidentUpdateView(APIView):
    """
    Incident update endpoint (admin only).
    
    Implements Requirement 18.7: Post incident updates.
    
    POST /api/status/incidents/{incident_id}/updates
    """
    permission_classes = [IsAuthenticated, IsAdministrator]
    
    def post(self, request, incident_id):
        """
        Add an update to an incident.
        
        Request Body:
            - message: Update message
            - status: New incident status (optional)
            - estimated_resolution: ETA for resolution (optional)
        
        Returns:
            Created update data
        """
        try:
            message = request.data.get('message')
            new_status = request.data.get('status')
            estimated_resolution = request.data.get('estimated_resolution')
            
            if not message:
                return Response(
                    {'error': 'Message is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            update = StatusPageService.add_incident_update(
                incident_id=incident_id,
                message=message,
                status=new_status,
                estimated_resolution=estimated_resolution,
                created_by=str(request.user.id) if request.user else None
            )
            
            if update:
                return Response(update, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': 'Failed to create update'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            return Response(
                {'error': 'Failed to create update', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IncidentResolutionView(APIView):
    """
    Incident resolution endpoint (admin only).
    
    Implements Requirement 18.8: Post resolution details.
    
    POST /api/status/incidents/{incident_id}/resolve
    """
    permission_classes = [IsAuthenticated, IsAdministrator]
    
    def post(self, request, incident_id):
        """
        Resolve an incident.
        
        Request Body:
            - root_cause: Root cause description
            - resolution: Resolution description
        
        Returns:
            Success message
        """
        try:
            root_cause = request.data.get('root_cause')
            resolution = request.data.get('resolution')
            
            if not all([root_cause, resolution]):
                return Response(
                    {'error': 'Root cause and resolution are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            success = StatusPageService.resolve_incident(
                incident_id=incident_id,
                root_cause=root_cause,
                resolution=resolution
            )
            
            if success:
                return Response(
                    {'message': 'Incident resolved successfully'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Failed to resolve incident'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            return Response(
                {'error': 'Failed to resolve incident', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MaintenanceWindowView(APIView):
    """
    Scheduled maintenance endpoint.
    
    Implements Requirement 18.11: Display scheduled maintenance.
    
    GET /api/status/maintenance
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Get scheduled maintenance windows.
        
        Returns:
            List of scheduled maintenance windows
        """
        try:
            maintenance = StatusPageService.get_scheduled_maintenance()
            
            return Response({
                'maintenance_windows': maintenance
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch maintenance windows', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StatusRSSFeedView(APIView):
    """
    RSS feed for status updates.
    
    Implements Requirement 18.12: Provide RSS feed.
    
    GET /api/status/rss
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Generate RSS feed for status updates.
        
        Returns:
            RSS feed XML
        """
        try:
            feed = Rss201rev2Feed(
                title="MueJam Library Status",
                link=request.build_absolute_uri('/status'),
                description="Platform status updates and incidents",
                language="en"
            )
            
            # Add recent incidents to feed
            incidents = StatusPageService.get_incident_history(days=30)
            
            for incident in incidents[:20]:  # Last 20 incidents
                feed.add_item(
                    title=incident['title'],
                    link=request.build_absolute_uri(f"/status/incidents/{incident['id']}"),
                    description=incident['description'],
                    pubdate=timezone.datetime.fromisoformat(incident['started_at'])
                )
            
            response = HttpResponse(content_type='application/rss+xml')
            feed.write(response, 'utf-8')
            return response
        except Exception as e:
            return Response(
                {'error': 'Failed to generate RSS feed', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HealthCheckView(APIView):
    """
    Manual health check trigger (admin only).
    
    POST /api/status/health-check
    Triggers manual health check of all components.
    """
    permission_classes = [IsAuthenticated, IsAdministrator]
    
    def post(self, request):
        """
        Trigger manual health check.
        
        Returns:
            Health check results
        """
        try:
            results = HealthCheckService.check_all_components()
            
            return Response({
                'message': 'Health check completed',
                'results': results
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Health check failed', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
