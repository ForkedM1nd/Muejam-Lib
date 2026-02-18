# DMCA Agent Dashboard Implementation

This document describes the implementation of the DMCA agent dashboard for task 3.2.

## Overview

The DMCA agent dashboard allows designated agents to review and act on DMCA takedown requests submitted by copyright holders. When a request is approved, the system automatically takes down the infringing content and notifies the content author.

## Requirements Implemented

- **31.6**: Provide DMCA agent dashboard for reviewing requests
- **31.7**: Implement content takedown on approval
- **31.8**: Send notification to content author with counter-notice instructions

## Components

### Backend API Endpoints

#### 1. GET /api/legal/dmca/requests
Lists all DMCA takedown requests with optional status filtering.

**Query Parameters:**
- `status` (optional): Filter by status (PENDING, APPROVED, REJECTED)

**Response:**
```json
[
  {
    "id": "uuid",
    "copyright_holder": "John Doe",
    "contact_info": "john@example.com",
    "copyrighted_work_description": "Description of the work",
    "infringing_url": "https://example.com/story/slug",
    "good_faith_statement": true,
    "signature": "John Doe",
    "status": "PENDING",
    "submitted_at": "2024-01-01T00:00:00Z",
    "reviewed_at": null,
    "reviewed_by": null
  }
]
```

**Requirements:** 31.6

#### 2. POST /api/legal/dmca/requests/{request_id}/review
Reviews a DMCA takedown request (approve or reject).

**Request Body:**
```json
{
  "action": "approve",  // or "reject"
  "reason": "Optional reason for rejection"
}
```

**Response:**
```json
{
  "id": "uuid",
  "status": "APPROVED",
  "reviewed_at": "2024-01-01T00:00:00Z",
  "reviewed_by": "reviewer-user-id",
  ...
}
```

**Requirements:** 31.6, 31.7, 31.8

### Email Notifications

The `LegalEmailService` class handles all DMCA-related email notifications:

#### 1. Confirmation Email to Requester
Sent when a DMCA request is submitted (Requirement 31.4).

#### 2. DMCA Agent Notification
Sent to the designated DMCA agent when a new request is submitted (Requirement 31.5).

#### 3. Takedown Notification to Author
Sent to the content author when their content is taken down, including:
- Reason for takedown
- Counter-notice instructions
- Contact information for DMCA agent

**Requirements:** 31.8

### Content Takedown Logic

The `takedown_content()` function handles content removal:

1. Parses the infringing URL to determine content type (story, chapter, or whisper)
2. Marks the content as deleted by setting `deleted_at` timestamp
3. Returns the author's email for notification purposes

**Supported URL formats:**
- `/stories/{slug}` - Takes down entire story
- `/stories/{slug}/chapters/{chapter_number}` - Takes down specific chapter
- `/whispers/{id}` - Takes down whisper

**Requirements:** 31.7

### Permissions

The `IsDMCAAgent` permission class restricts access to the DMCA dashboard.

**Current Implementation:** Requires authentication only
**Production TODO:** Implement proper role-based access control with a DMCA agent role

**Requirements:** 31.6

## Frontend Component

### DMCADashboard.tsx

A React component that provides the DMCA agent interface:

**Features:**
- Lists all DMCA requests with status filtering (PENDING, APPROVED, REJECTED)
- Displays request details including copyright holder, contact info, and infringing URL
- Provides review modal for approving or rejecting requests
- Shows loading and error states
- Refreshes list after review actions

**Requirements:** 31.6

## Database Schema

The `DMCATakedown` model stores all DMCA requests:

```prisma
model DMCATakedown {
  id                              String      @id @default(uuid())
  copyright_holder                String
  contact_info                    String
  copyrighted_work_description    String      @db.Text
  infringing_url                  String
  good_faith_statement            Boolean     @default(false)
  signature                       String
  status                          DMCAStatus  @default(PENDING)
  submitted_at                    DateTime    @default(now())
  reviewed_at                     DateTime?
  reviewed_by                     String?
  
  @@index([status])
  @@index([submitted_at])
}

enum DMCAStatus {
  PENDING
  APPROVED
  REJECTED
}
```

## Testing

Unit tests are provided in `apps/backend/tests/apps/legal_tests.py`:

- `DMCATakedownTests`: Tests for endpoint validation and authentication
- `DMCATakedownIntegrationTests`: Tests for the complete workflow

**Run tests:**
```bash
cd apps/backend
python -m pytest ../../tests/backend/apps/legal_tests.py::DMCATakedownTests -v
```

## Configuration

### Environment Variables

The following environment variables should be configured:

- `RESEND_API_KEY`: API key for Resend email service
- `RESEND_FROM_EMAIL`: Email address to send from (default: noreply@muejam.com)
- `DMCA_AGENT_EMAIL`: Email address of the designated DMCA agent (default: dmca@muejam.com)
- `FRONTEND_URL`: Base URL of the frontend application (default: http://localhost:3000)

## Usage

### For DMCA Agents

1. Navigate to `/admin/dmca` (or wherever the dashboard is mounted)
2. View pending requests in the PENDING tab
3. Click "Review Request" to see full details
4. Choose to approve or reject:
   - **Approve**: Content is immediately taken down and author is notified
   - **Reject**: Request is marked as rejected (optional reason can be provided)

### For Copyright Holders

1. Submit a DMCA request via the form at `/legal/dmca/submit`
2. Receive confirmation email with request ID
3. Wait for DMCA agent review
4. Receive notification of outcome

### For Content Authors

If your content is taken down:
1. You will receive an email notification with the reason
2. The email includes instructions for submitting a counter-notice
3. Contact the DMCA agent at the provided email address to submit a counter-notice

## Future Enhancements

1. **Role-Based Access Control**: Implement proper DMCA agent role instead of just checking authentication
2. **Counter-Notice System**: Add endpoints and UI for content authors to submit counter-notices
3. **Repeat Infringer Policy**: Track and automatically suspend accounts with 3+ DMCA violations (Requirement 31.12)
4. **Email Integration with Clerk**: Fetch actual user emails from Clerk instead of using placeholder emails
5. **Audit Logging**: Log all DMCA actions for compliance purposes
6. **Dashboard Analytics**: Show statistics on DMCA requests (total, approved, rejected, average review time)
7. **Bulk Actions**: Allow agents to review multiple requests at once
8. **Search and Filtering**: Add search by copyright holder, URL, or date range

## Notes

- The current implementation uses a simplified email extraction from the contact_info field. In production, this should be more robust.
- The content takedown logic uses placeholder emails for authors. This should be integrated with Clerk to fetch actual user emails.
- The permission system is simplified. Production should implement proper role-based access control with a dedicated DMCA agent role in the database.
