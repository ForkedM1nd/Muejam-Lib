# Admin Dashboard

This module provides comprehensive admin dashboard functionality for monitoring platform health, user activity, and business metrics.

## Requirements

Implements Requirements 17.1-17.5:
- 17.1: Admin dashboard accessible only to Administrator role
- 17.2: Display real-time metrics
- 17.3: Display business metrics
- 17.4: Display content moderation metrics
- 17.5: Display system health indicators

## Components

### AdminDashboardService

Service class that aggregates metrics from various sources:

- `get_system_health()`: Returns system health indicators
- `get_real_time_metrics()`: Returns real-time platform metrics
- `get_business_metrics(days)`: Returns business metrics for specified period
- `get_moderation_metrics()`: Returns content moderation metrics

All methods implement 60-second caching to reduce database load (Requirement 17.11).

### API Endpoints

All endpoints require authentication and Administrator role.

#### GET /api/admin/dashboard
Returns comprehensive dashboard data including all metrics.

**Response:**
```json
{
  "system_health": {
    "database_status": "healthy",
    "cache_status": "healthy",
    "external_services": {...},
    "disk_space": 45.2,
    "memory_usage": 62.8
  },
  "real_time_metrics": {
    "active_users": 1250,
    "requests_per_minute": 1250.5,
    "error_rate": 0.3,
    "api_response_times": {
      "p50": 125.0,
      "p95": 450.0,
      "p99": 850.0
    }
  },
  "business_metrics": {
    "new_signups": {...},
    "stories_published": {...},
    "whispers_posted": {...},
    "engagement_rates": {...}
  },
  "moderation_metrics": {
    "pending_reports": 15,
    "reports_resolved_today": 42,
    "average_resolution_time": 2.5,
    "actions_by_type": {...}
  }
}
```

#### GET /api/admin/metrics/real-time
Returns real-time platform metrics.

**Response:**
```json
{
  "active_users": 1250,
  "requests_per_minute": 1250.5,
  "error_rate": 0.3,
  "api_response_times": {
    "p50": 125.0,
    "p95": 450.0,
    "p99": 850.0
  },
  "last_updated": "2024-01-15T10:30:00Z"
}
```

#### GET /api/admin/metrics/business?days=30
Returns business metrics for specified time period.

**Query Parameters:**
- `days` (optional): Number of days to look back (1-365, default 30)

**Response:**
```json
{
  "new_signups": {
    "total": 1500,
    "daily_average": 50.0,
    "weekly_average": 350.0,
    "monthly_average": 1500.0
  },
  "stories_published": {
    "total": 450,
    "average_per_day": 15.0
  },
  "whispers_posted": {
    "total": 3200,
    "average_per_day": 106.67
  },
  "engagement_rates": {
    "likes_per_story": 12.5,
    "comments_per_story": 3.2,
    "shares_per_story": 1.8
  },
  "user_retention": {
    "dau_mau_ratio": 0.35,
    "weekly_retention": 0.68,
    "monthly_retention": 0.42
  },
  "period_days": 30,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

#### GET /api/admin/health
Returns system health status.

**Response:**
```json
{
  "database_status": "healthy",
  "cache_status": "healthy",
  "external_services": {
    "s3": "healthy",
    "clerk": "healthy",
    "resend": "healthy",
    "sentry": "healthy"
  },
  "disk_space": 45.2,
  "memory_usage": 62.8,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

#### GET /api/admin/metrics/moderation
Returns content moderation metrics.

**Response:**
```json
{
  "pending_reports": 15,
  "reports_resolved_today": 42,
  "average_resolution_time": 2.5,
  "actions_by_type": {
    "DISMISS": 120,
    "WARN": 45,
    "HIDE": 30,
    "DELETE": 15,
    "SUSPEND": 8
  },
  "last_updated": "2024-01-15T10:30:00Z"
}
```

## Permissions

All endpoints use the `IsAdministrator` permission class which:
- Requires authentication
- Checks for Administrator role or Django staff/superuser status
- Returns 403 Forbidden for non-administrators

## Caching

All metrics are cached for 60 seconds to reduce database load and improve performance (Requirement 17.11).

## Integration

To integrate this module:

1. Add 'apps.admin' to INSTALLED_APPS in settings.py
2. Include admin URLs in main urls.py:
   ```python
   path('api/admin/', include('apps.admin.urls')),
   ```

## Future Enhancements

- Real-time metrics integration with APM provider
- CSV export functionality (Requirement 17.10)
- Auto-refresh every 60 seconds (Requirement 17.11)
- User growth charts with trend lines (Requirement 17.6)
- Content growth charts (Requirement 17.7)
- Top content rankings (Requirement 17.8)
- Recent critical events display (Requirement 17.12)
