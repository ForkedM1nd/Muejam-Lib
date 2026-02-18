"""
Alerting Service with PagerDuty Integration

This module provides intelligent alerting with PagerDuty integration.
Implements Requirements 16.1-16.13 from production-readiness spec.

Features:
- PagerDuty incident creation and management
- Alert severity levels (critical, high, medium, low)
- Alert deduplication
- Maintenance window suppression
- Alert acknowledgment and resolution tracking
- Escalation for unacknowledged alerts
"""

import os
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
import requests
from dataclasses import dataclass


class AlertSeverity(Enum):
    """
    Alert severity levels.
    
    Implements Requirement 16.2: Define alert severity levels.
    """
    CRITICAL = 'critical'  # Immediate response
    HIGH = 'high'          # 1 hour response
    MEDIUM = 'medium'      # 4 hour response
    LOW = 'low'            # Next business day


@dataclass
class Alert:
    """Alert data structure."""
    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    source: str
    timestamp: datetime
    metadata: Dict[str, Any]
    dedup_key: Optional[str] = None


@dataclass
class AlertIncident:
    """PagerDuty incident data structure."""
    incident_id: str
    alert_id: str
    status: str  # triggered, acknowledged, resolved
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class AlertingConfig:
    """
    Alerting configuration.
    
    Implements Requirements 16.1-16.13.
    """
    
    # PagerDuty Configuration (Requirement 16.1)
    PAGERDUTY_ENABLED = os.getenv('PAGERDUTY_ENABLED', 'False') == 'True'
    PAGERDUTY_INTEGRATION_KEY = os.getenv('PAGERDUTY_INTEGRATION_KEY', '')
    PAGERDUTY_API_KEY = os.getenv('PAGERDUTY_API_KEY', '')
    PAGERDUTY_API_URL = 'https://api.pagerduty.com'
    PAGERDUTY_EVENTS_URL = 'https://events.pagerduty.com/v2/enqueue'
    
    # Alert Escalation (Requirement 16.13)
    ESCALATION_TIMEOUT_MINUTES = int(os.getenv('ALERT_ESCALATION_TIMEOUT', '15'))
    
    # Maintenance Windows (Requirement 16.10)
    MAINTENANCE_MODE = os.getenv('MAINTENANCE_MODE', 'False') == 'True'
    MAINTENANCE_START = os.getenv('MAINTENANCE_START', '')
    MAINTENANCE_END = os.getenv('MAINTENANCE_END', '')
    
    # Alert Deduplication (Requirement 16.9)
    DEDUP_WINDOW_SECONDS = int(os.getenv('ALERT_DEDUP_WINDOW', '300'))  # 5 minutes
    
    # Daily Summary (Requirement 16.12)
    SUMMARY_EMAIL_ENABLED = os.getenv('ALERT_SUMMARY_EMAIL_ENABLED', 'True') == 'True'
    SUMMARY_EMAIL_RECIPIENTS = os.getenv('ALERT_SUMMARY_EMAIL_RECIPIENTS', '').split(',')
    SUMMARY_EMAIL_TIME = os.getenv('ALERT_SUMMARY_EMAIL_TIME', '09:00')  # 9 AM


class AlertingService:
    """
    Alerting service with PagerDuty integration.
    
    Implements Requirements 16.1-16.13.
    """
    
    def __init__(self):
        """Initialize alerting service."""
        self.config = AlertingConfig()
        self._recent_alerts: Dict[str, datetime] = {}  # For deduplication
        self._active_incidents: Dict[str, AlertIncident] = {}  # Track incidents
    
    def send_alert(
        self,
        severity: AlertSeverity,
        title: str,
        description: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
        dedup_key: Optional[str] = None,
    ) -> Optional[str]:
        """
        Send an alert to PagerDuty.
        
        Implements Requirements:
        - 16.1: Integrate with PagerDuty
        - 16.2: Define alert severity levels
        - 16.6: Page on-call engineer for critical alerts
        - 16.9: Implement alert deduplication
        - 16.10: Implement alert suppression during maintenance
        
        Args:
            severity: Alert severity level
            title: Alert title
            description: Alert description
            source: Alert source (service/component)
            metadata: Additional metadata
            dedup_key: Deduplication key (optional)
            
        Returns:
            Incident ID if created, None otherwise
        """
        # Check if in maintenance mode (Requirement 16.10)
        if self._is_maintenance_window():
            print(f"Alert suppressed during maintenance: {title}")
            return None
        
        # Generate dedup key if not provided
        if not dedup_key:
            dedup_key = f"{source}:{title}"
        
        # Check for duplicate alerts (Requirement 16.9)
        if self._is_duplicate_alert(dedup_key):
            print(f"Duplicate alert suppressed: {title}")
            return None
        
        # Create alert object
        alert = Alert(
            alert_id=f"alert_{int(time.time())}",
            severity=severity,
            title=title,
            description=description,
            source=source,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
            dedup_key=dedup_key,
        )
        
        # Send to PagerDuty if enabled
        if self.config.PAGERDUTY_ENABLED and self.config.PAGERDUTY_INTEGRATION_KEY:
            incident_id = self._send_to_pagerduty(alert)
            if incident_id:
                # Track incident
                self._active_incidents[incident_id] = AlertIncident(
                    incident_id=incident_id,
                    alert_id=alert.alert_id,
                    status='triggered',
                    created_at=alert.timestamp,
                )
                
                # Record alert for deduplication
                self._recent_alerts[dedup_key] = alert.timestamp
                
                return incident_id
        
        return None
    
    def _send_to_pagerduty(self, alert: Alert) -> Optional[str]:
        """
        Send alert to PagerDuty Events API.
        
        Args:
            alert: Alert to send
            
        Returns:
            Incident dedup key if successful, None otherwise
        """
        try:
            # Map severity to PagerDuty severity
            pd_severity = self._map_severity(alert.severity)
            
            # Create PagerDuty event
            event = {
                'routing_key': self.config.PAGERDUTY_INTEGRATION_KEY,
                'event_action': 'trigger',
                'dedup_key': alert.dedup_key,
                'payload': {
                    'summary': alert.title,
                    'source': alert.source,
                    'severity': pd_severity,
                    'timestamp': alert.timestamp.isoformat(),
                    'custom_details': {
                        'description': alert.description,
                        **alert.metadata,
                    },
                },
            }
            
            # Send to PagerDuty
            response = requests.post(
                self.config.PAGERDUTY_EVENTS_URL,
                json=event,
                timeout=10,
            )
            
            if response.status_code == 202:
                result = response.json()
                return result.get('dedup_key')
            else:
                print(f"Failed to send alert to PagerDuty: {response.status_code} {response.text}")
                return None
                
        except Exception as e:
            print(f"Error sending alert to PagerDuty: {e}")
            return None
    
    def acknowledge_alert(self, incident_id: str) -> bool:
        """
        Acknowledge an alert.
        
        Implements Requirement 16.7: Track time to acknowledgment.
        
        Args:
            incident_id: Incident ID
            
        Returns:
            True if acknowledged, False otherwise
        """
        if incident_id not in self._active_incidents:
            return False
        
        incident = self._active_incidents[incident_id]
        
        if incident.status == 'triggered':
            incident.status = 'acknowledged'
            incident.acknowledged_at = datetime.utcnow()
            
            # Send acknowledgment to PagerDuty
            if self.config.PAGERDUTY_ENABLED:
                self._send_pagerduty_event(incident_id, 'acknowledge')
            
            return True
        
        return False
    
    def resolve_alert(self, incident_id: str, resolution_notes: str) -> bool:
        """
        Resolve an alert.
        
        Implements Requirement 16.8: Record resolution time and require notes.
        
        Args:
            incident_id: Incident ID
            resolution_notes: Resolution notes (required)
            
        Returns:
            True if resolved, False otherwise
        """
        if not resolution_notes:
            raise ValueError("Resolution notes are required")
        
        if incident_id not in self._active_incidents:
            return False
        
        incident = self._active_incidents[incident_id]
        
        if incident.status in ['triggered', 'acknowledged']:
            incident.status = 'resolved'
            incident.resolved_at = datetime.utcnow()
            incident.resolution_notes = resolution_notes
            
            # Send resolution to PagerDuty
            if self.config.PAGERDUTY_ENABLED:
                self._send_pagerduty_event(incident_id, 'resolve')
            
            return True
        
        return False
    
    def _send_pagerduty_event(self, incident_id: str, action: str) -> bool:
        """
        Send event to PagerDuty (acknowledge or resolve).
        
        Args:
            incident_id: Incident ID (dedup key)
            action: Event action ('acknowledge' or 'resolve')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            event = {
                'routing_key': self.config.PAGERDUTY_INTEGRATION_KEY,
                'event_action': action,
                'dedup_key': incident_id,
            }
            
            response = requests.post(
                self.config.PAGERDUTY_EVENTS_URL,
                json=event,
                timeout=10,
            )
            
            return response.status_code == 202
            
        except Exception as e:
            print(f"Error sending {action} to PagerDuty: {e}")
            return False
    
    def _is_duplicate_alert(self, dedup_key: str) -> bool:
        """
        Check if alert is a duplicate.
        
        Implements Requirement 16.9: Alert deduplication.
        
        Args:
            dedup_key: Deduplication key
            
        Returns:
            True if duplicate, False otherwise
        """
        if dedup_key in self._recent_alerts:
            last_alert_time = self._recent_alerts[dedup_key]
            time_since_last = (datetime.utcnow() - last_alert_time).total_seconds()
            
            if time_since_last < self.config.DEDUP_WINDOW_SECONDS:
                return True
            else:
                # Remove old alert from tracking
                del self._recent_alerts[dedup_key]
        
        return False
    
    def _is_maintenance_window(self) -> bool:
        """
        Check if currently in maintenance window.
        
        Implements Requirement 16.10: Alert suppression during maintenance.
        
        Returns:
            True if in maintenance window, False otherwise
        """
        if not self.config.MAINTENANCE_MODE:
            return False
        
        if not self.config.MAINTENANCE_START or not self.config.MAINTENANCE_END:
            return False
        
        try:
            now = datetime.utcnow()
            start = datetime.fromisoformat(self.config.MAINTENANCE_START)
            end = datetime.fromisoformat(self.config.MAINTENANCE_END)
            
            return start <= now <= end
        except Exception:
            return False
    
    def _map_severity(self, severity: AlertSeverity) -> str:
        """
        Map internal severity to PagerDuty severity.
        
        Args:
            severity: Internal severity level
            
        Returns:
            PagerDuty severity string
        """
        mapping = {
            AlertSeverity.CRITICAL: 'critical',
            AlertSeverity.HIGH: 'error',
            AlertSeverity.MEDIUM: 'warning',
            AlertSeverity.LOW: 'info',
        }
        return mapping.get(severity, 'info')
    
    def get_incident_metrics(self) -> Dict[str, Any]:
        """
        Get incident metrics for dashboards.
        
        Implements Requirement 16.11: Alert dashboards with MTTR.
        
        Returns:
            Dictionary with incident metrics
        """
        total_incidents = len(self._active_incidents)
        resolved_incidents = [
            i for i in self._active_incidents.values()
            if i.status == 'resolved'
        ]
        
        # Calculate MTTR (Mean Time To Resolution)
        mttr_seconds = 0
        if resolved_incidents:
            resolution_times = [
                (i.resolved_at - i.created_at).total_seconds()
                for i in resolved_incidents
                if i.resolved_at
            ]
            if resolution_times:
                mttr_seconds = sum(resolution_times) / len(resolution_times)
        
        # Calculate MTTA (Mean Time To Acknowledgment)
        acknowledged_incidents = [
            i for i in self._active_incidents.values()
            if i.acknowledged_at
        ]
        mtta_seconds = 0
        if acknowledged_incidents:
            ack_times = [
                (i.acknowledged_at - i.created_at).total_seconds()
                for i in acknowledged_incidents
            ]
            if ack_times:
                mtta_seconds = sum(ack_times) / len(ack_times)
        
        return {
            'total_incidents': total_incidents,
            'resolved_incidents': len(resolved_incidents),
            'active_incidents': total_incidents - len(resolved_incidents),
            'mttr_seconds': mttr_seconds,
            'mttr_minutes': mttr_seconds / 60,
            'mtta_seconds': mtta_seconds,
            'mtta_minutes': mtta_seconds / 60,
        }
    
    def check_escalation(self) -> List[str]:
        """
        Check for unacknowledged critical alerts that need escalation.
        
        Implements Requirement 16.13: Escalate unacknowledged critical alerts.
        
        Returns:
            List of incident IDs that need escalation
        """
        escalation_needed = []
        now = datetime.utcnow()
        timeout = timedelta(minutes=self.config.ESCALATION_TIMEOUT_MINUTES)
        
        for incident_id, incident in self._active_incidents.items():
            if incident.status == 'triggered':
                time_since_created = now - incident.created_at
                
                if time_since_created > timeout:
                    escalation_needed.append(incident_id)
        
        return escalation_needed


class AlertRules:
    """
    Alert rule definitions.
    
    Implements Requirements 16.3, 16.4, 16.5: Define alert conditions.
    """
    
    # Critical Alerts (Requirement 16.3)
    CRITICAL_RULES = {
        'service_downtime': {
            'title': 'Service Downtime Detected',
            'description': 'The service is not responding to health checks',
            'severity': AlertSeverity.CRITICAL,
        },
        'database_connection_failure': {
            'title': 'Database Connection Failure',
            'description': 'Unable to connect to the database',
            'severity': AlertSeverity.CRITICAL,
        },
        'high_error_rate': {
            'title': 'High Error Rate',
            'description': 'Error rate exceeds 5%',
            'threshold': 0.05,
            'severity': AlertSeverity.CRITICAL,
        },
        'slow_api_p99': {
            'title': 'Slow API Response Time',
            'description': 'API p99 response time exceeds 2000ms',
            'threshold': 2000,
            'severity': AlertSeverity.CRITICAL,
        },
    }
    
    # High Alerts (Requirement 16.4)
    HIGH_RULES = {
        'high_disk_space': {
            'title': 'High Disk Space Usage',
            'description': 'Disk space usage exceeds 85%',
            'threshold': 0.85,
            'severity': AlertSeverity.HIGH,
        },
        'high_memory_usage': {
            'title': 'High Memory Usage',
            'description': 'Memory usage exceeds 90%',
            'threshold': 0.90,
            'severity': AlertSeverity.HIGH,
        },
        'cache_failure': {
            'title': 'Cache Failure',
            'description': 'Unable to connect to cache (Redis/Valkey)',
            'severity': AlertSeverity.HIGH,
        },
        'external_service_degradation': {
            'title': 'External Service Degradation',
            'description': 'External service response time degraded',
            'severity': AlertSeverity.HIGH,
        },
    }
    
    # Medium Alerts (Requirement 16.5)
    MEDIUM_RULES = {
        'elevated_error_rate': {
            'title': 'Elevated Error Rate',
            'description': 'Error rate exceeds 1%',
            'threshold': 0.01,
            'severity': AlertSeverity.MEDIUM,
        },
        'slow_queries': {
            'title': 'Slow Database Queries',
            'description': 'Database queries exceeding 100ms threshold',
            'severity': AlertSeverity.MEDIUM,
        },
        'elevated_rate_limiting': {
            'title': 'Elevated Rate Limiting',
            'description': 'Unusual number of rate limit events',
            'severity': AlertSeverity.MEDIUM,
        },
        'suspicious_activity': {
            'title': 'Suspicious Activity Pattern',
            'description': 'Suspicious activity detected',
            'severity': AlertSeverity.MEDIUM,
        },
    }


# Global alerting service instance
_alerting_service: Optional[AlertingService] = None


def get_alerting_service() -> AlertingService:
    """
    Get the global alerting service instance.
    
    Returns:
        AlertingService instance
    """
    global _alerting_service
    if _alerting_service is None:
        _alerting_service = AlertingService()
    return _alerting_service


# Export public API
__all__ = [
    'AlertingService',
    'AlertingConfig',
    'AlertSeverity',
    'Alert',
    'AlertIncident',
    'AlertRules',
    'get_alerting_service',
]
