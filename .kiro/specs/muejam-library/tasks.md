# Implementation Plan: MueJam Library

## Overview

This implementation plan breaks down the MueJam Library platform into discrete, actionable coding tasks. The platform is a full-stack digital library for serial stories with an integrated micro-posting system. The implementation follows a monorepo structure with Next.js frontend, Django backend, PostgreSQL database, and supporting infrastructure.

## Technology Stack

- **Frontend**: Next.js 14 (App Router), React, Tailwind CSS
- **Backend**: Django 5.x, Django REST Framework
- **Database**: PostgreSQL 15+ with Prisma ORM
- **Cache/Queue**: Valkey (Redis-compatible)
- **Authentication**: Clerk
- **Email**: Resend API
- **Storage**: AWS S3
- **Background Jobs**: Celery
- **Testing**: pytest, hypothesis (property-based testing)

## Tasks

- [-] 1. Project Setup and Infrastructure
  - Initialize monorepo structure with frontend and backend directories
  - Set up Docker Compose for local development (PostgreSQL, Valkey)
  - Configure environment variables and secrets management
  - Set up Git repository with .gitignore for Python and Node.js
  - _Requirements: 17.1, 22.1_

- [ ] 2. Database Schema and Migrations
  - [~] 2.1 Create Prisma schema with all models
    - Define UserProfile, Story, Chapter, Tag, StoryTag models
    - Define Shelf, ShelfItem, ReadingProgress, Bookmark models
    - Define Highlight, Whisper, WhisperLike models
    - Define Follow, Block, Notification, Report models
    - Define UserInterest, StoryStatsDaily models
    - Add all indexes and unique constraints
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 11.1, 12.1, 13.1, 16.1_

  - [ ]* 2.2 Write property test for Prisma schema validation
    - **Property 2: Handle Uniqueness**
    - **Validates: Requirements 1.3**

  - [~] 2.3 Generate Prisma Client Python and run initial migration
    - Generate Prisma client for Python
    - Create initial database migration
    - Apply migration to local PostgreSQL instance
    - _Requirements: 20.4, 20.5_

- [ ] 3. Django Backend Setup
  - [~] 3.1 Initialize Django project with app structure
    - Create Django project with config directory
    - Create apps: users, stories, library, whispers, highlights, social, notifications, discovery, search, uploads, moderation, core
    - Configure Django settings for PostgreSQL, Valkey, Celery
    - Set up CORS configuration for frontend domain
    - _Requirements: 17.4_

  - [~] 3.2 Configure Clerk authentication middleware
    - Install clerk-backend-api Python SDK
    - Implement ClerkAuthMiddleware for JWT verification
    - Add middleware to extract clerk_user_id from requests
    - Create get_or_create_profile helper function
    - _Requirements: 1.1, 1.2_

  - [ ]* 3.3 Write property test for authentication middleware
    - **Property 1: Authentication Profile Creation**
    - **Validates: Requirements 1.2**

  - [~] 3.4 Implement core utilities
    - Create cursor pagination class (CursorPagination)
    - Create rate limiting decorator with Valkey backend
    - Create cache manager with TTL configurations
    - Create custom exception classes
    - _Requirements: 2.6, 15.1, 21.1_

  - [ ]* 3.5 Write property test for cursor pagination
    - **Property 4: Cursor Pagination Completeness**
    - **Validates: Requirements 2.6, 2.7**

  - [ ]* 3.6 Write property test for rate limiting
    - **Property 12: Rate Limit Enforcement**
    - **Validates: Requirements 6.4, 15.4**

- [~] 4. Checkpoint - Ensure backend setup is complete
  - Verify Django server starts successfully
  - Verify database connection works
  - Verify Valkey connection works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. User Profile Management
  - [~] 5.1 Implement UserProfile model operations
    - Create serializers for UserProfile (read/write)
    - Implement GET /v1/me endpoint (retrieve current user)
    - Implement PUT /v1/me endpoint (update profile)
    - Implement GET /v1/users/{handle} endpoint (public profile)
    - Add handle format validation (alphanumeric + underscore, 3-30 chars)
    - Add handle uniqueness validation
    - _Requirements: 1.3, 1.4, 1.5_

  - [ ]* 5.2 Write property test for handle validation
    - **Property 3: Handle Format Validation**
    - **Validates: Requirements 1.5**

  - [ ]* 5.3 Write unit tests for profile endpoints
    - Test profile creation on first authentication
    - Test profile update with valid data
    - Test handle uniqueness constraint
    - Test invalid handle format rejection
    - _Requirements: 1.2, 1.3, 1.5_

- [ ] 6. Story and Chapter Management
  - [~] 6.1 Implement Story CRUD operations
    - Create serializers for Story (list/detail/create/update)
    - Implement POST /v1/stories (create draft)
    - Implement GET /v1/stories (list with filters)
    - Implement GET /v1/stories/{slug} (get by slug)
    - Implement PUT /v1/stories/{id} (update draft)
    - Implement DELETE /v1/stories/{id} (soft delete)
    - Implement POST /v1/stories/{id}/publish (publish story)
    - Add slug generation from title
    - _Requirements: 5.1, 5.3, 5.5, 5.6_

  - [ ]* 6.2 Write property test for soft delete behavior
    - **Property 10: Soft Delete Behavior**
    - **Validates: Requirements 5.6, 6.5, 20.2**

  - [~] 6.3 Implement Chapter CRUD operations
    - Create serializers for Chapter (list/detail/create/update)
    - Implement GET /v1/stories/{id}/chapters (list chapters)
    - Implement GET /v1/chapters/{id} (get chapter content)
    - Implement POST /v1/stories/{id}/chapters (create draft)
    - Implement PUT /v1/chapters/{id} (update draft)
    - Implement DELETE /v1/chapters/{id} (soft delete)
    - Implement POST /v1/chapters/{id}/publish (publish chapter)
    - _Requirements: 5.2, 5.4, 5.7_

  - [ ]* 6.4 Write property test for publication status
    - **Property 9: Publication Status Update**
    - **Validates: Requirements 5.3**

  - [~] 6.5 Implement markdown sanitization
    - Add markdown sanitization library (bleach or similar)
    - Sanitize story blurb and chapter content on save
    - Configure allowed HTML tags and attributes
    - _Requirements: 5.10_

  - [ ]* 6.6 Write property test for XSS sanitization
    - **Property 11: XSS Sanitization**
    - **Validates: Requirements 5.10**

  - [~] 6.7 Implement rate limiting for publish operations
    - Add rate limit decorator to publish endpoints (5 per hour)
    - Return HTTP 429 with retry-after header on limit exceeded
    - _Requirements: 5.8, 15.3_

  - [ ]* 6.8 Write unit tests for story and chapter operations
    - Test story creation and retrieval
    - Test chapter creation with chapter_number
    - Test publish operation updates published_at
    - Test soft delete sets deleted_at
    - Test rate limit enforcement
    - _Requirements: 5.1, 5.2, 5.3, 5.6, 5.8_

- [ ] 7. Library and Shelf Management
  - [~] 7.1 Implement Shelf operations
    - Create serializers for Shelf and ShelfItem
    - Implement GET /v1/library/shelves (list user shelves)
    - Implement POST /v1/library/shelves (create shelf)
    - Implement PUT /v1/library/shelves/{id} (rename shelf)
    - Implement DELETE /v1/library/shelves/{id} (delete shelf)
    - _Requirements: 4.1, 4.5, 4.7_

  - [~] 7.2 Implement ShelfItem operations
    - Implement POST /v1/library/shelves/{id}/items (add story)
    - Implement DELETE /v1/library/shelves/{id}/items/{story_id} (remove story)
    - Implement GET /v1/library (get all shelves with stories)
    - _Requirements: 4.2, 4.3, 4.4_

  - [ ]* 7.3 Write property test for shelf item operations
    - **Property 6: Shelf Item Addition**
    - **Property 7: Shelf Item Removal Idempotence**
    - **Validates: Requirements 4.2, 4.3**

  - [ ]* 7.4 Write property test for multi-shelf membership
    - **Property 8: Multi-Shelf Story Membership**
    - **Validates: Requirements 4.6**

  - [ ]* 7.5 Write unit tests for library operations
    - Test shelf creation and retrieval
    - Test adding story to shelf
    - Test removing story from shelf
    - Test story in multiple shelves
    - Test shelf deletion removes ShelfItems
    - _Requirements: 4.1, 4.2, 4.3, 4.5, 4.6_

- [~] 8. Checkpoint - Ensure core content management works
  - Verify story and chapter CRUD operations
  - Verify library and shelf operations
  - Verify soft delete behavior
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Reading Progress and Bookmarks
  - [~] 9.1 Implement ReadingProgress tracking
    - Create serializers for ReadingProgress
    - Implement POST /v1/chapters/{id}/progress (update progress)
    - Implement GET /v1/chapters/{id}/progress (get progress)
    - Add debouncing logic for frequent updates
    - _Requirements: 3.4, 3.5_

  - [ ]* 9.2 Write property test for progress round trip
    - **Property 5: Reading Progress Round Trip**
    - **Validates: Requirements 3.4, 3.5**

  - [~] 9.3 Implement Bookmark operations
    - Create serializers for Bookmark
    - Implement POST /v1/chapters/{id}/bookmarks (create bookmark)
    - Implement GET /v1/chapters/{id}/bookmarks (list bookmarks)
    - Implement DELETE /v1/bookmarks/{id} (delete bookmark)
    - _Requirements: 3.6_

  - [ ]* 9.4 Write unit tests for reading progress and bookmarks
    - Test progress update and retrieval
    - Test bookmark creation and deletion
    - Test multiple bookmarks per chapter
    - _Requirements: 3.4, 3.5, 3.6_

- [ ] 10. Highlights System
  - [~] 10.1 Implement Highlight operations
    - Create serializers for Highlight
    - Implement POST /v1/chapters/{id}/highlights (create highlight)
    - Implement GET /v1/chapters/{id}/highlights (list highlights)
    - Implement DELETE /v1/highlights/{id} (delete highlight)
    - Add validation for start_offset < end_offset
    - Add validation for offsets within chapter content length
    - _Requirements: 8.1, 8.2, 8.5, 8.7, 8.8_

  - [ ]* 10.2 Write property test for highlight offset validation
    - **Property 16: Highlight Offset Validation**
    - **Validates: Requirements 8.7, 8.8**

  - [ ]* 10.3 Write property test for highlight storage
    - **Property 17: Highlight Storage Completeness**
    - **Validates: Requirements 8.2**

  - [ ]* 10.4 Write unit tests for highlights
    - Test highlight creation with valid offsets
    - Test highlight rejection with invalid offsets
    - Test highlight retrieval for chapter
    - Test highlight deletion
    - _Requirements: 8.1, 8.2, 8.5, 8.7, 8.8_

- [ ] 11. Whispers Micro-Posting System
  - [~] 11.1 Implement Whisper CRUD operations
    - Create serializers for Whisper (with scope handling)
    - Implement POST /v1/whispers (create whisper)
    - Implement GET /v1/whispers (list with scope filter)
    - Implement DELETE /v1/whispers/{id} (soft delete)
    - Add content sanitization for XSS prevention
    - Add rate limiting (10 whispers per minute)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.10_

  - [~] 11.2 Implement Whisper replies
    - Implement POST /v1/whispers/{id}/replies (create reply)
    - Implement GET /v1/whispers/{id}/replies (list replies)
    - Add rate limiting (20 replies per minute)
    - Handle parent_whisper_id relationship
    - _Requirements: 7.1, 7.2, 7.6, 7.8_

  - [~] 11.3 Implement Whisper likes
    - Create serializers for WhisperLike
    - Implement POST /v1/whispers/{id}/like (like whisper)
    - Implement DELETE /v1/whispers/{id}/like (unlike whisper)
    - Add duplicate like prevention
    - Include like count in whisper serializer
    - _Requirements: 7.3, 7.4, 7.5, 7.7_

  - [ ]* 11.4 Write property test for whisper like operations
    - **Property 13: Whisper Like Creation**
    - **Property 14: Whisper Like Round Trip**
    - **Property 15: Duplicate Like Prevention**
    - **Validates: Requirements 7.3, 7.4, 7.7**

  - [~] 11.5 Implement whisper feeds with caching
    - Add cache layer for global whispers feed (TTL: 60s)
    - Add cache layer for story-specific whispers (TTL: 60s)
    - Implement cache invalidation on whisper creation
    - _Requirements: 6.6, 6.7, 6.8, 21.3_

  - [ ]* 11.6 Write unit tests for whispers
    - Test whisper creation with different scopes
    - Test reply creation and retrieval
    - Test like/unlike operations
    - Test rate limiting enforcement
    - Test soft delete behavior
    - Test feed caching
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.3, 7.4_

- [ ] 12. Social Features (Follow and Block)
  - [~] 12.1 Implement Follow operations
    - Create serializers for Follow
    - Implement POST /v1/users/{id}/follow (follow user)
    - Implement DELETE /v1/users/{id}/follow (unfollow user)
    - Implement GET /v1/users/{id}/followers (list followers)
    - Implement GET /v1/users/{id}/following (list following)
    - Add duplicate follow prevention
    - _Requirements: 11.1, 11.2, 11.8_

  - [ ]* 12.2 Write property test for follow operations
    - **Property 20: Follow Relationship Creation**
    - **Property 21: Follow Relationship Round Trip**
    - **Property 23: Duplicate Follow Prevention**
    - **Validates: Requirements 11.1, 11.2, 11.8**

  - [~] 12.3 Implement Block operations
    - Create serializers for Block
    - Implement POST /v1/users/{id}/block (block user)
    - Implement DELETE /v1/users/{id}/block (unblock user)
    - Add logic to remove follow relationship on block
    - Add validation to prevent following blocked users
    - _Requirements: 11.3, 11.4, 11.7, 11.9_

  - [ ]* 12.4 Write property test for block operations
    - **Property 22: Block Prevents Follow**
    - **Property 24: Block Removes Follow**
    - **Validates: Requirements 11.7, 11.9**

  - [~] 12.5 Implement content filtering for blocked users
    - Add blocked user filter to story queries
    - Add blocked user filter to whisper queries
    - Add blocked user filter to search queries
    - _Requirements: 11.5, 11.6_

  - [ ]* 12.6 Write property test for blocked content exclusion
    - **Property 18: Deleted Content Exclusion**
    - **Validates: Requirements 9.6, 16.6**

  - [ ]* 12.7 Write unit tests for social features
    - Test follow/unfollow operations
    - Test block/unblock operations
    - Test block removes follow
    - Test blocked user content filtering
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.7, 11.9_

- [~] 13. Checkpoint - Ensure social and interaction features work
  - Verify whisper creation and feeds
  - Verify follow/block operations
  - Verify content filtering for blocked users
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. Notifications System
  - [~] 14.1 Implement Notification model operations
    - Create serializers for Notification
    - Implement GET /v1/notifications (list notifications)
    - Implement POST /v1/notifications/{id}/read (mark as read)
    - Implement POST /v1/notifications/read-all (mark all as read)
    - Add notification creation on reply and follow events
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

  - [~] 14.2 Set up Celery for background jobs
    - Configure Celery with Valkey broker
    - Create celery.py configuration file
    - Set up Celery Beat for scheduled tasks
    - _Requirements: 19.1, 19.7_

  - [~] 14.3 Implement email notification task
    - Install Resend Python SDK
    - Create send_notification_email Celery task
    - Implement idempotency key generation
    - Add retry logic with exponential backoff (max 3 retries)
    - Create email templates for REPLY and FOLLOW notifications
    - Add unsubscribe link to emails
    - _Requirements: 12.5, 12.6, 12.7, 12.8, 19.5_

  - [ ]* 14.4 Write property test for notification idempotency
    - **Property 25: Notification Idempotency**
    - **Validates: Requirements 12.9**

  - [ ]* 14.5 Write unit tests for notifications
    - Test notification creation on reply
    - Test notification creation on follow
    - Test mark as read functionality
    - Test email task execution
    - Test idempotency key prevents duplicates
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.9_

- [ ] 15. Discovery Feeds
  - [~] 15.1 Implement Trending feed
    - Create TrendingCalculator class
    - Implement calculate_trending_score method
    - Create GET /v1/discover?tab=trending endpoint
    - Add caching with TTL (3-5 minutes)
    - _Requirements: 2.2, 16.1, 16.2, 16.7, 21.2_

  - [~] 15.2 Implement New feed
    - Create GET /v1/discover?tab=new endpoint
    - Order by published_at descending
    - Add caching with TTL (3-5 minutes)
    - _Requirements: 2.3, 21.1_

  - [~] 15.3 Implement For You personalized feed
    - Create PersonalizationEngine class
    - Implement calculate_story_score method
    - Implement get_for_you_feed method
    - Add cold start detection and fallback to trending
    - Create GET /v1/discover?tab=for-you endpoint
    - Add caching with TTL (1-6 hours)
    - _Requirements: 2.4, 2.5, 10.5, 10.7, 21.6_

  - [~] 15.4 Implement UserInterest tracking
    - Create update_interests method in PersonalizationEngine
    - Track saves, reads, likes, follows as interest signals
    - Update tag and author interest scores
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [~] 15.5 Implement tag filtering and search
    - Add tag filter to discover endpoints
    - Add search query parameter for text search
    - _Requirements: 2.10, 2.11_

  - [ ]* 15.6 Write unit tests for discovery feeds
    - Test trending feed returns high-engagement stories
    - Test new feed returns recent stories
    - Test for you feed with sufficient history
    - Test cold start fallback to trending
    - Test tag filtering
    - Test search functionality
    - _Requirements: 2.2, 2.3, 2.4, 2.5, 2.10, 2.11_

- [ ] 16. Background Jobs for Personalization
  - [~] 16.1 Implement trending score update task
    - Create update_trending_scores Celery task
    - Schedule to run every 10-30 minutes
    - Update StoryStatsDaily with new scores
    - _Requirements: 16.3, 19.2_

  - [~] 16.2 Implement daily interest decay task
    - Create apply_daily_decay Celery task
    - Schedule to run every 24 hours
    - Multiply all UserInterest scores by 0.98
    - _Requirements: 10.6, 19.4_

  - [ ]* 16.3 Write property test for interest decay
    - **Property 19: Interest Score Decay**
    - **Validates: Requirements 10.6**

  - [ ]* 16.4 Write unit tests for background jobs
    - Test trending score calculation
    - Test daily decay application
    - Test job retry on failure
    - _Requirements: 16.1, 16.3, 19.2, 19.4, 19.5_

- [ ] 17. Search and Autocomplete
  - [~] 17.1 Implement full-text search
    - Set up PostgreSQL full-text search indexes
    - Create GET /v1/search endpoint
    - Search across story title, blurb, author name, tags
    - Rank results by relevance and trending score
    - Exclude soft-deleted and blocked content
    - _Requirements: 9.1, 9.5, 9.6, 9.7_

  - [~] 17.2 Implement autocomplete suggestions
    - Create GET /v1/search/suggest endpoint
    - Return suggestions for stories, tags, authors
    - Add caching with TTL (10-30 minutes)
    - _Requirements: 9.2, 9.3, 9.4, 21.5_

  - [ ]* 17.3 Write unit tests for search
    - Test full-text search across fields
    - Test search result ranking
    - Test autocomplete suggestions
    - Test exclusion of deleted/blocked content
    - Test suggestion caching
    - _Requirements: 9.1, 9.2, 9.5, 9.6, 9.7_

- [ ] 18. Media Upload System
  - [~] 18.1 Implement S3 presigned URL generation
    - Install boto3 Python SDK
    - Create S3UploadManager class
    - Implement generate_presigned_url method
    - Create POST /v1/uploads/presign endpoint
    - Add file type validation (JPEG, PNG, WebP, GIF)
    - Add size limits based on upload type (avatar: 2MB, cover: 5MB, whisper: 10MB)
    - Generate unique object keys using UUID
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.7_

  - [ ]* 18.2 Write property test for UUID uniqueness
    - **Property 27: UUID Uniqueness**
    - **Validates: Requirements 14.7**

  - [ ]* 18.3 Write unit tests for media uploads
    - Test presigned URL generation
    - Test file type validation
    - Test size limit enforcement
    - Test UUID uniqueness
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.7_

- [ ] 19. Content Moderation
  - [~] 19.1 Implement Report submission
    - Create serializers for Report
    - Implement POST /v1/reports endpoint
    - Support reporting stories, chapters, whispers, users
    - Add duplicate report prevention
    - Validate reason text (max 500 characters)
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_

  - [ ]* 19.2 Write property test for duplicate report prevention
    - **Property 26: Duplicate Report Prevention**
    - **Validates: Requirements 13.6**

  - [ ]* 19.3 Write unit tests for moderation
    - Test report creation for different content types
    - Test duplicate report prevention
    - Test reason text validation
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.6, 13.7_

- [~] 20. Checkpoint - Ensure discovery and moderation features work
  - Verify discovery feeds (trending, new, for you)
  - Verify search and autocomplete
  - Verify media upload presigned URLs
  - Verify report submission
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 21. API Error Handling and Validation
  - [~] 21.1 Implement consistent error response format
    - Create custom exception handler for DRF
    - Return JSON with error code, message, and details
    - Map Django/DRF exceptions to appropriate HTTP status codes
    - _Requirements: 17.2, 17.3_

  - [~] 21.2 Implement request validation
    - Add DRF serializer validation for all endpoints
    - Return HTTP 400 with detailed validation errors
    - _Requirements: 17.5, 17.6_

  - [ ]* 21.3 Write property test for validation error responses
    - **Property 28: Validation Error Response**
    - **Validates: Requirements 17.6**

  - [~] 21.4 Add authentication error handling
    - Return HTTP 401 for missing/invalid tokens
    - Return HTTP 403 for authorization failures
    - _Requirements: 17.7, 17.8_

  - [ ]* 21.5 Write unit tests for error handling
    - Test validation error format
    - Test authentication errors
    - Test authorization errors
    - Test rate limit errors
    - Test resource not found errors
    - _Requirements: 17.2, 17.3, 17.6, 17.7, 17.8_

- [ ] 22. Health Check and Monitoring
  - [~] 22.1 Implement health check endpoint
    - Create GET /v1/health endpoint (no auth required)
    - Check PostgreSQL connectivity
    - Check Valkey connectivity
    - Return HTTP 200 with "healthy" status when all dependencies are up
    - Return HTTP 503 with "unhealthy" status when any dependency is down
    - Include response time and timestamp
    - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6, 22.7_

  - [ ]* 22.2 Write unit tests for health check
    - Test healthy status when all dependencies are up
    - Test unhealthy status when database is down
    - Test unhealthy status when cache is down
    - _Requirements: 22.2, 22.3, 22.4, 22.5_

- [ ] 23. API Documentation
  - [~] 23.1 Set up OpenAPI/Swagger documentation
    - Install drf-spectacular
    - Configure OpenAPI schema generation
    - Add endpoint descriptions and examples
    - Generate API documentation at /v1/docs
    - _Requirements: 17.1_

- [ ] 24. Next.js Frontend Setup
  - [~] 24.1 Initialize Next.js project with App Router
    - Create Next.js 14 project with TypeScript
    - Set up Tailwind CSS configuration
    - Configure environment variables for API URL
    - Set up app directory structure
    - _Requirements: 23.1_

  - [~] 24.2 Set up Clerk authentication
    - Install @clerk/nextjs package
    - Configure Clerk provider in root layout
    - Create sign-in and sign-up pages
    - Set up middleware for protected routes
    - _Requirements: 1.1_

  - [~] 24.3 Create main layout and navigation
    - Implement main layout with top navigation
    - Add navigation links (Discover, Library, Write, Whispers, Profile)
    - Make navigation responsive for mobile
    - Ensure navigation is consistent across all views
    - _Requirements: 3.8, 23.6_

- [ ] 25. Frontend API Client
  - [~] 25.1 Create API client utility
    - Create fetch wrapper with authentication headers
    - Add error handling and response parsing
    - Create typed API functions for all endpoints
    - Add request/response interceptors
    - _Requirements: 17.1, 17.7_

  - [~] 25.2 Implement cursor pagination helper
    - Create usePagination hook for infinite scroll
    - Handle cursor state and next page loading
    - _Requirements: 18.1, 18.2_

- [ ] 26. Discover Feed Pages
  - [~] 26.1 Create Discover page with tabs
    - Implement /discover page with Trending, New, For You tabs
    - Create StoryCard component (cover, title, author, tags)
    - Implement infinite scroll with cursor pagination
    - Add tab state management
    - Cache feed results client-side
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [~] 26.2 Add tag filtering and search
    - Add tag filter UI to discover page
    - Add search input with autocomplete
    - Implement search results page
    - _Requirements: 2.10, 2.11, 9.1, 9.2_

  - [ ]* 26.3 Write integration tests for discover feed
    - Test tab switching
    - Test infinite scroll loading
    - Test tag filtering
    - Test search functionality
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.10, 2.11_

- [ ] 27. Story and Chapter Reading Pages
  - [~] 27.1 Create Story detail page
    - Implement /stories/[slug] page
    - Display cover image, title, blurb, tags, author info
    - List all published chapters
    - Add "Add to Shelf" button
    - _Requirements: 3.1_

  - [~] 27.2 Create Chapter reader page
    - Implement /stories/[slug]/chapters/[id] page
    - Display chapter content in distraction-free view
    - Limit to 2 primary actions (bookmark, settings)
    - Add reading progress tracking on scroll (debounced)
    - _Requirements: 3.2, 3.4, 3.7_

  - [~] 27.3 Implement reader customization settings
    - Add settings panel for font size (14-24px)
    - Add theme toggle (light/dark)
    - Add line width adjustment (600-800px)
    - Persist settings in localStorage
    - _Requirements: 3.3_

  - [~] 27.4 Implement text highlighting
    - Add text selection handler
    - Show highlight context menu on selection
    - Save highlight with start/end offsets
    - Display existing highlights in chapter
    - _Requirements: 8.1, 8.2, 8.4_

  - [ ]* 27.5 Write integration tests for reading experience
    - Test chapter content display
    - Test reading progress tracking
    - Test reader settings persistence
    - Test text highlighting
    - _Requirements: 3.2, 3.3, 3.4, 8.1, 8.2_

- [~] 28. Checkpoint - Ensure frontend reading experience works
  - Verify discover feed displays correctly
  - Verify story and chapter pages render
  - Verify reader customization works
  - Verify text highlighting works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 29. Library Management Pages
  - [~] 29.1 Create Library page
    - Implement /library page
    - Display all user shelves with story counts
    - Add "Create Shelf" button
    - Show stories in each shelf
    - _Requirements: 4.4_

  - [~] 29.2 Implement shelf management UI
    - Create ShelfManager component
    - Add shelf creation modal
    - Add shelf rename functionality
    - Add shelf deletion with confirmation
    - Add story removal from shelf
    - _Requirements: 4.1, 4.3, 4.5, 4.7_

  - [ ]* 29.3 Write integration tests for library
    - Test shelf creation
    - Test adding story to shelf
    - Test removing story from shelf
    - Test shelf deletion
    - _Requirements: 4.1, 4.2, 4.3, 4.5_

- [ ] 30. Author Writing Pages
  - [~] 30.1 Create Write dashboard page
    - Implement /write page
    - List user's stories (drafts and published)
    - Add "New Story" button
    - Show story status (draft/published)
    - _Requirements: 5.1_

  - [~] 30.2 Create Story editor page
    - Implement /write/stories/[id] page
    - Add form for title, blurb, cover upload
    - Add tag selection/creation
    - Add "Save Draft" and "Publish" buttons
    - Show list of chapters with edit links
    - _Requirements: 5.1, 5.3, 5.5_

  - [~] 30.3 Create Chapter editor page
    - Implement /write/chapters/[id] page
    - Add markdown editor for chapter content
    - Add chapter title input
    - Add "Save Draft" and "Publish" buttons
    - Show preview of rendered markdown
    - _Requirements: 5.2, 5.4_

  - [~] 30.4 Implement media upload flow
    - Create upload component for cover images
    - Request presigned URL from backend
    - Upload directly to S3
    - Save object key to story/profile
    - Show upload progress
    - _Requirements: 14.1, 14.3_

  - [ ]* 30.5 Write integration tests for writing
    - Test story creation
    - Test chapter creation
    - Test story publishing
    - Test chapter publishing
    - Test cover image upload
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 14.1_

- [ ] 31. Whispers Pages
  - [~] 31.1 Create Whispers feed page
    - Implement /whispers page
    - Display global whispers feed
    - Add infinite scroll with cursor pagination
    - Show whisper content, author, timestamp
    - Display reply count and like count
    - _Requirements: 6.6_

  - [~] 31.2 Create WhisperComposer component
    - Add text input with 280 character limit
    - Add media upload button
    - Add scope selector (global/story/highlight)
    - Show character count
    - Add rate limit indicator
    - _Requirements: 6.1, 6.2, 6.3, 6.9_

  - [~] 31.3 Implement whisper interactions
    - Add reply button and reply thread view
    - Add like button with optimistic updates
    - Show reply count and like count
    - _Requirements: 7.1, 7.3, 7.5_

  - [~] 31.4 Add story-specific whispers
    - Show whispers on story detail page
    - Filter whispers by story_id
    - _Requirements: 6.7_

  - [~] 31.5 Add highlight-linked whispers
    - Show whispers attached to highlights in reader
    - Allow creating whisper from highlight
    - _Requirements: 8.3, 8.4_

  - [ ]* 31.6 Write integration tests for whispers
    - Test whisper creation
    - Test reply creation
    - Test like/unlike
    - Test whisper feeds
    - _Requirements: 6.1, 6.6, 7.1, 7.3_

- [ ] 32. User Profile Pages
  - [~] 32.1 Create Profile page
    - Implement /profile/[handle] page
    - Display avatar, display name, bio, handle
    - Show user's published stories
    - Add follow/unfollow button
    - Add block/unblock button
    - Show follower and following counts
    - _Requirements: 1.4, 11.1, 11.3_

  - [~] 32.2 Create Profile settings page
    - Implement /settings/profile page
    - Add form for display name, bio, handle
    - Add avatar upload
    - Validate handle format and uniqueness
    - _Requirements: 1.3, 1.5, 1.6_

  - [ ]* 32.3 Write integration tests for profile
    - Test profile display
    - Test profile editing
    - Test avatar upload
    - Test follow/unfollow
    - Test block/unblock
    - _Requirements: 1.3, 1.4, 11.1, 11.3_

- [ ] 33. Notifications Page
  - [~] 33.1 Create Notifications page
    - Implement /notifications page
    - Display list of notifications (replies, follows)
    - Show unread indicator
    - Add "Mark as Read" functionality
    - Add "Mark All as Read" button
    - Link to relevant content (whisper, profile)
    - _Requirements: 12.3, 12.4_

  - [ ]* 33.2 Write integration tests for notifications
    - Test notification display
    - Test mark as read
    - Test mark all as read
    - _Requirements: 12.3, 12.4_

- [~] 34. Checkpoint - Ensure all frontend pages work
  - Verify library management UI
  - Verify writing/editing pages
  - Verify whispers feed and interactions
  - Verify profile pages
  - Verify notifications page
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 35. Mobile Responsiveness
  - [~] 35.1 Implement responsive layouts
    - Make all pages responsive for mobile, tablet, desktop
    - Ensure navigation works on mobile (hamburger menu if needed)
    - Optimize touch targets for mobile (minimum 44x44px)
    - Test on various screen sizes
    - _Requirements: 23.1, 23.2, 23.4_

  - [~] 35.2 Optimize typography for mobile
    - Set minimum 16px base font size on mobile
    - Maintain optimal line length (50-75 characters) in reader
    - Test readability on small screens
    - _Requirements: 23.3, 24.8_

  - [~] 35.3 Implement responsive images
    - Use Next.js Image component for optimization
    - Add responsive image loading
    - Optimize for mobile bandwidth
    - _Requirements: 23.5_

  - [ ]* 35.4 Write property test for touch target sizes
    - **Property 33: Touch Target Minimum Size**
    - **Validates: Requirements 23.4**

- [ ] 36. Typography and Visual Design
  - [~] 36.1 Implement typography-first design
    - Set up typography scale with clear hierarchy
    - Use generous whitespace throughout
    - Avoid dense sidebars in reader view
    - Use soft separators instead of heavy borders
    - _Requirements: 24.1, 24.2, 24.4_

  - [~] 36.2 Implement theme system
    - Create light and dark theme CSS variables
    - Add theme toggle in settings
    - Persist theme preference in localStorage
    - Ensure consistent theme across all pages
    - _Requirements: 24.6_

  - [~] 36.3 Optimize for performance
    - Use system fonts for native feel
    - Minimize custom font loading
    - Optimize CSS bundle size
    - _Requirements: 24.7_

  - [ ]* 36.4 Write property test for primary action limit
    - **Property 34: Primary Action Limit**
    - **Validates: Requirements 24.3**

- [ ] 37. Caching and Performance Optimization
  - [~] 37.1 Implement backend caching strategy
    - Add cache layer to all discovery feeds
    - Add cache layer to whispers feeds
    - Add cache layer to story metadata
    - Add cache layer to search suggestions
    - Configure appropriate TTLs for each cache type
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6_

  - [~] 37.2 Implement cache invalidation
    - Invalidate discover feeds on story publish
    - Invalidate whispers feeds on whisper creation
    - Invalidate user profile cache on profile update
    - _Requirements: 21.7_

  - [ ]* 37.3 Write property test for cache invalidation
    - **Property 32: Cache Invalidation on Update**
    - **Validates: Requirements 21.7**

  - [~] 37.4 Implement graceful cache fallback
    - Fall back to database queries when cache is unavailable
    - Log cache failures for monitoring
    - _Requirements: 21.9_

  - [ ]* 37.5 Write unit tests for caching
    - Test cache hit and miss scenarios
    - Test cache invalidation
    - Test fallback to database
    - _Requirements: 21.1, 21.7, 21.9_

- [ ] 38. Database Transactions and Consistency
  - [~] 38.1 Implement transaction wrappers
    - Wrap multi-step operations in database transactions
    - Add rollback on error
    - _Requirements: 20.1_

  - [~] 38.2 Implement optimistic locking
    - Add version field to frequently updated models
    - Handle concurrent update conflicts
    - _Requirements: 20.6_

  - [ ]* 38.3 Write unit tests for data consistency
    - Test transaction rollback on error
    - Test concurrent update handling
    - Test foreign key constraints
    - _Requirements: 20.1, 20.4, 20.6_

- [ ] 39. Deployment Configuration
  - [~] 39.1 Create Docker configuration
    - Create Dockerfile for Django backend
    - Create Dockerfile for Next.js frontend
    - Create docker-compose.yml for local development
    - Include PostgreSQL, Valkey, Celery worker, Celery beat
    - _Requirements: Infrastructure_

  - [~] 39.2 Set up environment configuration
    - Create .env.example files for backend and frontend
    - Document all required environment variables
    - Set up secrets management for production
    - _Requirements: Infrastructure_

  - [~] 39.3 Create database seed data
    - Create seed script for development data
    - Add sample users, stories, chapters, whispers
    - Add sample tags and relationships
    - _Requirements: Development_

- [ ] 40. Integration Testing
  - [ ]* 40.1 Write end-to-end API tests
    - Test complete user flows (signup → create story → publish)
    - Test reading flow (discover → read → bookmark)
    - Test social flow (follow → whisper → reply)
    - Test library flow (create shelf → add story)
    - _Requirements: Multiple_

  - [ ]* 40.2 Write frontend integration tests
    - Test authentication flow
    - Test story creation and publishing flow
    - Test reading and highlighting flow
    - Test whisper creation and interaction flow
    - _Requirements: Multiple_

- [~] 41. Final Checkpoint - Complete system verification
  - Run all unit tests and property tests
  - Run all integration tests
  - Test complete user flows manually
  - Verify all API endpoints work correctly
  - Verify all frontend pages render correctly
  - Verify background jobs execute correctly
  - Verify email notifications are sent
  - Verify caching works correctly
  - Verify rate limiting works correctly
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout implementation
- Property tests validate universal correctness properties across randomized inputs
- Unit tests validate specific examples, edge cases, and integration points
- The implementation follows a bottom-up approach: infrastructure → backend → frontend
- Background jobs and caching are implemented alongside core features for optimal performance
- All content uses soft deletes to maintain data integrity and enable audit trails
