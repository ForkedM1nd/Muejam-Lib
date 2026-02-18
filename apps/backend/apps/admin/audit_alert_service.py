"""
Audit Alert Service

Sends alerts to administrators when suspicious patterns are detected in audit logs.

Requirements:
- 32.9: Alert administrators when suspicious patterns are detected
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from apps.notifications.email_service import EmailNotificationService

logger = logging.getLogger(__name__)


class AuditAlertService:
    """Service for sending alerts about suspicious audit log patterns."""
    
    @staticmethod
    async def send_suspicious_pattern_alert(
        patterns: List[Dict[str, Any]],
        admin_emails: List[str]
    ) -> bool:
        """
        Send alert email to administrators about suspicious patterns.
        
        Args:
            patterns: List of detected suspicious patterns
            admin_emails: List of administrator email addresses
            
        Returns:
            True if alert was sent successfully, False otherwise
            
        Requirements: 32.9
        """
        if not patterns:
            logger.info("No suspicious patterns to alert about")
            return True
        
        if not admin_emails:
            logger.warning("No admin emails configured for alerts")
            return False
        
        try:
            # Group patterns by severity
            high_severity = [p for p in patterns if p.get('severity') == 'high']
            medium_severity = [p for p in patterns if p.get('severity') == 'medium']
            low_severity = [p for p in patterns if p.get('severity') == 'low']
            
            # Build email content
            subject = f"🚨 Security Alert: {len(patterns)} Suspicious Pattern(s) Detected"
            
            html_content = AuditAlertService._build_alert_email_html(
                high_severity,
                medium_severity,
                low_severity
            )
            
            # Send email to all admins
            email_service = EmailNotificationService()
            for admin_email in admin_emails:
                await email_service.send_email(
                    to_email=admin_email,
                    subject=subject,
                    html_content=html_content
                )
            
            logger.info(
                f"Sent suspicious pattern alert to {len(admin_emails)} administrators. "
                f"Patterns: {len(high_severity)} high, {len(medium_severity)} medium, "
                f"{len(low_severity)} low severity"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send suspicious pattern alert: {str(e)}")
            return False
    
    @staticmethod
    def _build_alert_email_html(
        high_severity: List[Dict[str, Any]],
        medium_severity: List[Dict[str, Any]],
        low_severity: List[Dict[str, Any]]
    ) -> str:
        """Build HTML content for alert email."""
        
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background-color: #dc3545; color: white; padding: 20px; }
                .content { padding: 20px; }
                .pattern { 
                    border-left: 4px solid #ccc; 
                    padding: 15px; 
                    margin: 15px 0; 
                    background-color: #f8f9fa;
                }
                .pattern.high { border-left-color: #dc3545; }
                .pattern.medium { border-left-color: #ffc107; }
                .pattern.low { border-left-color: #17a2b8; }
                .severity { 
                    display: inline-block; 
                    padding: 3px 8px; 
                    border-radius: 3px; 
                    font-size: 12px; 
                    font-weight: bold;
                }
                .severity.high { background-color: #dc3545; color: white; }
                .severity.medium { background-color: #ffc107; color: #333; }
                .severity.low { background-color: #17a2b8; color: white; }
                .details { 
                    margin-top: 10px; 
                    padding: 10px; 
                    background-color: white; 
                    border-radius: 3px;
                    font-size: 14px;
                }
                .footer { 
                    margin-top: 30px; 
                    padding: 20px; 
                    background-color: #f8f9fa; 
                    border-top: 1px solid #dee2e6;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚨 Security Alert: Suspicious Activity Detected</h1>
                <p>Automated audit log analysis has detected suspicious patterns that require your attention.</p>
            </div>
            <div class="content">
        """
        
        # Add high severity patterns
        if high_severity:
            html += f"""
                <h2>🔴 High Severity Patterns ({len(high_severity)})</h2>
                <p>These patterns require immediate investigation:</p>
            """
            for pattern in high_severity:
                html += AuditAlertService._format_pattern_html(pattern, 'high')
        
        # Add medium severity patterns
        if medium_severity:
            html += f"""
                <h2>🟡 Medium Severity Patterns ({len(medium_severity)})</h2>
                <p>These patterns should be reviewed:</p>
            """
            for pattern in medium_severity:
                html += AuditAlertService._format_pattern_html(pattern, 'medium')
        
        # Add low severity patterns
        if low_severity:
            html += f"""
                <h2>🔵 Low Severity Patterns ({len(low_severity)})</h2>
                <p>These patterns are informational:</p>
            """
            for pattern in low_severity:
                html += AuditAlertService._format_pattern_html(pattern, 'low')
        
        html += """
            </div>
            <div class="footer">
                <p><strong>What to do:</strong></p>
                <ol>
                    <li>Review the patterns above and investigate any suspicious activity</li>
                    <li>Check the full audit logs for additional context</li>
                    <li>Take appropriate action (e.g., suspend accounts, reset passwords, block IPs)</li>
                    <li>Document your findings and actions taken</li>
                </ol>
                <p><em>This is an automated alert from the MueJam Library security monitoring system.</em></p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    @staticmethod
    def _format_pattern_html(pattern: Dict[str, Any], severity: str) -> str:
        """Format a single pattern as HTML."""
        pattern_type = pattern.get('type', 'unknown')
        description = pattern.get('description', 'No description')
        details = pattern.get('details', {})
        
        html = f"""
        <div class="pattern {severity}">
            <div>
                <span class="severity {severity}">{severity.upper()}</span>
                <strong>{AuditAlertService._format_pattern_type(pattern_type)}</strong>
            </div>
            <p>{description}</p>
        """
        
        if details:
            html += '<div class="details">'
            html += '<strong>Details:</strong><br>'
            for key, value in details.items():
                formatted_key = key.replace('_', ' ').title()
                if isinstance(value, list):
                    value = ', '.join(str(v) for v in value)
                html += f'<strong>{formatted_key}:</strong> {value}<br>'
            html += '</div>'
        
        html += '</div>'
        
        return html
    
    @staticmethod
    def _format_pattern_type(pattern_type: str) -> str:
        """Format pattern type for display."""
        type_names = {
            'multiple_failed_logins': 'Multiple Failed Login Attempts',
            'multiple_ip_access': 'Access from Multiple IP Addresses',
            'rapid_admin_actions': 'Rapid Administrative Actions',
            'bulk_data_exports': 'Bulk Data Export Requests'
        }
        return type_names.get(pattern_type, pattern_type.replace('_', ' ').title())
    
    @staticmethod
    async def check_and_alert(admin_emails: List[str], hours: int = 24) -> Dict[str, Any]:
        """
        Check for suspicious patterns and send alerts if found.
        
        This method can be called periodically (e.g., via cron job or Celery task)
        to automatically monitor audit logs and alert administrators.
        
        Args:
            admin_emails: List of administrator email addresses
            hours: Number of hours to analyze (default: 24)
            
        Returns:
            Dictionary with check results
            
        Requirements: 32.9
        """
        from datetime import timedelta
        from prisma import Prisma
        from prisma.enums import AuditActionType
        from apps.admin.audit_log_views import (
            _detect_failed_logins,
            _detect_unusual_access,
            _detect_bulk_exports
        )
        
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            db = Prisma()
            await db.connect()
            
            try:
                patterns = []
                
                # Detect all suspicious patterns
                failed_logins = await _detect_failed_logins(db, start_time)
                if failed_logins:
                    patterns.extend(failed_logins)
                
                unusual_access = await _detect_unusual_access(db, start_time)
                if unusual_access:
                    patterns.extend(unusual_access)
                
                bulk_exports = await _detect_bulk_exports(db, start_time)
                if bulk_exports:
                    patterns.extend(bulk_exports)
                
                # Send alert if patterns found
                if patterns:
                    alert_sent = await AuditAlertService.send_suspicious_pattern_alert(
                        patterns,
                        admin_emails
                    )
                    
                    return {
                        'patterns_found': len(patterns),
                        'alert_sent': alert_sent,
                        'patterns': patterns
                    }
                else:
                    logger.info(f"No suspicious patterns detected in last {hours} hours")
                    return {
                        'patterns_found': 0,
                        'alert_sent': False,
                        'patterns': []
                    }
                    
            finally:
                await db.disconnect()
                
        except Exception as e:
            logger.error(f"Error checking for suspicious patterns: {str(e)}")
            return {
                'error': str(e),
                'patterns_found': 0,
                'alert_sent': False
            }
