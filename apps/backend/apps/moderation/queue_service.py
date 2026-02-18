"""Moderation queue service with priority calculation."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from prisma import Prisma


class ModerationQueueService:
    """
    Service for managing the moderation queue with priority-based sorting.
    
    Requirements:
        - 2.1: Display all pending reports in moderation queue
        - 2.2: Sort reports by priority and creation date
    """
    
    def __init__(self):
        self.db = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.db = Prisma()
        await self.db.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.db:
            await self.db.disconnect()
    
    async def get_queue(self) -> List[Dict[str, Any]]:
        """
        Get all pending reports sorted by priority and creation date.
        
        Returns:
            List of reports with priority scores, sorted by priority (desc) and created_at (asc)
            
        Requirements:
            - 2.1: Display all pending reports
            - 2.2: Sort by priority and creation date
        """
        # Fetch all pending reports with related data
        reports = await self.db.report.find_many(
            where={'status': 'PENDING'},
            include={
                'reporter': True,
                'reported_user': True,
                'story': True,
                'chapter': True,
                'whisper': True
            }
        )
        
        # Calculate priority for each report
        reports_with_priority = []
        for report in reports:
            priority_score = await self._calculate_priority(report)
            
            # Determine content type
            content_type = None
            content_id = None
            if report.story_id:
                content_type = 'story'
                content_id = report.story_id
            elif report.chapter_id:
                content_type = 'chapter'
                content_id = report.chapter_id
            elif report.whisper_id:
                content_type = 'whisper'
                content_id = report.whisper_id
            elif report.reported_user_id:
                content_type = 'user'
                content_id = report.reported_user_id
            
            reports_with_priority.append({
                'id': report.id,
                'reporter_id': report.reporter_id,
                'reporter_handle': report.reporter.handle if report.reporter else None,
                'content_type': content_type,
                'content_id': content_id,
                'reason': report.reason,
                'status': report.status,
                'created_at': report.created_at.isoformat(),
                'priority_score': priority_score,
                'priority_level': self._get_priority_level(priority_score)
            })
        
        # Sort by priority (descending) then by creation date (ascending - older first)
        reports_with_priority.sort(
            key=lambda x: (-x['priority_score'], x['created_at'])
        )
        
        return reports_with_priority
    
    async def _calculate_priority(self, report) -> float:
        """
        Calculate priority score for a report based on multiple factors.
        
        Priority Algorithm:
        - Duplicate reports: +10 per duplicate
        - Automated flags: +50 if automated flag exists
        - Reporter accuracy: +20 * accuracy (0-1)
        - Content type: +30 for user reports
        - Age: +2 per hour (capped at 100)
        
        Args:
            report: Report object with related data
            
        Returns:
            Priority score (float)
            
        Requirements:
            - 2.2: Priority algorithm based on multiple factors
        """
        priority_score = 0.0
        
        # 1. Base priority by duplicate report count
        duplicate_count = await self._count_duplicate_reports(report)
        priority_score += duplicate_count * 10
        
        # 2. Automated detection flags (placeholder - will be implemented in Phase 3)
        # For now, we'll check if there are any automated flags in the future
        has_automated_flag = False  # TODO: Implement in Phase 3
        if has_automated_flag:
            priority_score += 50
        
        # 3. Reporter reputation/accuracy
        reporter_accuracy = await self._get_reporter_accuracy(report.reporter_id)
        priority_score += reporter_accuracy * 20
        
        # 4. Content type priority (user reports are higher priority)
        if report.reported_user_id:
            priority_score += 30
        
        # 5. Age of report (older = higher priority)
        now = datetime.now(timezone.utc)
        hours_old = (now - report.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
        priority_score += min(hours_old * 2, 100)
        
        return priority_score
    
    async def _count_duplicate_reports(self, report) -> int:
        """
        Count duplicate reports for the same content.
        
        Args:
            report: Report object
            
        Returns:
            Number of duplicate reports (excluding the current one)
        """
        where_clause = {
            'status': 'PENDING',
            'id': {'not': report.id}
        }
        
        # Add content-specific filter
        if report.story_id:
            where_clause['story_id'] = report.story_id
        elif report.chapter_id:
            where_clause['chapter_id'] = report.chapter_id
        elif report.whisper_id:
            where_clause['whisper_id'] = report.whisper_id
        elif report.reported_user_id:
            where_clause['reported_user_id'] = report.reported_user_id
        else:
            return 0
        
        count = await self.db.report.count(where=where_clause)
        return count
    
    async def _get_reporter_accuracy(self, reporter_id: str) -> float:
        """
        Calculate reporter accuracy based on historical reports.
        
        Accuracy = (valid reports) / (total resolved reports)
        Valid reports are those that resulted in action (not dismissed)
        
        Args:
            reporter_id: ID of the reporter
            
        Returns:
            Accuracy score between 0 and 1
        """
        # Get all resolved reports from this reporter
        resolved_reports = await self.db.report.find_many(
            where={
                'reporter_id': reporter_id,
                'status': 'RESOLVED'
            },
            include={
                'moderation_actions': True
            }
        )
        
        if not resolved_reports:
            # New reporter - give neutral score
            return 0.5
        
        # Count valid reports (those with non-DISMISS actions)
        valid_count = 0
        for report in resolved_reports:
            if report.moderation_actions:
                # Check if any action was not DISMISS
                has_action = any(
                    action.action_type != 'DISMISS' 
                    for action in report.moderation_actions
                )
                if has_action:
                    valid_count += 1
        
        accuracy = valid_count / len(resolved_reports)
        return accuracy
    
    def _get_priority_level(self, priority_score: float) -> str:
        """
        Convert priority score to priority level label.
        
        Args:
            priority_score: Calculated priority score
            
        Returns:
            Priority level: 'high', 'medium', or 'low'
        """
        if priority_score >= 100:
            return 'high'
        elif priority_score >= 50:
            return 'medium'
        else:
            return 'low'
