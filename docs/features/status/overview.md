# Status Page

This module provides a public status page for monitoring platform health and incidents.

## Requirements

Implements Requirements 18.1-18.12:
- 18.1: Public status page accessible without authentication
- 18.2: Display current status for components
- 18.3: Use status indicators (operational, degraded, partial_outage, major_outage)
- 18.4: Automatically update component status every 60 seconds
- 18.5: Display incident history for past 90 days
- 18.6: Create incident reports
- 18.7: Post incident updates with ETAs
- 18.8: Post resolution details and root cause
- 18.9: Display uptime percentages (30, 60, 90 days)
- 18.10: Status subscriptions (email/SMS)
- 18.11: Display scheduled maintenance windows
- 18.12: Provide RSS feed for status updates

## Components

### Models (Prisma Schema)

- **ComponentStatus**: Tracks status of platform components
- **UptimeRecord**: Records uptime checks for calculating percentages
- **Incident**: Tracks platform incidents
- **IncidentComponent**: Links incidents to affected components
- **IncidentUpdate**: Status updates for incidents
- **MaintenanceWindow**: Scheduled maintenance windows
- **StatusSubscription**: User subscriptions for status notifications

### Services

#### StatusPageService

Main service for status page functionality:

- `get_current_status()`: Get current status of all components
- `get_incident_history(days)`: Get incident history
- `get_uptime_percentages(component_id, days)`: Calculate uptime
- `create_incident()`: Create new incident
- `add_incident_update()`: Add update to incident
- `resolve_incident()`: Resolve incident with root cause
- `get_scheduled_maintenance()`: Get upcoming maintenance

#### HealthCheckService

Automated health checking:

- `check_all_components()`: Check all components
- `check_api()`: Check API health
- `check_database()`: Check database connectivity
- `check_file_storage()`: Check S3 connectivity
- `check_email_service()`: Check Resend status
- `check_authentication()`: Check Clerk status

### API Endpoints

#### Public Endpoints (No Authentication Required)

##### GET /api/status
Get current platform status.

**Response:**
```json
{
  "components": [
    {
      "id": "uuid",
      "name": "API",
      "status": "operational",
      "last_checked": "2024-01-15T10:30:00Z"
    }
  ],
  "overall_status": "operational",
  "recent_incidents": [...],
  "scheduled_maintenance": [...],
  "last_updated": "2024-01-15T10:30:00Z"
}
```

##### GET /api/status/components/{component_id}
Get detailed component status with uptime.

**Response:**
```json
{
  "component": {
    "id": "uuid",
    "name": "API",
    "status": "operational"
  },
  "uptime": {
    "30_days": 99.9,
    "60_days": 99.8,
    "90_days": 99.7
  }
}
```

##### GET /api/status/incidents?days=90
Get incident history.

**Query Parameters:**
- `days`: Number of days to look back (1-365, default 90)

**Response:**
```json
{
  "incidents": [
    {
      "id": "uuid",
      "title": "Database Performance Degradation",
      "description": "...",
      "status": "resolved",
      "severity": "major",
      "started_at": "2024-01-15T08:00:00Z",
      "resolved_at": "2024-01-15T10:30:00Z",
      "root_cause": "...",
      "resolution": "...",
      "affected_components": [...],
      "updates": [...]
    }
  ],
  "period_days": 90
}
```

##### GET /api/status/maintenance
Get scheduled maintenance windows.

**Response:**
```json
{
  "maintenance_windows": [
    {
      "id": "uuid",
      "title": "Database Upgrade",
      "description": "...",
      "scheduled_start": "2024-01-20T02:00:00Z",
      "scheduled_end": "2024-01-20T04:00:00Z",
      "status": "scheduled",
      "affected_components": ["Database"]
    }
  ]
}
```

##### GET /api/status/rss
Get RSS feed of status updates.

**Response:** RSS XML feed

#### Admin Endpoints (Authentication + Administrator Role Required)

##### POST /api/status/incidents/create
Create a new incident.

**Request Body:**
```json
{
  "title": "Database Performance Issues",
  "description": "Users experiencing slow response times",
  "severity": "major",
  "affected_components": ["component-uuid-1", "component-uuid-2"]
}
```

**Response:**
```json
{
  "id": "uuid",
  "title": "...",
  "status": "investigating",
  "severity": "major",
  "started_at": "2024-01-15T10:30:00Z"
}
```

##### POST /api/status/incidents/{incident_id}/updates
Add an update to an incident.

**Request Body:**
```json
{
  "message": "We have identified the issue and are working on a fix",
  "status": "identified",
  "estimated_resolution": "2024-01-15T12:00:00Z"
}
```

##### POST /api/status/incidents/{incident_id}/resolve
Resolve an incident.

**Request Body:**
```json
{
  "root_cause": "Database connection pool exhaustion",
  "resolution": "Increased connection pool size and optimized queries"
}
```

##### POST /api/status/health-check
Trigger manual health check.

**Response:**
```json
{
  "message": "Health check completed",
  "results": {
    "API": "operational",
    "Database": "operational",
    "File Storage": "operational",
    "Email Service": "operational",
    "Authentication": "operational"
  }
}
```

## Status Indicators

The system uses four status levels (Requirement 18.3):

- **operational** (green): Component is fully functional
- **degraded** (yellow): Component is functional but experiencing performance issues
- **partial_outage** (orange): Component is partially unavailable
- **major_outage** (red): Component is completely unavailable

## Automated Health Checks

Health checks run automatically every 60 seconds via Celery Beat (Requirement 18.4).

### Setup

Add to `settings.py`:

```python
CELERY_BEAT_SCHEDULE = {
    'status-health-checks': {
        'task': 'apps.status.tasks.perform_health_checks',
        'schedule': 60.0,  # Run every 60 seconds
    },
}
```

## Uptime Calculation

Uptime percentages are calculated from `UptimeRecord` entries:

- Records are created every 60 seconds during health checks
- Uptime = (successful checks / total checks) × 100
- Calculated for 30, 60, and 90 day periods

## Integration

To integrate this module:

1. Add 'apps.status' to INSTALLED_APPS in settings.py
2. Include status URLs in main urls.py:
   ```python
   path('api/status/', include('apps.status.urls')),
   ```
3. Run Prisma migrations to create database tables
4. Configure Celery Beat for automated health checks
5. Initialize components:
   ```python
   python manage.py shell
   from apps.status.status_service import StatusPageService
   # Components will be auto-created on first access
   ```

## Monitored Components

The system monitors five core components (Requirement 18.2):

1. **API**: Django application health
2. **Database**: PostgreSQL connectivity and performance
3. **File Storage**: AWS S3 connectivity
4. **Email Service**: Resend API status
5. **Authentication**: Clerk API status

## Future Enhancements

- Status subscriptions implementation (Requirement 18.10)
- SMS notifications via Twilio
- Webhook notifications for external monitoring
- Historical uptime charts
- Incident postmortem templates
- Automated incident detection from metrics
