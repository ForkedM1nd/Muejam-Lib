# Requirements Document: MueJam Library

## Introduction

MueJam Library is a minimal digital library platform for serial stories with an integrated micro-posting system called "Whispers". The platform enables users to discover, read, and write serial fiction in a distraction-free environment while engaging with a community through short-form posts. The system emphasizes typography-first design, personalized content discovery, and seamless reading experiences across devices.

## Glossary

- **System**: The MueJam Library platform (frontend + backend + infrastructure)
- **User**: Any authenticated person using the platform
- **Reader**: A user consuming story content
- **Author**: A user who creates and publishes stories
- **Story**: A collection of chapters forming a serial narrative
- **Chapter**: A single installment of a story
- **Whisper**: A short-form post (global, story-linked, or highlight-linked)
- **Highlight**: A text passage selected and saved by a reader
- **Shelf**: A user's personal collection for organizing saved stories
- **Library**: A user's collection of shelves
- **Discover_Feed**: The main content discovery interface with Trending, New, and For You tabs
- **For_You_Feed**: Personalized content recommendations based on user interests
- **Reading_Progress**: Tracked position within a chapter
- **Bookmark**: A saved position within a chapter
- **Clerk**: Third-party authentication service
- **Valkey**: Redis-compatible caching layer
- **Presigned_Upload**: Direct-to-S3 upload mechanism using temporary signed URLs
- **Soft_Delete**: Marking content as deleted without physical removal
- **Rate_Limit**: Maximum number of operations allowed within a time window
- **Cursor_Pagination**: Pagination using opaque cursor tokens for stable ordering
- **Interest_Score**: Calculated affinity between user and content attributes
- **Trending_Score**: Time-decayed engagement metric for content popularity
- **Cold_Start**: Initial state when insufficient user data exists for personalization

## Requirements

### Requirement 1: User Authentication and Profile Management

**User Story:** As a user, I want to authenticate securely and manage my profile, so that I can access personalized features and identify myself to the community.

#### Acceptance Criteria

1. WHEN a user initiates authentication, THE System SHALL redirect to Clerk authentication flow
2. WHEN Clerk authentication succeeds, THE System SHALL create or retrieve a UserProfile using clerk_user_id
3. WHEN a user updates their profile, THE System SHALL validate handle uniqueness and update display_name, bio, and avatar_key
4. WHEN a user requests their profile, THE System SHALL return clerk_user_id, handle, display_name, bio, avatar_key, and creation timestamp
5. THE System SHALL enforce handle format as alphanumeric with underscores, 3-30 characters
6. WHEN a user uploads an avatar, THE System SHALL restrict file size to 2MB maximum

### Requirement 2: Story Discovery and Browsing

**User Story:** As a reader, I want to discover stories through multiple feeds, so that I can find content that interests me.

#### Acceptance Criteria

1. WHEN a user accesses the Discover_Feed, THE System SHALL display three tabs: Trending, New, and For You
2. WHEN a user selects the Trending tab, THE System SHALL return stories ordered by Trending_Score within the last 24 hours
3. WHEN a user selects the New tab, THE System SHALL return stories ordered by publication date descending
4. WHEN a user selects the For You tab, THE System SHALL return personalized story recommendations based on Interest_Score
5. WHEN a user has insufficient interaction history (Cold_Start), THE System SHALL fallback to Trending feed results
6. THE System SHALL implement Cursor_Pagination for all discovery feeds
7. WHEN a user requests the next page, THE System SHALL return results after the provided cursor with consistent ordering
8. THE System SHALL cache Trending feed results with TTL between 1-5 minutes
9. THE System SHALL cache For_You_Feed results with TTL between 1-6 hours
10. WHEN a user filters by tag, THE System SHALL return only stories tagged with the specified tag
11. WHEN a user searches with query text, THE System SHALL return stories matching title, blurb, or author name

### Requirement 3: Story and Chapter Reading

**User Story:** As a reader, I want to read stories in a distraction-free environment with customizable settings, so that I can enjoy content comfortably.

#### Acceptance Criteria

1. WHEN a user opens a story page, THE System SHALL display cover image, title, blurb, tags, author information, and chapters list
2. WHEN a user opens a chapter, THE System SHALL display chapter content in a distraction-free reader interface
3. WHERE reader customization is enabled, THE System SHALL allow users to adjust font size, theme (light/dark), and line width
4. WHEN a user scrolls through a chapter, THE System SHALL track Reading_Progress as character offset
5. WHEN a user returns to a chapter, THE System SHALL restore the last Reading_Progress position
6. WHEN a user creates a Bookmark, THE System SHALL save the current character offset and timestamp
7. THE System SHALL enforce maximum 2 primary actions visible in reader view
8. THE System SHALL maintain consistent top navigation across all views
9. WHEN a blocked author's story is requested, THE System SHALL return access denied or hide the content

### Requirement 4: Personal Library Management

**User Story:** As a reader, I want to organize stories into shelves, so that I can curate my personal library.

#### Acceptance Criteria

1. WHEN a user creates a Shelf, THE System SHALL store shelf name and creation timestamp
2. WHEN a user adds a story to a Shelf, THE System SHALL create a ShelfItem linking the story and shelf
3. WHEN a user removes a story from a Shelf, THE System SHALL delete the corresponding ShelfItem
4. WHEN a user requests their Library, THE System SHALL return all shelves with associated stories
5. WHEN a user deletes a Shelf, THE System SHALL remove all associated ShelfItems
6. THE System SHALL allow a story to exist in multiple shelves simultaneously
7. WHEN a user renames a Shelf, THE System SHALL update the shelf name while preserving ShelfItems

### Requirement 5: Story and Chapter Authoring

**User Story:** As an author, I want to create, edit, and publish stories and chapters, so that I can share my work with readers.

#### Acceptance Criteria

1. WHEN an author creates a story draft, THE System SHALL store title, blurb, cover_key, and published status as false
2. WHEN an author creates a chapter draft, THE System SHALL store title, content, story_id, chapter_number, and published status as false
3. WHEN an author publishes a story, THE System SHALL set published status to true and record publication timestamp
4. WHEN an author publishes a chapter, THE System SHALL set published status to true and record publication timestamp
5. WHEN an author edits a draft, THE System SHALL update the content without affecting publication status
6. WHEN an author deletes a story, THE System SHALL perform Soft_Delete by setting deleted_at timestamp
7. WHEN an author deletes a chapter, THE System SHALL perform Soft_Delete by setting deleted_at timestamp
8. THE System SHALL enforce Rate_Limit of 5 publish operations per hour per author
9. WHEN an author uploads a story cover, THE System SHALL restrict file size to 5MB maximum
10. THE System SHALL sanitize markdown content to prevent XSS attacks
11. WHEN a story is published, THE System SHALL appear in the New feed within cache TTL

### Requirement 6: Whispers Micro-Posting System

**User Story:** As a user, I want to post whispers globally or attach them to stories and highlights, so that I can share thoughts and engage with content.

#### Acceptance Criteria

1. WHEN a user creates a global Whisper, THE System SHALL store content with scope GLOBAL
2. WHEN a user creates a story-linked Whisper, THE System SHALL store content with scope STORY and story_id reference
3. WHEN a user creates a highlight-linked Whisper, THE System SHALL store content with scope HIGHLIGHT and highlight_id reference
4. THE System SHALL enforce Rate_Limit of 10 whispers per minute per user
5. WHEN a user deletes a Whisper, THE System SHALL perform Soft_Delete by setting deleted_at timestamp
6. WHEN a user requests global whispers feed, THE System SHALL return whispers with scope GLOBAL ordered by creation time descending
7. WHEN a user requests story-specific whispers, THE System SHALL return whispers with matching story_id ordered by creation time descending
8. THE System SHALL cache whispers feeds with TTL between 30-120 seconds
9. WHEN a user creates a Whisper with media, THE System SHALL restrict file size to 10MB maximum
10. THE System SHALL sanitize Whisper content to prevent XSS attacks
11. WHEN a blocked user's Whisper is requested, THE System SHALL exclude it from feeds

### Requirement 7: Whisper Interactions

**User Story:** As a user, I want to reply to and like whispers, so that I can engage in conversations and show appreciation.

#### Acceptance Criteria

1. WHEN a user replies to a Whisper, THE System SHALL create a new Whisper with parent_whisper_id reference
2. THE System SHALL enforce Rate_Limit of 20 replies per minute per user
3. WHEN a user likes a Whisper, THE System SHALL create a WhisperLike record with user_id and whisper_id
4. WHEN a user unlikes a Whisper, THE System SHALL delete the corresponding WhisperLike record
5. WHEN a user requests a Whisper, THE System SHALL include reply count and like count
6. WHEN a user requests replies to a Whisper, THE System SHALL return child whispers ordered by creation time ascending
7. THE System SHALL prevent duplicate likes by the same user on the same Whisper
8. WHEN a parent Whisper is soft-deleted, THE System SHALL still display replies but mark parent as deleted

### Requirement 8: Text Highlighting and Passage Whispers

**User Story:** As a reader, I want to highlight passages and attach whispers to them, so that I can annotate and discuss specific text.

#### Acceptance Criteria

1. WHEN a user selects text in a chapter, THE System SHALL capture start_offset and end_offset character positions
2. WHEN a user saves a Highlight, THE System SHALL store chapter_id, start_offset, end_offset, and creation timestamp
3. WHEN a user creates a Whisper from a Highlight, THE System SHALL link the Whisper to highlight_id with scope HIGHLIGHT
4. WHEN a user requests highlights for a chapter, THE System SHALL return all highlights with associated whispers
5. WHEN a user deletes a Highlight, THE System SHALL remove the highlight record
6. WHEN a Highlight is deleted, THE System SHALL preserve associated whispers but mark highlight reference as deleted
7. THE System SHALL validate that start_offset is less than end_offset
8. THE System SHALL validate that offsets are within chapter content length

### Requirement 9: Full-Text Search and Suggestions

**User Story:** As a user, I want to search for stories, authors, and tags with autocomplete suggestions, so that I can quickly find content.

#### Acceptance Criteria

1. WHEN a user submits a search query, THE System SHALL return stories matching title, blurb, author name, or tags
2. WHEN a user types in search input, THE System SHALL provide autocomplete suggestions for stories, tags, and authors
3. THE System SHALL cache search suggestions with TTL between 10-30 minutes
4. WHEN a user selects a suggestion, THE System SHALL navigate to the corresponding story or author profile
5. THE System SHALL rank search results by relevance score combining text match and Trending_Score
6. THE System SHALL exclude soft-deleted and blocked content from search results
7. THE System SHALL implement full-text search using PostgreSQL text search capabilities

### Requirement 10: Personalized Content Recommendations

**User Story:** As a reader, I want personalized story recommendations, so that I discover content aligned with my interests.

#### Acceptance Criteria

1. WHEN a user saves a story, THE System SHALL increment Interest_Score for associated tags and author
2. WHEN a user completes reading a chapter, THE System SHALL increment Interest_Score for associated tags and author
3. WHEN a user likes a Whisper, THE System SHALL increment Interest_Score for associated story tags
4. WHEN a user follows an author, THE System SHALL increment Interest_Score for that author
5. THE System SHALL calculate For_You_Feed ranking using weighted combination of Interest_Score, Trending_Score, and freshness
6. THE System SHALL apply daily score decay of 0.98 to all Interest_Scores
7. WHEN a user has no interaction history, THE System SHALL return Trending feed as fallback
8. THE System SHALL recompute For_You_Feed rankings as background job with 1-6 hour frequency
9. THE System SHALL exclude blocked authors and soft-deleted content from For_You_Feed

### Requirement 11: Social Following and Blocking

**User Story:** As a user, I want to follow authors I like and block users I don't want to interact with, so that I can curate my social experience.

#### Acceptance Criteria

1. WHEN a user follows another user, THE System SHALL create a Follow record with follower_id and following_id
2. WHEN a user unfollows another user, THE System SHALL delete the corresponding Follow record
3. WHEN a user blocks another user, THE System SHALL create a Block record with blocker_id and blocked_id
4. WHEN a user unblocks another user, THE System SHALL delete the corresponding Block record
5. WHEN a user requests content feeds, THE System SHALL exclude all content from blocked users
6. WHEN a user requests search results, THE System SHALL exclude all content from blocked users
7. THE System SHALL prevent a user from following a user they have blocked
8. THE System SHALL prevent duplicate follow relationships between the same users
9. WHEN a user blocks another user, THE System SHALL automatically remove any existing follow relationship

### Requirement 12: Notifications System

**User Story:** As a user, I want to receive notifications for replies and follows, so that I stay informed about community interactions.

#### Acceptance Criteria

1. WHEN a user receives a reply to their Whisper, THE System SHALL create an in-app Notification with type REPLY
2. WHEN a user is followed, THE System SHALL create an in-app Notification with type FOLLOW
3. WHEN a user requests notifications, THE System SHALL return unread notifications ordered by creation time descending
4. WHEN a user marks a notification as read, THE System SHALL update the read_at timestamp
5. WHEN a user receives a reply notification, THE System SHALL send an email via Resend with idempotency key
6. THE System SHALL process email notifications as background Celery jobs
7. THE System SHALL include unsubscribe link in all notification emails
8. WHEN a notification email fails, THE System SHALL retry with exponential backoff
9. THE System SHALL not send duplicate notifications for the same event using idempotency keys

### Requirement 13: Content Reporting and Moderation

**User Story:** As a user, I want to report inappropriate content, so that the platform remains safe and respectful.

#### Acceptance Criteria

1. WHEN a user reports a story, THE System SHALL create a Report record with story_id, reason, and reporter_id
2. WHEN a user reports a chapter, THE System SHALL create a Report record with chapter_id, reason, and reporter_id
3. WHEN a user reports a Whisper, THE System SHALL create a Report record with whisper_id, reason, and reporter_id
4. WHEN a user reports another user, THE System SHALL create a Report record with reported_user_id, reason, and reporter_id
5. THE System SHALL store report creation timestamp and status (pending, reviewed, resolved)
6. THE System SHALL prevent duplicate reports from the same user for the same content
7. WHEN a report is created, THE System SHALL accept reason text with maximum 500 characters

### Requirement 14: Media Upload System

**User Story:** As a user, I want to upload images for avatars, covers, and whispers, so that I can personalize my content.

#### Acceptance Criteria

1. WHEN a user requests a Presigned_Upload URL, THE System SHALL generate a signed S3 URL with 15-minute expiration
2. WHEN generating avatar upload URL, THE System SHALL enforce 2MB maximum file size
3. WHEN generating story cover upload URL, THE System SHALL enforce 5MB maximum file size
4. WHEN generating whisper media upload URL, THE System SHALL enforce 10MB maximum file size
5. THE System SHALL validate file type as image (JPEG, PNG, WebP, GIF)
6. WHEN a user completes upload, THE System SHALL store the S3 object key in the corresponding entity
7. THE System SHALL generate unique object keys using UUID to prevent collisions
8. THE System SHALL configure S3 bucket with public read access for uploaded media

### Requirement 15: Rate Limiting and Abuse Prevention

**User Story:** As a platform operator, I want to enforce rate limits, so that I prevent spam and abuse.

#### Acceptance Criteria

1. THE System SHALL enforce rate limit of 10 whispers per minute per user
2. THE System SHALL enforce rate limit of 20 replies per minute per user
3. THE System SHALL enforce rate limit of 5 publish operations per hour per author
4. WHEN a rate limit is exceeded, THE System SHALL return HTTP 429 status with retry-after header
5. THE System SHALL implement rate limiting using Valkey with sliding window algorithm
6. THE System SHALL reset rate limit counters after the time window expires
7. THE System SHALL apply rate limits per user based on clerk_user_id

### Requirement 16: Trending Score Calculation

**User Story:** As a reader, I want to see trending stories based on recent engagement, so that I discover popular content.

#### Acceptance Criteria

1. THE System SHALL calculate Trending_Score using weighted combination of saves, reads, likes, and whispers within 24 hours
2. THE System SHALL apply time decay factor of 0.98 per hour to engagement metrics
3. THE System SHALL recompute Trending_Score as background Celery job every 10-30 minutes
4. WHEN a story receives engagement, THE System SHALL increment the corresponding engagement counter
5. THE System SHALL store daily aggregated stats in StoryStatsDaily table
6. THE System SHALL exclude soft-deleted stories from trending calculations
7. WHEN Trending feed is requested, THE System SHALL return stories ordered by Trending_Score descending

### Requirement 17: API Structure and Versioning

**User Story:** As a client developer, I want a well-structured versioned API, so that I can build reliable integrations.

#### Acceptance Criteria

1. THE System SHALL prefix all API endpoints with /v1
2. THE System SHALL return JSON responses with consistent structure including data and error fields
3. WHEN an error occurs, THE System SHALL return appropriate HTTP status code and error message
4. THE System SHALL implement CORS headers for cross-origin requests from frontend domain
5. THE System SHALL validate request payloads against defined schemas
6. WHEN validation fails, THE System SHALL return HTTP 400 with detailed validation errors
7. THE System SHALL require authentication header for all protected endpoints
8. WHEN authentication fails, THE System SHALL return HTTP 401 with error message

### Requirement 18: Cursor-Based Pagination

**User Story:** As a user, I want smooth infinite scrolling through feeds, so that I can browse content seamlessly.

#### Acceptance Criteria

1. THE System SHALL implement Cursor_Pagination for all list endpoints
2. WHEN a paginated request is made, THE System SHALL return results array and next_cursor field
3. WHEN next_cursor is null, THE System SHALL indicate no more results available
4. WHEN a client provides a cursor, THE System SHALL return results after that cursor position
5. THE System SHALL encode cursor as opaque base64 string containing sort key and offset
6. THE System SHALL maintain stable ordering within pagination session
7. THE System SHALL default page size to 20 items when not specified
8. THE System SHALL enforce maximum page size of 100 items

### Requirement 19: Background Job Processing

**User Story:** As a platform operator, I want background jobs to handle async tasks, so that the system remains responsive.

#### Acceptance Criteria

1. THE System SHALL process email notifications as Celery background jobs
2. THE System SHALL recompute trending lists as scheduled Celery tasks every 10-30 minutes
3. THE System SHALL update user Interest_Scores as Celery background jobs
4. THE System SHALL apply daily score decay as scheduled Celery task
5. WHEN a background job fails, THE System SHALL retry with exponential backoff up to 3 attempts
6. THE System SHALL log all background job executions with status and duration
7. THE System SHALL use Valkey as Celery broker and result backend

### Requirement 20: Data Consistency and Integrity

**User Story:** As a platform operator, I want data consistency guarantees, so that the system maintains integrity.

#### Acceptance Criteria

1. THE System SHALL use database transactions for multi-step operations
2. WHEN a story is deleted, THE System SHALL preserve associated chapters, whispers, and highlights
3. WHEN a user is deleted, THE System SHALL perform Soft_Delete on all user-created content
4. THE System SHALL enforce foreign key constraints between related entities
5. THE System SHALL validate data types and constraints at database level
6. WHEN concurrent updates occur, THE System SHALL use optimistic locking to prevent conflicts
7. THE System SHALL maintain referential integrity between UserProfile and clerk_user_id

### Requirement 21: Caching Strategy

**User Story:** As a platform operator, I want intelligent caching, so that the system performs efficiently.

#### Acceptance Criteria

1. THE System SHALL cache Discover feeds with TTL between 1-5 minutes
2. THE System SHALL cache Trending feed with TTL between 1-5 minutes
3. THE System SHALL cache Whispers feeds with TTL between 30-120 seconds
4. THE System SHALL cache story metadata with TTL between 5-15 minutes
5. THE System SHALL cache search suggestions with TTL between 10-30 minutes
6. THE System SHALL cache For_You_Feed with TTL between 1-6 hours
7. WHEN cached content is updated, THE System SHALL invalidate relevant cache keys
8. THE System SHALL use Valkey for all caching operations
9. WHEN cache is unavailable, THE System SHALL fallback to database queries

### Requirement 22: Health Monitoring

**User Story:** As a platform operator, I want health check endpoints, so that I can monitor system status.

#### Acceptance Criteria

1. THE System SHALL provide GET /v1/health endpoint returning system status
2. WHEN health check is requested, THE System SHALL verify database connectivity
3. WHEN health check is requested, THE System SHALL verify Valkey connectivity
4. WHEN all dependencies are healthy, THE System SHALL return HTTP 200 with status "healthy"
5. WHEN any dependency is unhealthy, THE System SHALL return HTTP 503 with status "unhealthy"
6. THE System SHALL include response time and timestamp in health check response
7. THE System SHALL not require authentication for health check endpoint

### Requirement 23: Mobile Responsiveness

**User Story:** As a mobile user, I want the interface to work seamlessly on my device, so that I can use the platform anywhere.

#### Acceptance Criteria

1. THE System SHALL render all views responsively across mobile, tablet, and desktop screen sizes
2. THE System SHALL enable one-handed mobile usability with primary actions in thumb-reach zone
3. THE System SHALL maintain readable typography with minimum 16px base font size on mobile
4. WHEN a user interacts with touch targets, THE System SHALL provide minimum 44x44px tap areas
5. THE System SHALL optimize images for mobile bandwidth with responsive image loading
6. THE System SHALL maintain stable navigation bar position during scroll on mobile
7. THE System SHALL support swipe gestures for navigation where appropriate

### Requirement 24: Typography and Visual Design

**User Story:** As a user, I want a beautiful typography-first interface, so that reading is comfortable and enjoyable.

#### Acceptance Criteria

1. THE System SHALL use typography-first design with clear hierarchy and generous whitespace
2. THE System SHALL avoid dense sidebars in reader view
3. THE System SHALL limit primary actions to maximum 2 per view
4. THE System SHALL use soft separators instead of heavy borders
5. THE System SHALL maintain consistent top navigation across all views
6. THE System SHALL provide light and dark theme options
7. THE System SHALL use system fonts for optimal performance and native feel
8. THE System SHALL maintain optimal line length between 50-75 characters in reader view
