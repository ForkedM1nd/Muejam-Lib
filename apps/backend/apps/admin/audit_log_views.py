"""
Audit Log Query and Reporting Views

Provides API endpoints for querying and analyzing audit logs.

Requirements:
- 32.8: Provide audit log search and filtering
- 32.9: Alert on suspicious patterns
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from prisma import Prisma
from prisma.enums import AuditActionType, AuditResourceType, AuditResult
from apps.admin.audit_alert_service import AuditAlertService
from apps.core.decorators import async_api_view

logger = logging.getLogger(__name__)


def require_admin(view_func):
    """Decorator to require admin authentication."""
    def wrapper(request, *args, **kwargs):
        # TODO: Implement proper admin authentication check
        # For now, this is a placeholder
        # In production, check if user has admin role
        return view_func(request, *args, **kwargs)
    return wrapper


@api_view(['GET'])
@async_api_view
@require_admin
async def get_audit_logs(request):
    """
    Get audit logs with filtering and pagination.
    
    GET /api/admin/audit-logs
    
    Query parameters:
    - user_id: Filter by user ID
    - action_type: Filter by action type
    - resource_type: Filter by resource type
    - resource_id: Filter by resource ID
    - start_date: Filter by start date (ISO format)
    - end_date: Filter by end date (ISO format)
    - result: Filter by result (SUCCESS, FAILURE, PARTIAL)
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50, max: 100)
    
    Returns:
        JSON response with audit logs and pagination info
        
    Requirements: 32.8
    """
    try:
        # Parse query parameters
        user_id = request.GET.get('user_id')
        action_type = request.GET.get('action_type')
        resource_type = request.GET.get('resource_type')
        resource_id = request.GET.get('resource_id')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        result = request.GET.get('result')
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 50)), 100)
        
        # Build filter conditions
        where_conditions = {}
        
        if user_id:
            where_conditions['user_id'] = user_id
        
        if action_type:
            try:
                where_conditions['action_type'] = AuditActionType[action_type]
            except KeyError:
                return JsonResponse({
                    'error': f'Invalid action_type: {action_type}'
                }, status=400)
        
        if resource_type:
            try:
                where_conditions['resource_type'] = AuditResourceType[resource_type]
            except KeyError:
                return JsonResponse({
                    'error': f'Invalid resource_type: {resource_type}'
                }, status=400)
        
        if resource_id:
            where_conditions['resource_id'] = resource_id
        
        if result:
            try:
                where_conditions['result'] = AuditResult[result]
            except KeyError:
                return JsonResponse({
                    'error': f'Invalid result: {result}'
                }, status=400)
        
        # Date range filtering
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter['gte'] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                date_filter['lte'] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            where_conditions['created_at'] = date_filter
        
        # Connect to database
        db = Prisma()
        await db.connect()
        
        try:
            # Get total count
            total_count = await db.auditlog.count(where=where_conditions)
            
            # Calculate pagination
            skip = (page - 1) * page_size
            total_pages = (total_count + page_size - 1) // page_size
            
            # Query audit logs
            audit_logs = await db.auditlog.find_many(
                where=where_conditions,
                order={'created_at': 'desc'},
                skip=skip,
                take=page_size
            )
            
            # Format response
            logs_data = []
            for log in audit_logs:
                logs_data.append({
                    'id': log.id,
                    'user_id': log.user_id,
                    'action_type': log.action_type,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id,
                    'ip_address': log.ip_address,
                    'user_agent': log.user_agent,
                    'result': log.result,
                    'metadata': log.metadata,
                    'created_at': log.created_at.isoformat()
                })
            
            return JsonResponse({
                'logs': logs_data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            })
            
        finally:
            await db.disconnect()
            
    except ValueError as e:
        logger.error(f"Invalid parameter: {str(e)}")
        return JsonResponse({
            'error': f'Invalid parameter: {str(e)}'
        }, status=400)
    except Exception as e:
        logger.error(f"Error querying audit logs: {str(e)}")
        return JsonResponse({
            'error': 'Internal server error'
        }, status=500)


@api_view(['GET'])
@async_api_view
@require_admin
async def detect_suspicious_patterns(request):
    """
    Detect suspicious patterns in audit logs.
    
    GET /api/admin/audit-logs/suspicious-patterns
    
    Query parameters:
    - hours: Number of hours to analyze (default: 24)
    
    Returns:
        JSON response with detected suspicious patterns
        
    Requirements: 32.9
    """
    try:
        hours = int(request.GET.get('hours', 24))
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        db = Prisma()
        await db.connect()
        
        try:
            suspicious_patterns = []
            
            # 1. Detect multiple failed logins
            failed_logins = await _detect_failed_logins(db, start_time)
            if failed_logins:
                suspicious_patterns.extend(failed_logins)
            
            # 2. Detect unusual access patterns
            unusual_access = await _detect_unusual_access(db, start_time)
            if unusual_access:
                suspicious_patterns.extend(unusual_access)
            
            # 3. Detect bulk data exports
            bulk_exports = await _detect_bulk_exports(db, start_time)
            if bulk_exports:
                suspicious_patterns.extend(bulk_exports)
            
            return JsonResponse({
                'patterns': suspicious_patterns,
                'analyzed_period': {
                    'start': start_time.isoformat(),
                    'end': datetime.utcnow().isoformat(),
                    'hours': hours
                }
            })
            
        finally:
            await db.disconnect()
            
    except Exception as e:
        logger.error(f"Error detecting suspicious patterns: {str(e)}")
        return JsonResponse({
            'error': 'Internal server error'
        }, status=500)


async def _detect_failed_logins(db: Prisma, start_time: datetime) -> List[Dict[str, Any]]:
    """
    Detect multiple failed login attempts.
    
    Threshold: 5 or more failed logins from same IP or user within the time period.
    """
    patterns = []
    
    # Get failed login attempts
    failed_logins = await db.auditlog.find_many(
        where={
            'action_type': AuditActionType.LOGIN_FAILED,
            'created_at': {'gte': start_time}
        },
        order={'created_at': 'desc'}
    )
    
    # Group by IP address
    ip_failures = {}
    for log in failed_logins:
        ip = log.ip_address
        if ip not in ip_failures:
            ip_failures[ip] = []
        ip_failures[ip].append(log)
    
    # Check for suspicious IPs
    for ip, logs in ip_failures.items():
        if len(logs) >= 5:
            patterns.append({
                'type': 'multiple_failed_logins',
                'severity': 'high',
                'description': f'Multiple failed login attempts from IP {ip}',
                'details': {
                    'ip_address': ip,
                    'attempt_count': len(logs),
                    'first_attempt': logs[-1].created_at.isoformat(),
                    'last_attempt': logs[0].created_at.isoformat(),
                    'affected_users': list(set(log.user_id for log in logs if log.user_id))
                }
            })
    
    # Group by user ID
    user_failures = {}
    for log in failed_logins:
        if log.user_id:
            if log.user_id not in user_failures:
                user_failures[log.user_id] = []
            user_failures[log.user_id].append(log)
    
    # Check for suspicious users
    for user_id, logs in user_failures.items():
        if len(logs) >= 5:
            patterns.append({
                'type': 'multiple_failed_logins',
                'severity': 'medium',
                'description': f'Multiple failed login attempts for user {user_id}',
                'details': {
                    'user_id': user_id,
                    'attempt_count': len(logs),
                    'first_attempt': logs[-1].created_at.isoformat(),
                    'last_attempt': logs[0].created_at.isoformat(),
                    'source_ips': list(set(log.ip_address for log in logs))
                }
            })
    
    return patterns


async def _detect_unusual_access(db: Prisma, start_time: datetime) -> List[Dict[str, Any]]:
    """
    Detect unusual access patterns.
    
    Patterns:
    - Same user accessing from multiple IPs in short time
    - Rapid succession of administrative actions
    """
    patterns = []
    
    # Get all login successes
    logins = await db.auditlog.find_many(
        where={
            'action_type': AuditActionType.LOGIN_SUCCESS,
            'created_at': {'gte': start_time}
        },
        order={'created_at': 'desc'}
    )
    
    # Group by user
    user_logins = {}
    for log in logins:
        if log.user_id not in user_logins:
            user_logins[log.user_id] = []
        user_logins[log.user_id].append(log)
    
    # Check for multiple IPs per user
    for user_id, logs in user_logins.items():
        unique_ips = set(log.ip_address for log in logs)
        if len(unique_ips) >= 3:
            patterns.append({
                'type': 'multiple_ip_access',
                'severity': 'medium',
                'description': f'User {user_id} accessed from multiple IPs',
                'details': {
                    'user_id': user_id,
                    'ip_count': len(unique_ips),
                    'ip_addresses': list(unique_ips),
                    'login_count': len(logs),
                    'time_span_hours': (logs[0].created_at - logs[-1].created_at).total_seconds() / 3600
                }
            })
    
    # Check for rapid administrative actions
    admin_actions = await db.auditlog.find_many(
        where={
            'action_type': {
                'in': [
                    AuditActionType.CONFIG_CHANGE,
                    AuditActionType.USER_ROLE_CHANGE,
                    AuditActionType.SYSTEM_SETTINGS_UPDATE,
                    AuditActionType.ROLE_ASSIGNMENT
                ]
            },
            'created_at': {'gte': start_time}
        },
        order={'created_at': 'desc'}
    )
    
    # Group by user
    user_admin_actions = {}
    for log in admin_actions:
        if log.user_id not in user_admin_actions:
            user_admin_actions[log.user_id] = []
        user_admin_actions[log.user_id].append(log)
    
    # Check for rapid actions
    for user_id, logs in user_admin_actions.items():
        if len(logs) >= 10:
            time_span = (logs[0].created_at - logs[-1].created_at).total_seconds() / 60
            if time_span < 60:  # 10+ actions in less than 1 hour
                patterns.append({
                    'type': 'rapid_admin_actions',
                    'severity': 'high',
                    'description': f'Rapid administrative actions by user {user_id}',
                    'details': {
                        'user_id': user_id,
                        'action_count': len(logs),
                        'time_span_minutes': time_span,
                        'actions_per_minute': len(logs) / max(time_span, 1),
                        'action_types': list(set(log.action_type for log in logs))
                    }
                })
    
    return patterns


async def _detect_bulk_exports(db: Prisma, start_time: datetime) -> List[Dict[str, Any]]:
    """
    Detect bulk data export requests.
    
    Threshold: 3 or more data export requests from same user within the time period.
    """
    patterns = []
    
    # Get data export requests
    exports = await db.auditlog.find_many(
        where={
            'action_type': AuditActionType.DATA_EXPORT_REQUEST,
            'created_at': {'gte': start_time}
        },
        order={'created_at': 'desc'}
    )
    
    # Group by user
    user_exports = {}
    for log in exports:
        if log.user_id not in user_exports:
            user_exports[log.user_id] = []
        user_exports[log.user_id].append(log)
    
    # Check for bulk exports
    for user_id, logs in user_exports.items():
        if len(logs) >= 3:
            patterns.append({
                'type': 'bulk_data_exports',
                'severity': 'high',
                'description': f'Multiple data export requests by user {user_id}',
                'details': {
                    'user_id': user_id,
                    'export_count': len(logs),
                    'first_export': logs[-1].created_at.isoformat(),
                    'last_export': logs[0].created_at.isoformat(),
                    'source_ips': list(set(log.ip_address for log in logs))
                }
            })
    
    return patterns



@api_view(['POST'])
@async_api_view
@require_admin
async def trigger_suspicious_pattern_alert(request):
    """
    Manually trigger suspicious pattern detection and send alerts.
    
    POST /api/admin/audit-logs/trigger-alert
    
    Request body:
    - admin_emails: List of administrator email addresses
    - hours: Number of hours to analyze (default: 24)
    
    Returns:
        JSON response with alert status
        
    Requirements: 32.9
    """
    try:
        import json
        body = json.loads(request.body)
        
        admin_emails = body.get('admin_emails', [])
        hours = body.get('hours', 24)
        
        if not admin_emails:
            return JsonResponse({
                'error': 'admin_emails is required'
            }, status=400)
        
        # Check for suspicious patterns and send alerts
        result = await AuditAlertService.check_and_alert(admin_emails, hours)
        
        return JsonResponse({
            'success': True,
            'patterns_found': result.get('patterns_found', 0),
            'alert_sent': result.get('alert_sent', False),
            'message': f"Found {result.get('patterns_found', 0)} suspicious pattern(s)"
        })
        
    except Exception as e:
        logger.error(f"Error triggering suspicious pattern alert: {str(e)}")
        return JsonResponse({
            'error': 'Internal server error'
        }, status=500)
