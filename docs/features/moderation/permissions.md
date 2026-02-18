# Moderation Permission System

This document describes the role-based permission system for the content moderation dashboard.

## Overview

The moderation system implements a three-tier role hierarchy with specific permissions for each role:

1. **MODERATOR** - Basic moderation access
2. **SENIOR_MODERATOR** - Enhanced moderation capabilities
3. **ADMINISTRATOR** - Full moderation and administrative access

## Role Permissions

### MODERATOR
**Can:**
- View moderation queue and report details
- Dismiss **low-priority reports only**

**Cannot:**
- Dismiss medium or high-priority reports
- Warn users
- Hide or delete content
- Suspend users
- Assign moderator roles

### SENIOR_MODERATOR
**Can:**
- View moderation queue and report details
- Dismiss reports (any priority)
- Warn users
- Hide content (soft delete)

**Cannot:**
- Delete content (permanent deletion)
- Suspend users
- Assign moderator roles

### ADMINISTRATOR
**Can:**
- All SENIOR_MODERATOR permissions
- Delete content (permanent deletion)
- Suspend users
- Assign and remove moderator roles
- View list of all moderators

## Implementation

### Permission Decorators

The system provides three main decorators for protecting endpoints:

#### 1. `@require_moderator_role(allowed_roles=None)`

Requires the user to have an active moderator role. Optionally restricts to specific roles.

```python
from apps.moderation.permissions import require_moderator_role

# Any moderator role
@require_moderator_role()
def view_queue(request):
    pass

# Specific roles only
@require_moderator_role(['ADMINISTRATOR', 'SENIOR_MODERATOR'])
def hide_content(request):
    pass
```

#### 2. `@require_administrator`

Convenience decorator that requires ADMINISTRATOR role.

```python
from apps.moderation.permissions import require_administrator

@require_administrator
def assign_moderator(request):
    pass
```

#### 3. `@check_action_permission`

Validates that the user has permission to perform a specific moderation action based on their role and the action type.

```python
from apps.moderation.permissions import check_action_permission

@check_action_permission
def take_moderation_action(request):
    # Permission already validated based on action_type in request.data
    pass
```

### Permission Validation Function

For programmatic permission checks:

```python
from apps.moderation.permissions import can_perform_action

# Check if user can perform an action
can_perform, error_message = await can_perform_action(
    user_id='user123',
    action_type='DELETE',
    report_priority='high'  # Required for DISMISS actions
)

if not can_perform:
    return Response({'error': error_message}, status=403)
```

## API Endpoints and Required Permissions

| Endpoint | Method | Required Role | Description |
|----------|--------|---------------|-------------|
| `/api/moderation/queue/` | GET | Any Moderator | View moderation queue |
| `/api/moderation/reports/{id}/` | GET | Any Moderator | View report details |
| `/api/moderation/actions/` | POST | Varies by action | Take moderation action |
| `/api/moderation/stats/` | GET | Any Moderator | View moderation statistics |
| `/api/moderation/moderators/` | GET | Administrator | List all moderators |
| `/api/moderation/moderators/assign/` | POST | Administrator | Assign moderator role |
| `/api/moderation/moderators/{id}/` | DELETE | Administrator | Remove moderator role |

## Moderation Actions and Required Permissions

| Action | Moderator | Senior Moderator | Administrator |
|--------|-----------|------------------|---------------|
| DISMISS (low priority) | ✅ | ✅ | ✅ |
| DISMISS (medium/high) | ❌ | ✅ | ✅ |
| WARN | ❌ | ✅ | ✅ |
| HIDE | ❌ | ✅ | ✅ |
| DELETE | ❌ | ❌ | ✅ |
| SUSPEND | ❌ | ❌ | ✅ |

## Error Responses

### 401 Unauthorized
Returned when the user is not authenticated.

```json
{
  "error": "Authentication required"
}
```

### 403 Forbidden
Returned when the user lacks the required permissions.

```json
{
  "error": "Moderator access required"
}
```

```json
{
  "error": "Insufficient permissions. Required role: ADMINISTRATOR"
}
```

```json
{
  "error": "Moderators can only dismiss low-priority reports"
}
```

```json
{
  "error": "Senior Moderators cannot perform DELETE action. Only Administrators can delete content or suspend users."
}
```

## Requirements Mapping

This implementation satisfies the following requirements:

- **Requirement 3.1**: Support role types: ADMINISTRATOR, SENIOR_MODERATOR, MODERATOR
- **Requirement 3.2**: Grant access to moderation dashboard when role is assigned
- **Requirement 3.3**: Senior_Moderators can review reports, hide content, and warn users
- **Requirement 3.4**: Moderators can review reports and dismiss low-priority reports only
- **Requirement 3.5**: Only Administrators can delete content, suspend users, and assign moderator roles
- **Requirement 3.6**: Return 403 Forbidden error for unauthorized access
- **Requirement 3.7**: Log all role assignments and permission changes (implemented in views)
- **Requirement 3.8**: Display list of all moderators with roles and activity statistics (admin only)

## Testing

The permission system includes comprehensive unit tests in `test_permissions.py`:

```bash
# Run permission tests
python -m pytest apps/moderation/test_permissions.py -v
```

Tests cover:
- Role-based action permissions for all roles
- Decorator behavior for authentication and authorization
- Permission validation for different action types
- Error responses for unauthorized access

## Usage Examples

### Protecting a View

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from apps.moderation.permissions import require_moderator_role

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_moderator_role(['SENIOR_MODERATOR', 'ADMINISTRATOR'])
def senior_mod_endpoint(request):
    # Only senior moderators and administrators can access
    # request.moderator_role contains the user's role
    return Response({'role': request.moderator_role.role})
```

### Checking Permissions Programmatically

```python
from apps.moderation.permissions import can_perform_action

async def process_action(user_id, action_type, report):
    # Calculate report priority
    priority = calculate_priority(report)
    
    # Check if user can perform this action
    can_perform, error = await can_perform_action(
        user_id=user_id,
        action_type=action_type,
        report_priority=priority
    )
    
    if not can_perform:
        raise PermissionError(error)
    
    # Proceed with action
    execute_action(action_type, report)
```

## Database Schema

The `ModeratorRole` model stores role assignments:

```prisma
model ModeratorRole {
  id          String            @id @default(uuid())
  user_id     String            @unique
  role        ModeratorRoleType
  assigned_by String
  assigned_at DateTime          @default(now())
  is_active   Boolean           @default(true)

  @@index([user_id])
  @@index([role])
  @@index([is_active])
}

enum ModeratorRoleType {
  MODERATOR
  SENIOR_MODERATOR
  ADMINISTRATOR
}
```

## Security Considerations

1. **Role Validation**: All endpoints validate the user's role before allowing access
2. **Action-Level Permissions**: Moderation actions are validated based on both role and action type
3. **Priority-Based Access**: Moderators can only dismiss low-priority reports
4. **Audit Trail**: All role assignments and moderation actions are logged (Requirement 3.7)
5. **Active Status**: Only active moderator roles grant permissions

## Future Enhancements

1. **Granular Permissions**: Add more fine-grained permissions (e.g., content-type specific)
2. **Time-Limited Roles**: Support temporary moderator assignments
3. **Permission Groups**: Allow custom permission groups beyond the three default roles
4. **Activity Monitoring**: Track moderator activity and flag suspicious patterns
5. **Role Hierarchy**: Implement automatic permission inheritance
