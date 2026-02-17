"""Views for content moderation system."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from prisma import Prisma
from datetime import datetime
from .serializers import ReportCreateSerializer, ReportSerializer
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
