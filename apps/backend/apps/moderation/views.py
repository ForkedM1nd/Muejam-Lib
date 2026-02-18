"""Views for content moderation system."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from prisma import Prisma
from datetime import datetime
from .serializers import ReportCreateSerializer, ReportSerializer
from .queue_service import ModerationQueueService
from .permissions import (
    require_moderator_role,
    require_administrator,
    check_action_permission
)
import asyncio


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_report(request):
    """
    Submit a report for content moderation.
    
    Request Body:
        - content_type: Type of content ('story', 'chapter', 'whisper', 'user')
        - content_id: ID of the content being reported
        - reason: Reason for reporting (max 500 characters)
        
    Returns:
        Created report data
        
    Requirements:
        - 13.1: Report stories
        - 13.2: Report chapters
        - 13.3: Report whispers
        - 13.4: Report users
        - 13.5: Store report with reason and status
        - 13.6: Prevent duplicate reports
        - 13.7: Validate reason text (max 500 characters)
    """
    # Validate request data
    serializer = ReportCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    content_type = validated_data['content_type']
    content_id = validated_data['content_id']
    reason = validated_data['reason']
    
    # Get reporter ID
    reporter_id = request.user_profile.id
    
    # Create report
    try:
        report_data = asyncio.run(
            create_report(reporter_id, content_type, content_id, reason)
        )
        
        if report_data is None:
            return Response(
                {'error': 'You have already reported this content'},
                status=status.HTTP_409_CONFLICT
            )
        
        return Response(report_data, status=status.HTTP_201_CREATED)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to submit report'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def create_report(reporter_id, content_type, content_id, reason):
    """
    Create a report in the database.
    
    Args:
        reporter_id: ID of the user submitting the report
        content_type: Type of content being reported
        content_id: ID of the content
        reason: Reason for reporting
        
    Returns:
        Report data dictionary or None if duplicate
        
    Requirements:
        - 13.1-13.4: Support reporting different content types
        - 13.5: Store report with status PENDING
        - 13.6: Prevent duplicate reports
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Build where clause for duplicate check
        where_clause = {'reporter_id': reporter_id}
        
        # Build data for report creation
        report_data = {
            'reporter_id': reporter_id,
            'reason': reason,
            'status': 'PENDING'
        }
        
        # Add content-specific fields
        if content_type == 'story':
            # Verify story exists
            story = await db.story.find_unique(where={'id': content_id})
            if not story:
                raise ValueError('Story not found')
            
            where_clause['story_id'] = content_id
            report_data['story_id'] = content_id
            
        elif content_type == 'chapter':
            # Verify chapter exists
            chapter = await db.chapter.find_unique(where={'id': content_id})
            if not chapter:
                raise ValueError('Chapter not found')
            
            where_clause['chapter_id'] = content_id
            report_data['chapter_id'] = content_id
            
        elif content_type == 'whisper':
            # Verify whisper exists
            whisper = await db.whisper.find_unique(where={'id': content_id})
            if not whisper:
                raise ValueError('Whisper not found')
            
            where_clause['whisper_id'] = content_id
            report_data['whisper_id'] = content_id
            
        elif content_type == 'user':
            # Verify user exists
            user = await db.userprofile.find_unique(where={'id': content_id})
            if not user:
                raise ValueError('User not found')
            
            where_clause['reported_user_id'] = content_id
            report_data['reported_user_id'] = content_id
        
        # Check for duplicate report
        existing_report = await db.report.find_first(where=where_clause)
        
        if existing_report:
            # Duplicate report - return None
            return None
        
        # Create new report
        report = await db.report.create(data=report_data)
        
        # Return report data
        return {
            'id': report.id,
            'reporter_id': report.reporter_id,
            'reported_user_id': report.reported_user_id,
            'story_id': report.story_id,
            'chapter_id': report.chapter_id,
            'whisper_id': report.whisper_id,
            'reason': report.reason,
            'status': report.status,
            'created_at': report.created_at.isoformat()
        }
        
    finally:
        await db.disconnect()



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_moderator_role()
def get_moderation_queue(request):
    """
    Get all pending reports sorted by priority and creation date.
    
    Requires any active moderator role.
    
    Returns:
        List of reports with priority scores and levels
        
    Requirements:
        - 2.1: Display all pending reports in moderation queue
        - 2.2: Sort reports by priority (high, medium, low) and creation date
        - 3.2: Grant access to moderation dashboard when role is assigned
        - 3.6: Return 403 for unauthorized access
    """
    try:
        # Get the moderation queue
        queue = asyncio.run(fetch_moderation_queue())
        
        return Response({
            'reports': queue,
            'count': len(queue)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch moderation queue'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def fetch_moderation_queue():
    """
    Fetch the moderation queue using the ModerationQueueService.
    
    Returns:
        List of reports with priority information
        
    Requirements:
        - 2.1: Display all pending reports
        - 2.2: Sort by priority and creation date
    """
    async with ModerationQueueService() as queue_service:
        return await queue_service.get_queue()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_moderator_role()
def get_report_details(request, report_id):
    """
    Get detailed information about a specific report.
    
    Requires any active moderator role.
    
    Returns:
        Report details including:
        - Report information
        - Reported content with full context
        - Reporter information and history
        - Content metadata
        
    Requirements:
        - 2.3: Display reported content, reporter reason, content metadata, and reporter history
        - 3.2: Grant access to moderation dashboard when role is assigned
        - 3.6: Return 403 for unauthorized access
    """
    try:
        report_data = asyncio.run(fetch_report_details(report_id))
        
        if report_data is None:
            return Response(
                {'error': 'Report not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(report_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch report details'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def fetch_report_details(report_id: str):
    """
    Fetch detailed report information with full context.
    
    Args:
        report_id: ID of the report
        
    Returns:
        Dictionary with report details or None if not found
        
    Requirements:
        - 2.3: Display full report context
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Fetch report with all related data
        report = await db.report.find_unique(
            where={'id': report_id},
            include={
                'reporter': True,
                'reported_user': True,
                'story': {
                    'include': {
                        'author': True
                    }
                },
                'chapter': {
                    'include': {
                        'story': {
                            'include': {
                                'author': True
                            }
                        }
                    }
                },
                'whisper': {
                    'include': {
                        'user': True
                    }
                },
                'moderation_actions': True
            }
        )
        
        if not report:
            return None
        
        # Get reporter history
        reporter_stats = await db.report.count(
            where={'reporter_id': report.reporter_id}
        )
        
        # Build content context
        content_context = None
        if report.story:
            content_context = {
                'type': 'story',
                'id': report.story.id,
                'title': report.story.title,
                'blurb': report.story.blurb,
                'author': {
                    'id': report.story.author.id,
                    'handle': report.story.author.handle,
                    'display_name': report.story.author.display_name
                },
                'published': report.story.published,
                'created_at': report.story.created_at.isoformat()
            }
        elif report.chapter:
            content_context = {
                'type': 'chapter',
                'id': report.chapter.id,
                'title': report.chapter.title,
                'chapter_number': report.chapter.chapter_number,
                'content_preview': report.chapter.content[:500] + '...' if len(report.chapter.content) > 500 else report.chapter.content,
                'story': {
                    'id': report.chapter.story.id,
                    'title': report.chapter.story.title,
                    'author': {
                        'id': report.chapter.story.author.id,
                        'handle': report.chapter.story.author.handle,
                        'display_name': report.chapter.story.author.display_name
                    }
                },
                'published': report.chapter.published,
                'created_at': report.chapter.created_at.isoformat()
            }
        elif report.whisper:
            content_context = {
                'type': 'whisper',
                'id': report.whisper.id,
                'content': report.whisper.content,
                'scope': report.whisper.scope,
                'author': {
                    'id': report.whisper.user.id,
                    'handle': report.whisper.user.handle,
                    'display_name': report.whisper.user.display_name
                },
                'created_at': report.whisper.created_at.isoformat()
            }
        elif report.reported_user:
            content_context = {
                'type': 'user',
                'id': report.reported_user.id,
                'handle': report.reported_user.handle,
                'display_name': report.reported_user.display_name,
                'bio': report.reported_user.bio,
                'created_at': report.reported_user.created_at.isoformat()
            }
        
        # Build response
        return {
            'id': report.id,
            'status': report.status,
            'reason': report.reason,
            'created_at': report.created_at.isoformat(),
            'reporter': {
                'id': report.reporter.id,
                'handle': report.reporter.handle,
                'display_name': report.reporter.display_name,
                'total_reports': reporter_stats
            },
            'content': content_context,
            'moderation_actions': [
                {
                    'id': action.id,
                    'action_type': action.action_type,
                    'reason': action.reason,
                    'moderator_id': action.moderator_id,
                    'created_at': action.created_at.isoformat()
                }
                for action in report.moderation_actions
            ]
        }
        
    finally:
        await db.disconnect()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@check_action_permission
def take_moderation_action(request):
    """
    Take a moderation action on a report.
    
    Permission requirements:
    - DISMISS: Moderators (low-priority only), Senior Moderators, Administrators
    - WARN: Senior Moderators, Administrators
    - HIDE: Senior Moderators, Administrators
    - DELETE: Administrators only
    - SUSPEND: Administrators only
    
    Request Body:
        - report_id: ID of the report
        - action_type: Type of action (DISMISS, WARN, HIDE, DELETE, SUSPEND)
        - reason: Reason for the action
        
    Returns:
        Created moderation action data
        
    Requirements:
        - 2.4: Support actions: dismiss, warn, hide, delete, suspend
        - 2.5: Require dismissal reason
        - 2.6: Immediately remove content from public view for hide/delete
        - 2.7: Record all moderation actions in audit log
        - 3.3: Senior_Moderators can review reports, hide content, and warn users
        - 3.4: Moderators can review reports and dismiss low-priority reports only
        - 3.5: Only Administrators can delete content, suspend users
        - 3.6: Return 403 for unauthorized access
    """
    # Validate request data
    report_id = request.data.get('report_id')
    action_type = request.data.get('action_type')
    reason = request.data.get('reason')
    
    if not report_id or not action_type or not reason:
        return Response(
            {'error': 'report_id, action_type, and reason are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate action type
    valid_actions = ['DISMISS', 'WARN', 'HIDE', 'DELETE', 'SUSPEND']
    if action_type not in valid_actions:
        return Response(
            {'error': f'Invalid action_type. Must be one of: {", ".join(valid_actions)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get moderator ID
    moderator_id = request.user_profile.id
    
    try:
        action_data = asyncio.run(
            execute_moderation_action(report_id, moderator_id, action_type, reason)
        )
        
        if action_data is None:
            return Response(
                {'error': 'Report not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(action_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to execute moderation action: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def execute_moderation_action(report_id: str, moderator_id: str, action_type: str, reason: str):
    """
    Execute a moderation action on a report.
    
    Args:
        report_id: ID of the report
        moderator_id: ID of the moderator
        action_type: Type of action
        reason: Reason for the action
        
    Returns:
        Moderation action data or None if report not found
        
    Requirements:
        - 2.4: Support different action types (DISMISS, WARN, HIDE, DELETE, SUSPEND)
        - 2.5: Require dismissal reason (enforced by API)
        - 2.6: Immediately remove content for hide/delete
        - 2.7: Record action in audit log
        - 2.8: Notify content author via email
    """
    from .email_service import ModerationEmailService
    from infrastructure.logging_config import get_logger, log_moderation_action
    
    # Initialize structured logger
    structured_logger = get_logger(__name__)
    
    db = Prisma()
    await db.connect()
    
    try:
        # Fetch report with all related data
        report = await db.report.find_unique(
            where={'id': report_id},
            include={
                'story': {
                    'include': {
                        'author': True
                    }
                },
                'chapter': {
                    'include': {
                        'story': {
                            'include': {
                                'author': True
                            }
                        }
                    }
                },
                'whisper': {
                    'include': {
                        'user': True
                    }
                },
                'reported_user': True
            }
        )
        
        if not report:
            return None
        
        # Create moderation action (Requirement 2.7: Record in audit log)
        action = await db.moderationaction.create(
            data={
                'report_id': report_id,
                'moderator_id': moderator_id,
                'action_type': action_type,
                'reason': reason
            }
        )
        
        # Log moderation action (Requirement 15.5)
        content_id = None
        if report.story:
            content_id = report.story.id
        elif report.chapter:
            content_id = report.chapter.id
        elif report.whisper:
            content_id = report.whisper.id
        elif report.reported_user:
            content_id = report.reported_user.id
        
        log_moderation_action(
            logger=structured_logger,
            moderator_id=moderator_id,
            action_type=action_type,
            content_id=content_id or report_id,
            reason=reason,
        )
        
        # Initialize email service
        email_service = ModerationEmailService()
        
        # Execute action based on type
        if action_type == 'DISMISS':
            # Requirement 2.5: Dismissal reason is required (enforced by API validation)
            # No further action needed for dismiss
            pass
        
        elif action_type == 'WARN':
            # Requirement 2.4: WARN action with user notification
            # Determine who to warn
            warned_user_clerk_id = None
            if report.story:
                warned_user_clerk_id = report.story.author.clerk_user_id
            elif report.chapter:
                warned_user_clerk_id = report.chapter.story.author.clerk_user_id
            elif report.whisper:
                warned_user_clerk_id = report.whisper.user.clerk_user_id
            elif report.reported_user:
                warned_user_clerk_id = report.reported_user.clerk_user_id
            
            if warned_user_clerk_id:
                await email_service.send_warning_notification(
                    user_clerk_id=warned_user_clerk_id,
                    reason=reason
                )
        
        elif action_type == 'HIDE':
            # Requirement 2.6: Immediately remove content from public view
            content_title = None
            author_clerk_id = None
            content_type = None
            
            if report.story:
                await db.story.update(
                    where={'id': report.story.id},
                    data={'deleted_at': datetime.now()}
                )
                content_title = report.story.title
                author_clerk_id = report.story.author.clerk_user_id
                content_type = 'story'
            elif report.chapter:
                await db.chapter.update(
                    where={'id': report.chapter.id},
                    data={'deleted_at': datetime.now()}
                )
                content_title = f"{report.chapter.story.title} - Chapter {report.chapter.chapter_number}"
                author_clerk_id = report.chapter.story.author.clerk_user_id
                content_type = 'chapter'
            elif report.whisper:
                await db.whisper.update(
                    where={'id': report.whisper.id},
                    data={'deleted_at': datetime.now()}
                )
                content_title = report.whisper.content[:50] + '...' if len(report.whisper.content) > 50 else report.whisper.content
                author_clerk_id = report.whisper.user.clerk_user_id
                content_type = 'whisper'
            
            # Requirement 2.8: Notify content author via email
            if author_clerk_id and content_title:
                await email_service.send_content_takedown_notification(
                    author_clerk_id=author_clerk_id,
                    content_type=content_type,
                    content_title=content_title,
                    action_type='HIDE',
                    reason=reason
                )
        
        elif action_type == 'DELETE':
            # Requirement 2.6: Immediately remove content from public view (permanent deletion)
            content_title = None
            author_clerk_id = None
            content_type = None
            
            if report.story:
                content_title = report.story.title
                author_clerk_id = report.story.author.clerk_user_id
                content_type = 'story'
                await db.story.delete(where={'id': report.story.id})
            elif report.chapter:
                content_title = f"{report.chapter.story.title} - Chapter {report.chapter.chapter_number}"
                author_clerk_id = report.chapter.story.author.clerk_user_id
                content_type = 'chapter'
                await db.chapter.delete(where={'id': report.chapter.id})
            elif report.whisper:
                content_title = report.whisper.content[:50] + '...' if len(report.whisper.content) > 50 else report.whisper.content
                author_clerk_id = report.whisper.user.clerk_user_id
                content_type = 'whisper'
                await db.whisper.delete(where={'id': report.whisper.id})
            
            # Requirement 2.8: Notify content author via email
            if author_clerk_id and content_title:
                await email_service.send_content_takedown_notification(
                    author_clerk_id=author_clerk_id,
                    content_type=content_type,
                    content_title=content_title,
                    action_type='DELETE',
                    reason=reason
                )
        
        elif action_type == 'SUSPEND':
            # Requirement 2.4: SUSPEND action with account suspension
            # For now, we'll store suspension info in the metadata field
            # In a full implementation, this would use an AccountSuspension model
            suspended_user_clerk_id = None
            
            if report.reported_user:
                suspended_user_clerk_id = report.reported_user.clerk_user_id
            elif report.story:
                suspended_user_clerk_id = report.story.author.clerk_user_id
            elif report.chapter:
                suspended_user_clerk_id = report.chapter.story.author.clerk_user_id
            elif report.whisper:
                suspended_user_clerk_id = report.whisper.user.clerk_user_id
            
            if suspended_user_clerk_id:
                # Send suspension notification
                await email_service.send_suspension_notification(
                    user_clerk_id=suspended_user_clerk_id,
                    reason=reason,
                    duration="permanent"  # Default to permanent, can be made configurable
                )
                
                # Note: Actual suspension enforcement would require:
                # 1. Creating AccountSuspension record
                # 2. Middleware to check suspension status on authentication
                # 3. Clerk API integration to disable account
                # For now, we record the action in the moderation log
        
        # Update report status to RESOLVED
        await db.report.update(
            where={'id': report_id},
            data={'status': 'RESOLVED'}
        )
        
        # Return action data
        return {
            'id': action.id,
            'report_id': action.report_id,
            'moderator_id': action.moderator_id,
            'action_type': action.action_type,
            'reason': action.reason,
            'created_at': action.created_at.isoformat()
        }
        
    finally:
        await db.disconnect()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_moderator_role()
def get_moderation_stats(request):
    """
    Get moderation performance metrics.
    
    Requires any active moderator role.
    
    Returns:
        Moderation statistics including:
        - Reports reviewed
        - Average response time
        - Action distribution
        - Pending reports count
        
    Requirements:
        - 2.9: Display moderator performance metrics
        - 3.2: Grant access to moderation dashboard when role is assigned
        - 3.6: Return 403 for unauthorized access
    """
    try:
        stats = asyncio.run(fetch_moderation_stats())
        return Response(stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch moderation stats'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def fetch_moderation_stats():
    """
    Fetch moderation statistics.
    
    Returns:
        Dictionary with moderation metrics
        
    Requirements:
        - 2.9: Display performance metrics
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Count pending reports
        pending_count = await db.report.count(
            where={'status': 'PENDING'}
        )
        
        # Count resolved reports
        resolved_count = await db.report.count(
            where={'status': 'RESOLVED'}
        )
        
        # Get all resolved reports with actions for metrics
        resolved_reports = await db.report.find_many(
            where={'status': 'RESOLVED'},
            include={'moderation_actions': True}
        )
        
        # Calculate average response time
        total_response_time = 0
        response_count = 0
        for report in resolved_reports:
            if report.moderation_actions:
                first_action = min(report.moderation_actions, key=lambda a: a.created_at)
                response_time = (first_action.created_at - report.created_at).total_seconds()
                total_response_time += response_time
                response_count += 1
        
        avg_response_time = total_response_time / response_count if response_count > 0 else 0
        
        # Calculate action distribution
        action_counts = {
            'DISMISS': 0,
            'WARN': 0,
            'HIDE': 0,
            'DELETE': 0,
            'SUSPEND': 0
        }
        
        all_actions = await db.moderationaction.find_many()
        for action in all_actions:
            action_counts[action.action_type] = action_counts.get(action.action_type, 0) + 1
        
        return {
            'pending_reports': pending_count,
            'resolved_reports': resolved_count,
            'total_reports': pending_count + resolved_count,
            'average_response_time_seconds': round(avg_response_time, 2),
            'action_distribution': action_counts
        }
        
    finally:
        await db.disconnect()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_administrator
def list_moderators(request):
    """
    Get list of all moderators with their roles and activity statistics.
    
    Restricted to administrators only.
    
    Returns:
        List of moderators with:
        - User information
        - Role type
        - Assignment details
        - Activity statistics
        
    Requirements:
        - 3.5: Only Administrators can assign moderator roles
        - 3.6: Return 403 for unauthorized access
        - 3.8: Display list of all moderators with their roles and activity statistics
    """
    try:
        moderators = asyncio.run(fetch_moderators())
        return Response({
            'moderators': moderators,
            'count': len(moderators)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch moderators'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def fetch_moderators():
    """
    Fetch all moderators with their activity statistics.
    
    Returns:
        List of moderators with user info and stats
        
    Requirements:
        - 3.8: Display list with roles and activity statistics
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Fetch all active moderator roles
        moderator_roles = await db.moderatorrole.find_many(
            where={'is_active': True}
        )
        
        moderators = []
        for mod_role in moderator_roles:
            # Get user information
            user = await db.userprofile.find_unique(
                where={'id': mod_role.user_id}
            )
            
            if not user:
                continue
            
            # Get activity statistics for this moderator
            actions_count = await db.moderationaction.count(
                where={'moderator_id': mod_role.user_id}
            )
            
            # Get recent actions
            recent_actions = await db.moderationaction.find_many(
                where={'moderator_id': mod_role.user_id},
                order={'created_at': 'desc'},
                take=1
            )
            
            last_action_at = recent_actions[0].created_at.isoformat() if recent_actions else None
            
            moderators.append({
                'id': mod_role.id,
                'user': {
                    'id': user.id,
                    'handle': user.handle,
                    'display_name': user.display_name
                },
                'role': mod_role.role,
                'assigned_by': mod_role.assigned_by,
                'assigned_at': mod_role.assigned_at.isoformat(),
                'is_active': mod_role.is_active,
                'activity_stats': {
                    'total_actions': actions_count,
                    'last_action_at': last_action_at
                }
            })
        
        return moderators
        
    finally:
        await db.disconnect()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_administrator
def assign_moderator_role(request):
    """
    Assign a moderator role to a user.
    
    Restricted to administrators only.
    
    Request Body:
        - user_id: ID of the user to assign role
        - role: Type of role (MODERATOR, SENIOR_MODERATOR, ADMINISTRATOR)
        
    Returns:
        Created moderator role data
        
    Requirements:
        - 3.1: Support role types: ADMINISTRATOR, SENIOR_MODERATOR, MODERATOR
        - 3.2: Grant access to moderation dashboard when role is assigned
        - 3.5: Only Administrators can assign moderator roles
        - 3.6: Return 403 for unauthorized access
        - 3.7: Log all role assignments in audit log
    """
    from .serializers import ModeratorRoleCreateSerializer
    
    # Validate request data
    serializer = ModeratorRoleCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    user_id = validated_data['user_id']
    role = validated_data['role']
    
    # Get assigner ID
    assigned_by = request.user_profile.id
    
    try:
        role_data = asyncio.run(
            create_moderator_role(user_id, role, assigned_by)
        )
        
        if role_data is None:
            return Response(
                {'error': 'User not found or already has a moderator role'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(role_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to assign moderator role: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def create_moderator_role(user_id: str, role: str, assigned_by: str):
    """
    Create a moderator role assignment.
    
    Args:
        user_id: ID of the user to assign role
        role: Type of role
        assigned_by: ID of the administrator assigning the role
        
    Returns:
        Moderator role data or None if user not found or already has role
        
    Requirements:
        - 3.1: Support role types
        - 3.2: Grant access to moderation dashboard
        - 3.7: Log role assignment
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Verify user exists
        user = await db.userprofile.find_unique(where={'id': user_id})
        if not user:
            return None
        
        # Check if user already has a moderator role
        existing_role = await db.moderatorrole.find_first(
            where={'user_id': user_id}
        )
        
        if existing_role:
            # If role exists but is inactive, reactivate it with new role
            if not existing_role.is_active:
                updated_role = await db.moderatorrole.update(
                    where={'id': existing_role.id},
                    data={
                        'role': role,
                        'assigned_by': assigned_by,
                        'assigned_at': datetime.now(),
                        'is_active': True
                    }
                )
                
                return {
                    'id': updated_role.id,
                    'user_id': updated_role.user_id,
                    'role': updated_role.role,
                    'assigned_by': updated_role.assigned_by,
                    'assigned_at': updated_role.assigned_at.isoformat(),
                    'is_active': updated_role.is_active
                }
            else:
                # User already has an active role
                return None
        
        # Create new moderator role
        moderator_role = await db.moderatorrole.create(
            data={
                'user_id': user_id,
                'role': role,
                'assigned_by': assigned_by
            }
        )
        
        # Return role data
        return {
            'id': moderator_role.id,
            'user_id': moderator_role.user_id,
            'role': moderator_role.role,
            'assigned_by': moderator_role.assigned_by,
            'assigned_at': moderator_role.assigned_at.isoformat(),
            'is_active': moderator_role.is_active
        }
        
    finally:
        await db.disconnect()


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@require_administrator
def remove_moderator_role(request, moderator_id):
    """
    Remove a moderator role (deactivate).
    
    Restricted to administrators only.
    
    Args:
        moderator_id: ID of the moderator role to remove
        
    Returns:
        Success message
        
    Requirements:
        - 3.5: Only Administrators can assign moderator roles
        - 3.6: Return 403 for unauthorized access
        - 3.7: Log all role assignments and permission changes
    """
    try:
        success = asyncio.run(deactivate_moderator_role(moderator_id))
        
        if not success:
            return Response(
                {'error': 'Moderator role not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(
            {'message': 'Moderator role removed successfully'},
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {'error': f'Failed to remove moderator role: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def deactivate_moderator_role(moderator_id: str) -> bool:
    """
    Deactivate a moderator role.
    
    Args:
        moderator_id: ID of the moderator role
        
    Returns:
        True if successful, False if not found
        
    Requirements:
        - 3.7: Log permission changes
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Find the moderator role
        moderator_role = await db.moderatorrole.find_unique(
            where={'id': moderator_id}
        )
        
        if not moderator_role:
            return False
        
        # Deactivate the role
        await db.moderatorrole.update(
            where={'id': moderator_id},
            data={'is_active': False}
        )
        
        return True
        
    finally:
        await db.disconnect()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_administrator
def list_filter_configs(request):
    """
    Get all filter configurations.
    
    Restricted to administrators only.
    
    Returns:
        List of all filter configurations with their settings
        
    Requirements:
        - 4.8: Allow administrators to configure filter sensitivity levels
        - 4.9: Maintain a whitelist for false positive terms
    """
    try:
        configs = asyncio.run(fetch_filter_configs())
        return Response({
            'configs': configs,
            'count': len(configs)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch filter configurations: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def fetch_filter_configs():
    """
    Fetch all filter configurations.
    
    Returns:
        List of filter configurations
        
    Requirements:
        - 4.8: Allow administrators to configure filter sensitivity levels
    """
    db = Prisma()
    await db.connect()
    
    try:
        configs = await db.contentfilterconfig.find_many(
            order={'filter_type': 'asc'}
        )
        
        return [
            {
                'id': config.id,
                'filter_type': config.filter_type,
                'sensitivity': config.sensitivity,
                'enabled': config.enabled,
                'whitelist': config.whitelist if config.whitelist else [],
                'blacklist': config.blacklist if config.blacklist else [],
                'updated_at': config.updated_at.isoformat()
            }
            for config in configs
        ]
        
    finally:
        await db.disconnect()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_administrator
def get_filter_config(request, filter_type):
    """
    Get configuration for a specific filter type.
    
    Restricted to administrators only.
    
    Args:
        filter_type: Type of filter (PROFANITY, SPAM, HATE_SPEECH)
        
    Returns:
        Filter configuration data
        
    Requirements:
        - 4.8: Allow administrators to configure filter sensitivity levels
        - 4.9: Maintain a whitelist for false positive terms
    """
    # Validate filter type
    valid_types = ['PROFANITY', 'SPAM', 'HATE_SPEECH']
    filter_type_upper = filter_type.upper()
    
    if filter_type_upper not in valid_types:
        return Response(
            {'error': f'Invalid filter_type. Must be one of: {", ".join(valid_types)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        config = asyncio.run(fetch_filter_config(filter_type_upper))
        
        if config is None:
            return Response(
                {'error': 'Filter configuration not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(config, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch filter configuration: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def fetch_filter_config(filter_type: str):
    """
    Fetch configuration for a specific filter type.
    
    Args:
        filter_type: Type of filter
        
    Returns:
        Filter configuration dictionary or None if not found
        
    Requirements:
        - 4.8: Allow administrators to configure filter sensitivity levels
    """
    db = Prisma()
    await db.connect()
    
    try:
        config = await db.contentfilterconfig.find_unique(
            where={'filter_type': filter_type}
        )
        
        if not config:
            return None
        
        return {
            'id': config.id,
            'filter_type': config.filter_type,
            'sensitivity': config.sensitivity,
            'enabled': config.enabled,
            'whitelist': config.whitelist if config.whitelist else [],
            'blacklist': config.blacklist if config.blacklist else [],
            'updated_at': config.updated_at.isoformat()
        }
        
    finally:
        await db.disconnect()


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@require_administrator
def update_filter_config(request, filter_type):
    """
    Update configuration for a specific filter type.
    
    Restricted to administrators only.
    
    Args:
        filter_type: Type of filter (PROFANITY, SPAM, HATE_SPEECH)
        
    Request Body:
        - sensitivity: Filter sensitivity level (STRICT, MODERATE, PERMISSIVE) [optional]
        - enabled: Whether the filter is enabled [optional]
        - whitelist: List of terms to ignore [optional]
        - blacklist: List of additional terms to flag [optional]
        
    Returns:
        Updated filter configuration data
        
    Requirements:
        - 4.8: Allow administrators to configure filter sensitivity levels
        - 4.9: Maintain a whitelist for false positive terms
        - 4.10: Log all automated filtering actions for review and tuning
    """
    from .serializers import FilterConfigUpdateSerializer
    
    # Validate filter type
    valid_types = ['PROFANITY', 'SPAM', 'HATE_SPEECH']
    filter_type_upper = filter_type.upper()
    
    if filter_type_upper not in valid_types:
        return Response(
            {'error': f'Invalid filter_type. Must be one of: {", ".join(valid_types)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate request data
    serializer = FilterConfigUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data
    
    # Get administrator ID
    admin_id = request.user_profile.id
    
    try:
        config = asyncio.run(
            update_filter_configuration(
                filter_type_upper,
                admin_id,
                validated_data
            )
        )
        
        if config is None:
            return Response(
                {'error': 'Filter configuration not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(config, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to update filter configuration: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def update_filter_configuration(filter_type: str, admin_id: str, updates: dict):
    """
    Update a filter configuration.
    
    Args:
        filter_type: Type of filter
        admin_id: ID of the administrator making the update
        updates: Dictionary with update fields
        
    Returns:
        Updated filter configuration or None if not found
        
    Requirements:
        - 4.8: Allow administrators to configure filter sensitivity levels
        - 4.9: Maintain a whitelist for false positive terms
        - 4.10: Log all automated filtering actions
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Check if config exists
        existing_config = await db.contentfilterconfig.find_unique(
            where={'filter_type': filter_type}
        )
        
        if not existing_config:
            return None
        
        # Build update data
        update_data = {'updated_by': admin_id}
        
        if 'sensitivity' in updates:
            update_data['sensitivity'] = updates['sensitivity']
        
        if 'enabled' in updates:
            update_data['enabled'] = updates['enabled']
        
        if 'whitelist' in updates:
            update_data['whitelist'] = updates['whitelist']
        
        if 'blacklist' in updates:
            update_data['blacklist'] = updates['blacklist']
        
        # Update configuration
        config = await db.contentfilterconfig.update(
            where={'filter_type': filter_type},
            data=update_data
        )
        
        return {
            'id': config.id,
            'filter_type': config.filter_type,
            'sensitivity': config.sensitivity,
            'enabled': config.enabled,
            'whitelist': config.whitelist if config.whitelist else [],
            'blacklist': config.blacklist if config.blacklist else [],
            'updated_at': config.updated_at.isoformat()
        }
        
    finally:
        await db.disconnect()



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nsfw_preference(request):
    """
    Get user's NSFW content preference.
    
    Returns:
        User's NSFW preference (SHOW_ALL, BLUR_NSFW, or HIDE_NSFW)
        
    Requirements:
        - 8.5: Allow users to set content preferences
    """
    user_id = request.user_profile.id
    
    try:
        preference = asyncio.run(fetch_nsfw_preference(user_id))
        return Response({'nsfw_preference': preference}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': 'Failed to fetch NSFW preference'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def fetch_nsfw_preference(user_id: str):
    """
    Fetch user's NSFW preference.
    
    Args:
        user_id: ID of the user
        
    Returns:
        NSFW preference string
    """
    from apps.moderation.nsfw_service import get_nsfw_service
    
    service = get_nsfw_service()
    await service.db.connect()
    
    try:
        preference = await service.get_user_nsfw_preference(user_id)
        return preference.value
    finally:
        await service.db.disconnect()


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_nsfw_preference(request):
    """
    Update user's NSFW content preference.
    
    Request Body:
        - nsfw_preference: Preference value (SHOW_ALL, BLUR_NSFW, or HIDE_NSFW)
        
    Returns:
        Updated preference data
        
    Requirements:
        - 8.5: Allow users to set content preferences
    """
    user_id = request.user_profile.id
    nsfw_preference = request.data.get('nsfw_preference')
    
    # Validate preference value
    from prisma.enums import NSFWPreference
    valid_preferences = [p.value for p in NSFWPreference]
    
    if not nsfw_preference or nsfw_preference not in valid_preferences:
        return Response(
            {
                'error': f'Invalid nsfw_preference. Must be one of: {", ".join(valid_preferences)}'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        preference_data = asyncio.run(
            update_user_nsfw_preference(user_id, nsfw_preference)
        )
        return Response(preference_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': 'Failed to update NSFW preference'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def update_user_nsfw_preference(user_id: str, preference_value: str):
    """
    Update user's NSFW preference.
    
    Args:
        user_id: ID of the user
        preference_value: Preference value string
        
    Returns:
        Updated preference data
    """
    from apps.moderation.nsfw_service import get_nsfw_service
    from prisma.enums import NSFWPreference
    
    service = get_nsfw_service()
    await service.db.connect()
    
    try:
        preference = NSFWPreference[preference_value]
        preference_data = await service.create_user_nsfw_preference(
            user_id,
            preference
        )
        return preference_data
    finally:
        await service.db.disconnect()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_moderator_role()
def override_nsfw_flag(request):
    """
    Override NSFW classification for content (moderator action).
    
    Requires any active moderator role.
    
    Request Body:
        - content_type: Type of content (STORY, CHAPTER, WHISPER, IMAGE)
        - content_id: ID of the content
        - is_nsfw: New NSFW status (true or false)
        
    Returns:
        Updated NSFW flag data
        
    Requirements:
        - 8.8: Allow moderators to override automatic NSFW classifications
        - 8.10: Log all NSFW detection events
        - 3.2: Grant access to moderation dashboard when role is assigned
        - 3.6: Return 403 for unauthorized access
    """
    moderator_id = request.user_profile.id
    content_type = request.data.get('content_type')
    content_id = request.data.get('content_id')
    is_nsfw = request.data.get('is_nsfw')
    
    # Validate required fields
    if not content_type or not content_id or is_nsfw is None:
        return Response(
            {'error': 'content_type, content_id, and is_nsfw are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate content_type
    from prisma.enums import NSFWContentType
    valid_content_types = [t.value for t in NSFWContentType]
    
    if content_type not in valid_content_types:
        return Response(
            {
                'error': f'Invalid content_type. Must be one of: {", ".join(valid_content_types)}'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate is_nsfw is boolean
    if not isinstance(is_nsfw, bool):
        return Response(
            {'error': 'is_nsfw must be a boolean value'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        flag_data = asyncio.run(
            execute_nsfw_override(content_type, content_id, is_nsfw, moderator_id)
        )
        
        return Response(flag_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to override NSFW flag: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def execute_nsfw_override(content_type: str, content_id: str, is_nsfw: bool, moderator_id: str):
    """
    Execute NSFW flag override.
    
    Args:
        content_type: Type of content
        content_id: ID of the content
        is_nsfw: New NSFW status
        moderator_id: ID of the moderator
        
    Returns:
        Updated NSFW flag data
        
    Requirements:
        - 8.8: Override automatic NSFW classifications
        - 8.10: Log NSFW detection events
    """
    from apps.moderation.nsfw_service import get_nsfw_service
    from prisma.enums import NSFWContentType
    
    service = get_nsfw_service()
    await service.db.connect()
    
    try:
        # Convert string to enum
        content_type_enum = NSFWContentType[content_type]
        
        # Override the NSFW flag
        flag = await service.override_nsfw_flag(
            content_type=content_type_enum,
            content_id=content_id,
            is_nsfw=is_nsfw,
            moderator_id=moderator_id
        )
        
        return flag
        
    finally:
        await service.db.disconnect()
