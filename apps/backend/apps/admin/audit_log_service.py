"""
Audit Logging Service

Comprehensive audit logging for compliance, security, and debugging.

Requirements:
- 32.1: Log authentication events
- 32.2: Log moderation actions
- 32.3: Log administrative actions
- 32.4: Log data access for sensitive operations
- 32.5: Include required fields in audit log entries
- 32.6: Store logs in immutable storage
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
from prisma import Prisma, Json
from prisma.enums import AuditActionType, AuditResourceType, AuditResult

logger = logging.getLogger(__name__)


class AuditLogService:
    """Service for recording audit log entries."""
    
    @staticmethod
    async def log_event(
        action_type: AuditActionType,
        user_id: Optional[str] = None,
        resource_type: Optional[AuditResourceType] = None,
        resource_id: Optional[str] = None,
        ip_address: str = "0.0.0.0",
        user_agent: str = "Unknown",
        result: AuditResult = AuditResult.SUCCESS,
        metadata: Optional[Dict[str, Any]] = None
    ) -> dict:
        """
        Log an audit event.
        
        Args:
            action_type: Type of action being logged
            user_id: ID of user performing the action (optional for system actions)
            resource_type: Type of resource being acted upon
            resource_id: ID of the resource
            ip_address: IP address of the request
            user_agent: User agent string
            result: Result of the action (SUCCESS, FAILURE, PARTIAL)
            metadata: Additional context data
            
        Returns:
            Created audit log entry
            
        Requirements: 32.1, 32.2, 32.3, 32.4, 32.5
        """
        db = Prisma()
        await db.connect()
        
        try:
            # Create audit log entry
            # Build data dict, omitting metadata if None
            data = {
                'user_id': user_id,
                'action_type': action_type,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'result': result
            }
            
            # Only include metadata if it has content
            if metadata:
                # Use Prisma's Json type
                data['metadata'] = Json(metadata)
            
            audit_log = await db.auditlog.create(data=data)
            
            logger.info(
                f"Audit log created: {action_type} by user {user_id} "
                f"on {resource_type}:{resource_id} - {result}"
            )
            
            return {
                'id': audit_log.id,
                'user_id': audit_log.user_id,
                'action_type': audit_log.action_type,
                'resource_type': audit_log.resource_type,
                'resource_id': audit_log.resource_id,
                'ip_address': audit_log.ip_address,
                'user_agent': audit_log.user_agent,
                'result': audit_log.result,
                'metadata': audit_log.metadata,
                'created_at': audit_log.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            # Don't raise - audit logging should not break application flow
            return {}
            
        finally:
            await db.disconnect()
    
    # Authentication Events (Requirement 32.1)
    
    @staticmethod
    async def log_login_success(
        user_id: str,
        ip_address: str,
        user_agent: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log successful login."""
        return await AuditLogService.log_event(
            action_type=AuditActionType.LOGIN_SUCCESS,
            user_id=user_id,
            resource_type=AuditResourceType.USER,
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=metadata
        )
    
    @staticmethod
    async def log_login_failed(
        user_id: Optional[str],
        ip_address: str,
        user_agent: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log failed login attempt."""
        meta = {'reason': reason}
        if metadata:
            meta.update(metadata)
        
        return await AuditLogService.log_event(
            action_type=AuditActionType.LOGIN_FAILED,
            user_id=user_id,
            resource_type=AuditResourceType.USER,
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.FAILURE,
            metadata=meta
        )
    
    @staticmethod
    async def log_logout(
        user_id: str,
        ip_address: str,
        user_agent: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log user logout."""
        return await AuditLogService.log_event(
            action_type=AuditActionType.LOGOUT,
            user_id=user_id,
            resource_type=AuditResourceType.USER,
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=metadata
        )
    
    @staticmethod
    async def log_password_change(
        user_id: str,
        ip_address: str,
        user_agent: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log password change."""
        return await AuditLogService.log_event(
            action_type=AuditActionType.PASSWORD_CHANGE,
            user_id=user_id,
            resource_type=AuditResourceType.USER,
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=metadata
        )
    
    @staticmethod
    async def log_2fa_enabled(
        user_id: str,
        ip_address: str,
        user_agent: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log 2FA enabled."""
        return await AuditLogService.log_event(
            action_type=AuditActionType.TWO_FA_ENABLED,
            user_id=user_id,
            resource_type=AuditResourceType.USER,
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=metadata
        )
    
    @staticmethod
    async def log_2fa_disabled(
        user_id: str,
        ip_address: str,
        user_agent: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log 2FA disabled."""
        return await AuditLogService.log_event(
            action_type=AuditActionType.TWO_FA_DISABLED,
            user_id=user_id,
            resource_type=AuditResourceType.USER,
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=metadata
        )
    
    # Moderation Actions (Requirement 32.2)
    
    @staticmethod
    async def log_content_takedown(
        moderator_id: str,
        resource_type: AuditResourceType,
        resource_id: str,
        ip_address: str,
        user_agent: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log content takedown."""
        meta = {'reason': reason}
        if metadata:
            meta.update(metadata)
        
        return await AuditLogService.log_event(
            action_type=AuditActionType.CONTENT_TAKEDOWN,
            user_id=moderator_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=meta
        )
    
    @staticmethod
    async def log_user_suspension(
        moderator_id: str,
        suspended_user_id: str,
        ip_address: str,
        user_agent: str,
        reason: str,
        duration: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log user suspension."""
        meta = dict(metadata) if metadata else {}
        meta['reason'] = reason
        if duration:
            meta['duration'] = duration
        
        return await AuditLogService.log_event(
            action_type=AuditActionType.USER_SUSPENSION,
            user_id=moderator_id,
            resource_type=AuditResourceType.USER,
            resource_id=suspended_user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=meta
        )
    
    @staticmethod
    async def log_report_resolution(
        moderator_id: str,
        report_id: str,
        ip_address: str,
        user_agent: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log report resolution."""
        meta = dict(metadata) if metadata else {}
        meta['action'] = action
        
        return await AuditLogService.log_event(
            action_type=AuditActionType.REPORT_RESOLUTION,
            user_id=moderator_id,
            resource_type=AuditResourceType.REPORT,
            resource_id=report_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=meta
        )
    
    @staticmethod
    async def log_role_assignment(
        admin_id: str,
        target_user_id: str,
        ip_address: str,
        user_agent: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log role assignment."""
        meta = dict(metadata) if metadata else {}
        meta['role'] = role
        
        return await AuditLogService.log_event(
            action_type=AuditActionType.ROLE_ASSIGNMENT,
            user_id=admin_id,
            resource_type=AuditResourceType.USER,
            resource_id=target_user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=meta
        )
    
    # Administrative Actions (Requirement 32.3)
    
    @staticmethod
    async def log_config_change(
        admin_id: str,
        ip_address: str,
        user_agent: str,
        config_key: str,
        old_value: Any,
        new_value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log configuration change."""
        meta = dict(metadata) if metadata else {}
        meta['config_key'] = config_key
        meta['old_value'] = str(old_value)
        meta['new_value'] = str(new_value)
        
        return await AuditLogService.log_event(
            action_type=AuditActionType.CONFIG_CHANGE,
            user_id=admin_id,
            resource_type=AuditResourceType.SYSTEM_CONFIG,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=meta
        )
    
    @staticmethod
    async def log_user_role_change(
        admin_id: str,
        target_user_id: str,
        ip_address: str,
        user_agent: str,
        old_role: str,
        new_role: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log user role change."""
        meta = dict(metadata) if metadata else {}
        meta['old_role'] = old_role
        meta['new_role'] = new_role
        
        return await AuditLogService.log_event(
            action_type=AuditActionType.USER_ROLE_CHANGE,
            user_id=admin_id,
            resource_type=AuditResourceType.USER,
            resource_id=target_user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=meta
        )
    
    @staticmethod
    async def log_system_settings_update(
        admin_id: str,
        ip_address: str,
        user_agent: str,
        setting_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log system settings update."""
        meta = dict(metadata) if metadata else {}
        meta['setting_name'] = setting_name
        
        return await AuditLogService.log_event(
            action_type=AuditActionType.SYSTEM_SETTINGS_UPDATE,
            user_id=admin_id,
            resource_type=AuditResourceType.SYSTEM_CONFIG,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=meta
        )
    
    # Data Access (Requirement 32.4)
    
    @staticmethod
    async def log_data_export_request(
        user_id: str,
        ip_address: str,
        user_agent: str,
        export_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log data export request."""
        return await AuditLogService.log_event(
            action_type=AuditActionType.DATA_EXPORT_REQUEST,
            user_id=user_id,
            resource_type=AuditResourceType.DATA_EXPORT,
            resource_id=export_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=metadata
        )
    
    @staticmethod
    async def log_account_deletion_request(
        user_id: str,
        ip_address: str,
        user_agent: str,
        deletion_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log account deletion request."""
        return await AuditLogService.log_event(
            action_type=AuditActionType.ACCOUNT_DELETION_REQUEST,
            user_id=user_id,
            resource_type=AuditResourceType.DELETION_REQUEST,
            resource_id=deletion_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=metadata
        )
    
    @staticmethod
    async def log_privacy_settings_change(
        user_id: str,
        ip_address: str,
        user_agent: str,
        changes: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log privacy settings change."""
        meta = dict(metadata) if metadata else {}
        meta['changes'] = changes
        
        return await AuditLogService.log_event(
            action_type=AuditActionType.PRIVACY_SETTINGS_CHANGE,
            user_id=user_id,
            resource_type=AuditResourceType.PRIVACY_SETTINGS,
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=meta
        )
    
    # Other Critical Actions
    
    @staticmethod
    async def log_api_key_created(
        user_id: str,
        ip_address: str,
        user_agent: str,
        api_key_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log API key creation."""
        return await AuditLogService.log_event(
            action_type=AuditActionType.API_KEY_CREATED,
            user_id=user_id,
            resource_type=AuditResourceType.API_KEY,
            resource_id=api_key_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=metadata
        )
    
    @staticmethod
    async def log_api_key_revoked(
        user_id: str,
        ip_address: str,
        user_agent: str,
        api_key_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log API key revocation."""
        return await AuditLogService.log_event(
            action_type=AuditActionType.API_KEY_REVOKED,
            user_id=user_id,
            resource_type=AuditResourceType.API_KEY,
            resource_id=api_key_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=metadata
        )
    
    @staticmethod
    async def log_consent_recorded(
        user_id: str,
        ip_address: str,
        user_agent: str,
        document_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log consent recorded."""
        meta = dict(metadata) if metadata else {}
        meta['document_type'] = document_type
        
        return await AuditLogService.log_event(
            action_type=AuditActionType.CONSENT_RECORDED,
            user_id=user_id,
            resource_type=AuditResourceType.USER,
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=meta
        )
    
    @staticmethod
    async def log_consent_withdrawn(
        user_id: str,
        ip_address: str,
        user_agent: str,
        consent_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log consent withdrawal."""
        meta = dict(metadata) if metadata else {}
        meta['consent_type'] = consent_type
        
        return await AuditLogService.log_event(
            action_type=AuditActionType.CONSENT_WITHDRAWN,
            user_id=user_id,
            resource_type=AuditResourceType.USER,
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result=AuditResult.SUCCESS,
            metadata=meta
        )


def get_client_ip(request) -> str:
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip


def get_user_agent(request) -> str:
    """Extract user agent from request."""
    return request.META.get('HTTP_USER_AGENT', 'Unknown')
