# Design Document: MueJam Library

## Overview

MueJam Library is a full-stack digital library platform built with a modern, scalable architecture. The system uses Next.js 14 (App Router) for the frontend, Django REST Framework for the backend API, PostgreSQL with Prisma for data persistence, and Valkey for caching and job queuing. The design emphasizes clean separation of concerns, efficient data access patterns, and a typography-first user experience.

### Key Design Principles

1. **API-First Architecture**: Frontend and backend communicate exclusively through versioned REST API
2. **Cursor-Based Pagination**: All list endpoints use opaque cursors for stable, efficient pagination
3. **Soft Deletes**: Content is never physically deleted, enabling audit trails and recovery
4. **Cache-Aside Pattern**: Valkey caches frequently accessed data with appropriate TTLs
5. **Background Processing**: Long-running tasks execute asynchronously via Celery
6. **Personalization Engine**: Interest-based ranking combines behavioral signals with trending metrics
7. **Direct-to-S3 Uploads**: Media uploads bypass backend using presigned URLs
8. **Rate Limiting**: Sliding window rate limits prevent abuse at the API layer

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                  Next.js 14 (App Router)                     │
│                    + Tailwind CSS                            │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS/REST
                         │
┌────────────────────────▼────────────────────────────────────┐
│                      API Gateway                             │
│                   Django + DRF                               │
│              (Authentication, Routing)                       │
└─────┬──────────────────┬──────────────────┬────────────────┘
      │                  │                  │
      │                  │                  │
┌─────▼─────┐   ┌───────▼────────┐   ┌────▼──────┐
│  Clerk    │   │   PostgreSQL   │   │  Valkey   │
│   Auth    │   │   + Prisma     │   │  (Cache)  │
└───────────┘   └────────────────┘   └───────────┘
                         │
                ┌────────▼────────┐
                │     Celery      │
                │  (Background)   │
                └─────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐     ┌────▼────┐     ┌────▼────┐
   │  Resend │     │   AWS   │     │ Valkey  │
   │ (Email) │     │   S3    │     │ (Broker)│
   └─────────┘     └─────────┘     └─────────┘
```

### Technology Stack

- **Frontend**: Next.js 14 with App Router, React Server Components, Tailwind CSS
- **Backend**: Django 5.x, Django REST Framework 3.x
- **Database**: PostgreSQL 15+
- **ORM**: Prisma Client Python for type-safe database access
- **Cache/Queue**: Valkey (Redis-compatible)
- **Authentication**: Clerk (clerk-backend-api Python SDK)
- **Email**: Resend API
- **Storage**: AWS S3 with presigned URLs
- **Background Jobs**: Celery with Valkey broker
- **API Documentation**: OpenAPI/Swagger via drf-spectacular


## Components and Interfaces

### Frontend Components (Next.js)

#### Page Structure

```
app/
├── (auth)/
│   ├── sign-in/page.tsx          # Clerk sign-in
│   └── sign-up/page.tsx          # Clerk sign-up
├── (main)/
│   ├── layout.tsx                # Main layout with nav
│   ├── discover/page.tsx         # Discover feed (Trending/New/For You)
│   ├── library/page.tsx          # User's shelves
│   ├── stories/
│   │   └── [slug]/
│   │       ├── page.tsx          # Story detail page
│   │       └── chapters/[id]/page.tsx  # Chapter reader
│   ├── write/
│   │   ├── page.tsx              # Author dashboard
│   │   ├── stories/[id]/page.tsx # Edit story
│   │   └── chapters/[id]/page.tsx # Edit chapter
│   ├── whispers/page.tsx         # Global whispers feed
│   ├── search/page.tsx           # Search results
│   ├── notifications/page.tsx    # Notifications list
│   └── profile/[handle]/page.tsx # User profile
└── api/
    └── clerk-webhook/route.ts    # Clerk user sync webhook
```

#### Key React Components


**DiscoverFeed Component**
- Tabs: Trending, New, For You
- Infinite scroll with cursor pagination
- Story cards with cover, title, author, tags
- Client-side state management for active tab

**ChapterReader Component**
- Distraction-free reading view
- Settings panel: font size (14-24px), theme (light/dark), line width (600-800px)
- Progress tracking on scroll (debounced)
- Highlight selection with context menu
- Bookmark button in fixed position

**WhisperComposer Component**
- Text input with character limit (280 chars)
- Media upload button (presigned S3)
- Scope selector (global/story/highlight)
- Rate limit indicator

**ShelfManager Component**
- Shelf list with story counts
- Add/remove story actions
- Create/rename/delete shelf modals

### Backend API Structure (Django)

#### Django Apps

```
backend/
├── config/
│   ├── settings.py               # Django settings
│   ├── urls.py                   # Root URL config
│   └── celery.py                 # Celery configuration
├── apps/
│   ├── users/
│   │   ├── models.py             # UserProfile (Prisma-backed)
│   │   ├── views.py              # Profile endpoints
│   │   └── middleware.py         # Clerk auth middleware
│   ├── stories/
│   │   ├── models.py             # Story, Chapter (Prisma-backed)
│   │   ├── views.py              # Story/chapter CRUD
│   │   └── serializers.py        # DRF serializers
│   ├── library/
│   │   ├── models.py             # Shelf, ShelfItem
│   │   ├── views.py              # Library management
│   │   └── serializers.py
│   ├── whispers/
│   │   ├── models.py             # Whisper, WhisperLike
│   │   ├── views.py              # Whisper CRUD, feeds
│   │   └── serializers.py
│   ├── highlights/
│   │   ├── models.py             # Highlight
│   │   ├── views.py              # Highlight CRUD
│   │   └── serializers.py
│   ├── social/
│   │   ├── models.py             # Follow, Block
│   │   ├── views.py              # Follow/block actions
│   │   └── serializers.py
│   ├── notifications/
│   │   ├── models.py             # Notification
│   │   ├── views.py              # Notification list, mark read
│   │   ├── tasks.py              # Celery tasks for emails
│   │   └── serializers.py
│   ├── discovery/
│   │   ├── views.py              # Discover feeds
│   │   ├── personalization.py   # For You algorithm
│   │   ├── trending.py           # Trending calculation
│   │   └── tasks.py              # Background score updates
│   ├── search/
│   │   ├── views.py              # Search and suggest endpoints
│   │   └── indexing.py           # PostgreSQL full-text search
│   ├── uploads/
│   │   ├── views.py              # Presigned URL generation
│   │   └── s3.py                 # S3 client wrapper
│   ├── moderation/
│   │   ├── models.py             # Report
│   │   ├── views.py              # Report submission
│   │   └── serializers.py
│   └── core/
│       ├── pagination.py         # Cursor pagination
│       ├── rate_limiting.py      # Rate limit decorators
│       ├── cache.py              # Cache utilities
│       └── exceptions.py         # Custom exceptions
└── prisma/
    └── schema.prisma             # Prisma schema definition
```

#### Authentication Middleware

```python
# apps/users/middleware.py
from clerk_backend_api import Clerk
from django.conf import settings

class ClerkAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.clerk = Clerk(bearer_auth=settings.CLERK_SECRET_KEY)
    
    def __call__(self, request):
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                # Verify JWT token with Clerk
                session = self.clerk.verify_token(token)
                request.clerk_user_id = session.user_id
                # Fetch or create UserProfile
                request.user_profile = get_or_create_profile(session.user_id)
            except Exception:
                request.clerk_user_id = None
                request.user_profile = None
        return self.get_response(request)
```

#### Rate Limiting Decorator

```python
# apps/core/rate_limiting.py
from functools import wraps
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status

def rate_limit(key_prefix, max_requests, window_seconds):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_id = request.clerk_user_id
            if not user_id:
                return view_func(request, *args, **kwargs)
            
            cache_key = f"rate_limit:{key_prefix}:{user_id}"
            current = cache.get(cache_key, 0)
            
            if current >= max_requests:
                return Response(
                    {"error": "Rate limit exceeded"},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={"Retry-After": str(window_seconds)}
                )
            
            cache.set(cache_key, current + 1, window_seconds)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```


#### Cursor Pagination Implementation

```python
# apps/core/pagination.py
import base64
import json
from rest_framework.pagination import BasePagination
from rest_framework.response import Response

class CursorPagination(BasePagination):
    page_size = 20
    max_page_size = 100
    
    def paginate_queryset(self, queryset, request, view=None):
        self.page_size = min(
            int(request.query_params.get('page_size', self.page_size)),
            self.max_page_size
        )
        
        cursor = request.query_params.get('cursor')
        if cursor:
            decoded = json.loads(base64.b64decode(cursor))
            # Apply cursor filter based on ordering
            queryset = queryset.filter(
                id__lt=decoded['id']
            )
        
        results = list(queryset[:self.page_size + 1])
        has_next = len(results) > self.page_size
        
        if has_next:
            results = results[:-1]
            last_item = results[-1]
            next_cursor = base64.b64encode(
                json.dumps({'id': last_item.id}).encode()
            ).decode()
            self.next_cursor = next_cursor
        else:
            self.next_cursor = None
        
        return results
    
    def get_paginated_response(self, data):
        return Response({
            'data': data,
            'next_cursor': self.next_cursor
        })
```

### API Endpoints

#### Public Endpoints

```
GET  /v1/health                          # Health check
GET  /v1/stories                         # List stories (with filters)
GET  /v1/stories/{slug}                  # Get story by slug
GET  /v1/stories/{id}/chapters           # List chapters for story
GET  /v1/chapters/{id}                   # Get chapter content
GET  /v1/whispers                        # List whispers (global or filtered)
GET  /v1/search                          # Full-text search
GET  /v1/search/suggest                  # Autocomplete suggestions
GET  /v1/users/{handle}                  # Get user profile
```

#### Authenticated Endpoints

```
# User Profile
GET    /v1/me                            # Get current user profile
PUT    /v1/me                            # Update profile

# Library Management
GET    /v1/library/shelves               # List user's shelves
POST   /v1/library/shelves               # Create shelf
PUT    /v1/library/shelves/{id}          # Update shelf
DELETE /v1/library/shelves/{id}          # Delete shelf
POST   /v1/library/shelves/{id}/items    # Add story to shelf
DELETE /v1/library/shelves/{id}/items/{story_id}  # Remove story

# Story & Chapter Writing
POST   /v1/stories                       # Create story draft
PUT    /v1/stories/{id}                  # Update story
DELETE /v1/stories/{id}                  # Soft delete story
POST   /v1/stories/{id}/publish          # Publish story
POST   /v1/stories/{id}/chapters         # Create chapter draft
PUT    /v1/chapters/{id}                 # Update chapter
DELETE /v1/chapters/{id}                 # Soft delete chapter
POST   /v1/chapters/{id}/publish         # Publish chapter

# Reading Progress & Bookmarks
POST   /v1/chapters/{id}/progress        # Update reading progress
GET    /v1/chapters/{id}/progress        # Get reading progress
POST   /v1/chapters/{id}/bookmarks       # Create bookmark
GET    /v1/chapters/{id}/bookmarks       # List bookmarks
DELETE /v1/bookmarks/{id}                # Delete bookmark

# Whispers
POST   /v1/whispers                      # Create whisper
DELETE /v1/whispers/{id}                 # Soft delete whisper
POST   /v1/whispers/{id}/replies         # Reply to whisper
GET    /v1/whispers/{id}/replies         # List replies
POST   /v1/whispers/{id}/like            # Like whisper
DELETE /v1/whispers/{id}/like            # Unlike whisper

# Highlights
POST   /v1/chapters/{id}/highlights      # Create highlight
GET    /v1/chapters/{id}/highlights      # List highlights
DELETE /v1/highlights/{id}               # Delete highlight

# Social
POST   /v1/users/{id}/follow             # Follow user
DELETE /v1/users/{id}/follow             # Unfollow user
POST   /v1/users/{id}/block              # Block user
DELETE /v1/users/{id}/block              # Unblock user
GET    /v1/users/{id}/followers          # List followers
GET    /v1/users/{id}/following          # List following

# Notifications
GET    /v1/notifications                 # List notifications
POST   /v1/notifications/{id}/read       # Mark as read
POST   /v1/notifications/read-all        # Mark all as read

# Uploads
POST   /v1/uploads/presign               # Get presigned S3 URL

# Reports
POST   /v1/reports                       # Submit report
```


## Data Models

### Prisma Schema

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-py"
  interface = "asyncio"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model UserProfile {
  id              String    @id @default(uuid())
  clerk_user_id   String    @unique
  handle          String    @unique
  display_name    String
  bio             String?
  avatar_key      String?
  created_at      DateTime  @default(now())
  updated_at      DateTime  @updatedAt
  
  // Relations
  stories         Story[]
  shelves         Shelf[]
  whispers        Whisper[]
  highlights      Highlight[]
  whisper_likes   WhisperLike[]
  reading_progress ReadingProgress[]
  bookmarks       Bookmark[]
  followers       Follow[]  @relation("Following")
  following       Follow[]  @relation("Follower")
  blockers        Block[]   @relation("Blocked")
  blocking        Block[]   @relation("Blocker")
  notifications   Notification[]
  reports_made    Report[]  @relation("Reporter")
  reports_received Report[] @relation("Reported")
  interests       UserInterest[]
  
  @@index([handle])
  @@index([clerk_user_id])
}

model Story {
  id              String    @id @default(uuid())
  slug            String    @unique
  title           String
  blurb           String
  cover_key       String?
  author_id       String
  published       Boolean   @default(false)
  published_at    DateTime?
  deleted_at      DateTime?
  created_at      DateTime  @default(now())
  updated_at      DateTime  @updatedAt
  
  // Relations
  author          UserProfile @relation(fields: [author_id], references: [id])
  chapters        Chapter[]
  tags            StoryTag[]
  shelf_items     ShelfItem[]
  whispers        Whisper[]
  stats           StoryStatsDaily[]
  reports         Report[]
  
  @@index([slug])
  @@index([author_id])
  @@index([published, deleted_at])
  @@index([published_at])
}

model Chapter {
  id              String    @id @default(uuid())
  story_id        String
  chapter_number  Int
  title           String
  content         String    @db.Text
  published       Boolean   @default(false)
  published_at    DateTime?
  deleted_at      DateTime?
  created_at      DateTime  @default(now())
  updated_at      DateTime  @updatedAt
  
  // Relations
  story           Story     @relation(fields: [story_id], references: [id])
  highlights      Highlight[]
  reading_progress ReadingProgress[]
  bookmarks       Bookmark[]
  reports         Report[]
  
  @@unique([story_id, chapter_number])
  @@index([story_id, published])
}

model Tag {
  id              String    @id @default(uuid())
  name            String    @unique
  slug            String    @unique
  created_at      DateTime  @default(now())
  
  // Relations
  stories         StoryTag[]
  interests       UserInterest[]
  
  @@index([slug])
}

model StoryTag {
  story_id        String
  tag_id          String
  
  story           Story     @relation(fields: [story_id], references: [id], onDelete: Cascade)
  tag             Tag       @relation(fields: [tag_id], references: [id], onDelete: Cascade)
  
  @@id([story_id, tag_id])
  @@index([tag_id])
}

model Shelf {
  id              String    @id @default(uuid())
  user_id         String
  name            String
  created_at      DateTime  @default(now())
  updated_at      DateTime  @updatedAt
  
  // Relations
  user            UserProfile @relation(fields: [user_id], references: [id])
  items           ShelfItem[]
  
  @@index([user_id])
}

model ShelfItem {
  id              String    @id @default(uuid())
  shelf_id        String
  story_id        String
  added_at        DateTime  @default(now())
  
  // Relations
  shelf           Shelf     @relation(fields: [shelf_id], references: [id], onDelete: Cascade)
  story           Story     @relation(fields: [story_id], references: [id])
  
  @@unique([shelf_id, story_id])
  @@index([story_id])
}

model ReadingProgress {
  id              String    @id @default(uuid())
  user_id         String
  chapter_id      String
  offset          Int       @default(0)
  updated_at      DateTime  @updatedAt
  
  // Relations
  user            UserProfile @relation(fields: [user_id], references: [id])
  chapter         Chapter   @relation(fields: [chapter_id], references: [id])
  
  @@unique([user_id, chapter_id])
  @@index([chapter_id])
}

model Bookmark {
  id              String    @id @default(uuid())
  user_id         String
  chapter_id      String
  offset          Int
  created_at      DateTime  @default(now())
  
  // Relations
  user            UserProfile @relation(fields: [user_id], references: [id])
  chapter         Chapter   @relation(fields: [chapter_id], references: [id])
  
  @@index([user_id])
  @@index([chapter_id])
}

model Highlight {
  id              String    @id @default(uuid())
  user_id         String
  chapter_id      String
  start_offset    Int
  end_offset      Int
  created_at      DateTime  @default(now())
  
  // Relations
  user            UserProfile @relation(fields: [user_id], references: [id])
  chapter         Chapter   @relation(fields: [chapter_id], references: [id])
  whispers        Whisper[]
  
  @@index([user_id])
  @@index([chapter_id])
}

enum WhisperScope {
  GLOBAL
  STORY
  HIGHLIGHT
}

model Whisper {
  id              String    @id @default(uuid())
  user_id         String
  content         String
  media_key       String?
  scope           WhisperScope
  story_id        String?
  highlight_id    String?
  parent_id       String?
  deleted_at      DateTime?
  created_at      DateTime  @default(now())
  
  // Relations
  user            UserProfile @relation(fields: [user_id], references: [id])
  story           Story?    @relation(fields: [story_id], references: [id])
  highlight       Highlight? @relation(fields: [highlight_id], references: [id])
  parent          Whisper?  @relation("WhisperReplies", fields: [parent_id], references: [id])
  replies         Whisper[] @relation("WhisperReplies")
  likes           WhisperLike[]
  reports         Report[]
  
  @@index([user_id])
  @@index([scope, created_at])
  @@index([story_id, created_at])
  @@index([highlight_id])
  @@index([parent_id])
}

model WhisperLike {
  id              String    @id @default(uuid())
  user_id         String
  whisper_id      String
  created_at      DateTime  @default(now())
  
  // Relations
  user            UserProfile @relation(fields: [user_id], references: [id])
  whisper         Whisper   @relation(fields: [whisper_id], references: [id], onDelete: Cascade)
  
  @@unique([user_id, whisper_id])
  @@index([whisper_id])
}

model Follow {
  id              String    @id @default(uuid())
  follower_id     String
  following_id    String
  created_at      DateTime  @default(now())
  
  // Relations
  follower        UserProfile @relation("Follower", fields: [follower_id], references: [id])
  following       UserProfile @relation("Following", fields: [following_id], references: [id])
  
  @@unique([follower_id, following_id])
  @@index([following_id])
}

model Block {
  id              String    @id @default(uuid())
  blocker_id      String
  blocked_id      String
  created_at      DateTime  @default(now())
  
  // Relations
  blocker         UserProfile @relation("Blocker", fields: [blocker_id], references: [id])
  blocked         UserProfile @relation("Blocked", fields: [blocked_id], references: [id])
  
  @@unique([blocker_id, blocked_id])
  @@index([blocked_id])
}

enum NotificationType {
  REPLY
  FOLLOW
}

model Notification {
  id              String    @id @default(uuid())
  user_id         String
  type            NotificationType
  actor_id        String
  whisper_id      String?
  read_at         DateTime?
  created_at      DateTime  @default(now())
  
  // Relations
  user            UserProfile @relation(fields: [user_id], references: [id])
  
  @@index([user_id, read_at, created_at])
}

enum ReportStatus {
  PENDING
  REVIEWED
  RESOLVED
}

model Report {
  id              String    @id @default(uuid())
  reporter_id     String
  reported_user_id String?
  story_id        String?
  chapter_id      String?
  whisper_id      String?
  reason          String
  status          ReportStatus @default(PENDING)
  created_at      DateTime  @default(now())
  
  // Relations
  reporter        UserProfile @relation("Reporter", fields: [reporter_id], references: [id])
  reported_user   UserProfile? @relation("Reported", fields: [reported_user_id], references: [id])
  story           Story?    @relation(fields: [story_id], references: [id])
  chapter         Chapter?  @relation(fields: [chapter_id], references: [id])
  whisper         Whisper?  @relation(fields: [whisper_id], references: [id])
  
  @@index([reporter_id])
  @@index([status])
}

model UserInterest {
  id              String    @id @default(uuid())
  user_id         String
  tag_id          String?
  author_id       String?
  score           Float     @default(0)
  updated_at      DateTime  @updatedAt
  
  // Relations
  user            UserProfile @relation(fields: [user_id], references: [id])
  tag             Tag?      @relation(fields: [tag_id], references: [id])
  
  @@unique([user_id, tag_id])
  @@unique([user_id, author_id])
  @@index([user_id])
}

model StoryStatsDaily {
  id              String    @id @default(uuid())
  story_id        String
  date            DateTime  @db.Date
  saves_count     Int       @default(0)
  reads_count     Int       @default(0)
  likes_count     Int       @default(0)
  whispers_count  Int       @default(0)
  trending_score  Float     @default(0)
  
  // Relations
  story           Story     @relation(fields: [story_id], references: [id])
  
  @@unique([story_id, date])
  @@index([date, trending_score])
}
```


### Personalization Algorithm

#### Interest Score Calculation

```python
# apps/discovery/personalization.py
from prisma import Prisma
from typing import List, Dict
import math

class PersonalizationEngine:
    # Weight factors for different signals
    WEIGHTS = {
        'save': 3.0,
        'complete_read': 2.5,
        'partial_read': 1.0,
        'like': 1.5,
        'follow': 4.0,
    }
    
    DAILY_DECAY = 0.98
    
    async def update_interests(self, user_id: str, event: str, story_id: str):
        """Update user interest scores based on behavioral signals"""
        db = Prisma()
        await db.connect()
        
        # Get story with tags and author
        story = await db.story.find_unique(
            where={'id': story_id},
            include={'tags': {'include': {'tag': True}}, 'author': True}
        )
        
        weight = self.WEIGHTS.get(event, 1.0)
        
        # Update tag interests
        for story_tag in story.tags:
            await db.userinterest.upsert(
                where={
                    'user_id_tag_id': {
                        'user_id': user_id,
                        'tag_id': story_tag.tag.id
                    }
                },
                data={
                    'create': {
                        'user_id': user_id,
                        'tag_id': story_tag.tag.id,
                        'score': weight
                    },
                    'update': {
                        'score': {'increment': weight}
                    }
                }
            )
        
        # Update author interest
        await db.userinterest.upsert(
            where={
                'user_id_author_id': {
                    'user_id': user_id,
                    'author_id': story.author_id
                }
            },
            data={
                'create': {
                    'user_id': user_id,
                    'author_id': story.author_id,
                    'score': weight
                },
                'update': {
                    'score': {'increment': weight}
                }
            }
        )
        
        await db.disconnect()
    
    async def calculate_story_score(self, user_id: str, story: Dict) -> float:
        """Calculate personalized score for a story"""
        db = Prisma()
        await db.connect()
        
        # Get user interests
        interests = await db.userinterest.find_many(
            where={'user_id': user_id}
        )
        
        interest_map = {
            f"tag_{i.tag_id}": i.score for i in interests if i.tag_id
        }
        interest_map.update({
            f"author_{i.author_id}": i.score for i in interests if i.author_id
        })
        
        # Calculate interest score
        interest_score = 0.0
        
        # Tag affinity
        for tag in story.get('tags', []):
            interest_score += interest_map.get(f"tag_{tag['id']}", 0)
        
        # Author affinity
        author_score = interest_map.get(f"author_{story['author_id']}", 0)
        interest_score += author_score
        
        # Get trending score
        trending_score = story.get('trending_score', 0)
        
        # Freshness score (days since publication)
        days_old = (datetime.now() - story['published_at']).days
        freshness_score = math.exp(-0.1 * days_old)
        
        # Combined score with weights
        final_score = (
            0.5 * interest_score +
            0.3 * trending_score +
            0.2 * freshness_score
        )
        
        await db.disconnect()
        return final_score
    
    async def get_for_you_feed(self, user_id: str, cursor: str = None, limit: int = 20) -> List[Dict]:
        """Generate personalized For You feed"""
        db = Prisma()
        await db.connect()
        
        # Check if user has sufficient interaction history
        interest_count = await db.userinterest.count(
            where={'user_id': user_id}
        )
        
        # Cold start: fallback to trending
        if interest_count < 3:
            stories = await self.get_trending_feed(cursor, limit)
            await db.disconnect()
            return stories
        
        # Get candidate stories (published, not deleted, not blocked)
        blocked_users = await db.block.find_many(
            where={'blocker_id': user_id},
            select={'blocked_id': True}
        )
        blocked_ids = [b.blocked_id for b in blocked_users]
        
        stories = await db.story.find_many(
            where={
                'published': True,
                'deleted_at': None,
                'author_id': {'not_in': blocked_ids}
            },
            include={
                'tags': {'include': {'tag': True}},
                'author': True,
                'stats': {
                    'where': {'date': datetime.now().date()},
                    'take': 1
                }
            },
            take=100  # Get larger candidate set for scoring
        )
        
        # Score and rank stories
        scored_stories = []
        for story in stories:
            score = await self.calculate_story_score(user_id, story)
            scored_stories.append((score, story))
        
        # Sort by score descending
        scored_stories.sort(key=lambda x: x[0], reverse=True)
        
        # Apply cursor pagination
        if cursor:
            # Find cursor position and slice
            pass  # Implementation details
        
        result = [story for score, story in scored_stories[:limit]]
        
        await db.disconnect()
        return result
```

#### Trending Score Calculation

```python
# apps/discovery/trending.py
from datetime import datetime, timedelta
import math

class TrendingCalculator:
    # Weight factors for engagement types
    ENGAGEMENT_WEIGHTS = {
        'save': 3.0,
        'read': 1.0,
        'like': 2.0,
        'whisper': 2.5,
    }
    
    HOURLY_DECAY = 0.98
    
    async def calculate_trending_score(self, story_id: str) -> float:
        """Calculate trending score for a story based on 24h engagement"""
        db = Prisma()
        await db.connect()
        
        # Get today's stats
        stats = await db.statsstatsdaily.find_unique(
            where={
                'story_id_date': {
                    'story_id': story_id,
                    'date': datetime.now().date()
                }
            }
        )
        
        if not stats:
            await db.disconnect()
            return 0.0
        
        # Calculate weighted engagement
        raw_score = (
            stats.saves_count * self.ENGAGEMENT_WEIGHTS['save'] +
            stats.reads_count * self.ENGAGEMENT_WEIGHTS['read'] +
            stats.likes_count * self.ENGAGEMENT_WEIGHTS['like'] +
            stats.whispers_count * self.ENGAGEMENT_WEIGHTS['whisper']
        )
        
        # Apply time decay (assuming uniform distribution over 24h)
        hours_elapsed = 12  # Average
        decayed_score = raw_score * (self.HOURLY_DECAY ** hours_elapsed)
        
        await db.disconnect()
        return decayed_score
    
    async def update_all_trending_scores(self):
        """Background task to recompute all trending scores"""
        db = Prisma()
        await db.connect()
        
        # Get all published stories
        stories = await db.story.find_many(
            where={'published': True, 'deleted_at': None}
        )
        
        for story in stories:
            score = await self.calculate_trending_score(story.id)
            
            # Update or create today's stats
            await db.storystats daily.upsert(
                where={
                    'story_id_date': {
                        'story_id': story.id,
                        'date': datetime.now().date()
                    }
                },
                data={
                    'create': {
                        'story_id': story.id,
                        'date': datetime.now().date(),
                        'trending_score': score
                    },
                    'update': {
                        'trending_score': score
                    }
                }
            )
        
        await db.disconnect()
```


### Caching Strategy

#### Cache Key Patterns

```python
# apps/core/cache.py
from django.core.cache import cache
from typing import Optional, Callable, Any
import hashlib
import json

class CacheManager:
    # TTL configurations (in seconds)
    TTL_CONFIG = {
        'discover_feed': 180,        # 3 minutes
        'trending_feed': 300,        # 5 minutes
        'whispers_feed': 60,         # 1 minute
        'story_metadata': 600,       # 10 minutes
        'search_suggest': 1200,      # 20 minutes
        'for_you_feed': 7200,        # 2 hours
        'user_profile': 300,         # 5 minutes
    }
    
    @staticmethod
    def make_key(prefix: str, **params) -> str:
        """Generate cache key from prefix and parameters"""
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
        return f"{prefix}:{param_hash}"
    
    @staticmethod
    async def get_or_set(
        key: str,
        fetch_func: Callable,
        ttl: int,
        *args,
        **kwargs
    ) -> Any:
        """Get from cache or fetch and cache"""
        cached = cache.get(key)
        if cached is not None:
            return cached
        
        result = await fetch_func(*args, **kwargs)
        cache.set(key, result, ttl)
        return result
    
    @staticmethod
    def invalidate_pattern(pattern: str):
        """Invalidate all keys matching pattern"""
        # Note: Requires Valkey SCAN command
        # Implementation depends on cache backend
        pass

# Usage examples
async def get_discover_feed(tab: str, cursor: str = None):
    cache_key = CacheManager.make_key(
        'discover_feed',
        tab=tab,
        cursor=cursor or ''
    )
    
    return await CacheManager.get_or_set(
        cache_key,
        fetch_discover_feed,
        CacheManager.TTL_CONFIG['discover_feed'],
        tab,
        cursor
    )
```

#### Cache Invalidation Strategy

```python
# apps/core/cache.py (continued)

class CacheInvalidator:
    """Handle cache invalidation on data changes"""
    
    @staticmethod
    def on_story_published(story_id: str):
        """Invalidate caches when story is published"""
        # Invalidate discover feeds
        CacheManager.invalidate_pattern('discover_feed:*')
        # Invalidate author's profile
        CacheManager.invalidate_pattern(f'user_profile:*')
    
    @staticmethod
    def on_whisper_created(whisper_id: str, scope: str, story_id: str = None):
        """Invalidate caches when whisper is created"""
        # Invalidate global whispers feed
        if scope == 'GLOBAL':
            CacheManager.invalidate_pattern('whispers_feed:global:*')
        # Invalidate story-specific feed
        elif scope == 'STORY' and story_id:
            CacheManager.invalidate_pattern(f'whispers_feed:story:{story_id}:*')
    
    @staticmethod
    def on_user_profile_updated(user_id: str):
        """Invalidate caches when profile is updated"""
        CacheManager.invalidate_pattern(f'user_profile:{user_id}')
```

### Presigned Upload Flow

```python
# apps/uploads/s3.py
import boto3
from botocore.config import Config
from django.conf import settings
import uuid

class S3UploadManager:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            config=Config(signature_version='s3v4')
        )
        self.bucket = settings.AWS_S3_BUCKET
    
    def generate_presigned_url(
        self,
        file_type: str,
        max_size: int,
        content_type: str
    ) -> dict:
        """Generate presigned POST URL for direct S3 upload"""
        
        # Generate unique object key
        file_extension = content_type.split('/')[-1]
        object_key = f"uploads/{uuid.uuid4()}.{file_extension}"
        
        # Define upload conditions
        conditions = [
            {'bucket': self.bucket},
            {'key': object_key},
            {'Content-Type': content_type},
            ['content-length-range', 1, max_size]
        ]
        
        # Generate presigned POST
        presigned_post = self.s3_client.generate_presigned_post(
            Bucket=self.bucket,
            Key=object_key,
            Fields={'Content-Type': content_type},
            Conditions=conditions,
            ExpiresIn=900  # 15 minutes
        )
        
        return {
            'url': presigned_post['url'],
            'fields': presigned_post['fields'],
            'object_key': object_key
        }

# apps/uploads/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .s3 import S3UploadManager

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def presign_upload(request):
    """Generate presigned URL for file upload"""
    upload_type = request.data.get('type')  # 'avatar', 'cover', 'whisper_media'
    content_type = request.data.get('content_type')
    
    # Validate content type
    allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    if content_type not in allowed_types:
        return Response({'error': 'Invalid content type'}, status=400)
    
    # Determine max size based on upload type
    max_sizes = {
        'avatar': 2 * 1024 * 1024,      # 2MB
        'cover': 5 * 1024 * 1024,       # 5MB
        'whisper_media': 10 * 1024 * 1024  # 10MB
    }
    max_size = max_sizes.get(upload_type, 2 * 1024 * 1024)
    
    # Generate presigned URL
    s3_manager = S3UploadManager()
    presigned_data = s3_manager.generate_presigned_url(
        upload_type,
        max_size,
        content_type
    )
    
    return Response(presigned_data)
```

### Background Jobs (Celery)

```python
# config/celery.py
from celery import Celery
from django.conf import settings
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('muejam')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat schedule
app.conf.beat_schedule = {
    'update-trending-scores': {
        'task': 'apps.discovery.tasks.update_trending_scores',
        'schedule': 1800.0,  # Every 30 minutes
    },
    'apply-daily-decay': {
        'task': 'apps.discovery.tasks.apply_daily_decay',
        'schedule': 86400.0,  # Every 24 hours
    },
}

# apps/notifications/tasks.py
from celery import shared_task
from resend import Resend
from django.conf import settings
import hashlib

@shared_task(bind=True, max_retries=3)
def send_notification_email(self, user_email: str, notification_type: str, data: dict):
    """Send notification email via Resend with idempotency"""
    
    # Generate idempotency key
    idempotency_data = f"{user_email}:{notification_type}:{data.get('id')}"
    idempotency_key = hashlib.sha256(idempotency_data.encode()).hexdigest()
    
    resend_client = Resend(api_key=settings.RESEND_API_KEY)
    
    try:
        # Prepare email content based on notification type
        if notification_type == 'REPLY':
            subject = "New reply to your whisper"
            html_content = f"""
                <p>Someone replied to your whisper!</p>
                <p><a href="{settings.FRONTEND_URL}/whispers/{data['whisper_id']}">View reply</a></p>
                <p><a href="{settings.FRONTEND_URL}/settings/notifications">Unsubscribe</a></p>
            """
        elif notification_type == 'FOLLOW':
            subject = "New follower"
            html_content = f"""
                <p>{data['actor_name']} started following you!</p>
                <p><a href="{settings.FRONTEND_URL}/profile/{data['actor_handle']}">View profile</a></p>
                <p><a href="{settings.FRONTEND_URL}/settings/notifications">Unsubscribe</a></p>
            """
        
        # Send email with idempotency key
        resend_client.emails.send({
            'from': 'MueJam <notifications@muejam.com>',
            'to': user_email,
            'subject': subject,
            'html': html_content,
            'headers': {
                'X-Idempotency-Key': idempotency_key
            }
        })
        
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

# apps/discovery/tasks.py
from celery import shared_task
from .trending import TrendingCalculator
from .personalization import PersonalizationEngine

@shared_task
def update_trending_scores():
    """Recompute trending scores for all stories"""
    calculator = TrendingCalculator()
    await calculator.update_all_trending_scores()

@shared_task
def apply_daily_decay():
    """Apply daily decay to all interest scores"""
    from prisma import Prisma
    
    db = Prisma()
    await db.connect()
    
    # Multiply all interest scores by decay factor
    await db.execute_raw(
        "UPDATE UserInterest SET score = score * 0.98"
    )
    
    await db.disconnect()
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified several areas where properties can be consolidated:

- **Soft Delete Properties**: Requirements 5.6, 6.5 all test soft delete behavior - these can be combined into one comprehensive soft delete property
- **Round Trip Properties**: Requirements 3.5 (progress), 7.4 (likes), 11.2 (follows) all test round-trip behavior - these are distinct enough to keep separate
- **Uniqueness Constraints**: Requirements 7.7 (whisper likes), 11.8 (follows), 13.6 (reports) all test uniqueness - these should remain separate as they apply to different entities
- **Rate Limiting**: Requirements 6.4, 15.4 test rate limiting - these can be combined into one comprehensive rate limit property
- **Filtering Properties**: Requirements 9.6, 16.6 both test exclusion of deleted/blocked content - these can be combined

### Core Properties

**Property 1: Authentication Profile Creation**
*For any* valid clerk_user_id, when authentication succeeds, the system should either return an existing UserProfile or create a new one with that clerk_user_id
**Validates: Requirements 1.2**

**Property 2: Handle Uniqueness**
*For any* two user profiles, their handles must be unique - attempting to update a profile with an existing handle should be rejected
**Validates: Requirements 1.3**

**Property 3: Handle Format Validation**
*For any* string, the system should accept it as a handle if and only if it contains only alphanumeric characters and underscores and has length between 3-30 characters
**Validates: Requirements 1.5**

**Property 4: Cursor Pagination Completeness**
*For any* dataset and pagination parameters, repeatedly following next_cursor links should return all items exactly once with no duplicates or omissions
**Validates: Requirements 2.6, 2.7**

**Property 5: Reading Progress Round Trip**
*For any* chapter and character offset, saving reading progress then retrieving it should return the same offset value
**Validates: Requirements 3.4, 3.5**

**Property 6: Shelf Item Addition**
*For any* shelf and story, adding the story to the shelf should result in a ShelfItem linking them that can be retrieved
**Validates: Requirements 4.2**

**Property 7: Shelf Item Removal Idempotence**
*For any* shelf and story, adding then removing the story should result in the story not being in the shelf
**Validates: Requirements 4.3**

**Property 8: Multi-Shelf Story Membership**
*For any* story and set of shelves, adding the story to all shelves should result in the story appearing in all of them simultaneously
**Validates: Requirements 4.6**

**Property 9: Publication Status Update**
*For any* unpublished story, publishing it should set published=true and populate published_at with a valid timestamp
**Validates: Requirements 5.3**

**Property 10: Soft Delete Behavior**
*For any* content entity (story, chapter, whisper), deleting it should set deleted_at timestamp while preserving the entity in the database and all its relationships
**Validates: Requirements 5.6, 6.5, 20.2**

**Property 11: XSS Sanitization**
*For any* markdown content containing script tags or javascript: URLs, the sanitized output should not execute JavaScript when rendered
**Validates: Requirements 5.10**

**Property 12: Rate Limit Enforcement**
*For any* user and rate-limited operation, attempting more operations than the limit within the time window should result in HTTP 429 responses for excess attempts
**Validates: Requirements 6.4, 15.4**

**Property 13: Whisper Like Creation**
*For any* user and whisper, liking the whisper should create a WhisperLike record that can be retrieved
**Validates: Requirements 7.3**

**Property 14: Whisper Like Round Trip**
*For any* user and whisper, liking then unliking should result in no WhisperLike record existing
**Validates: Requirements 7.4**

**Property 15: Duplicate Like Prevention**
*For any* user and whisper, attempting to like the same whisper twice should result in only one WhisperLike record
**Validates: Requirements 7.7**

**Property 16: Highlight Offset Validation**
*For any* highlight, the system should accept it if and only if start_offset < end_offset and both offsets are within the chapter content length
**Validates: Requirements 8.7, 8.8**

**Property 17: Highlight Storage Completeness**
*For any* valid highlight with chapter_id, start_offset, and end_offset, saving it should store all fields and allow retrieval
**Validates: Requirements 8.2**

**Property 18: Deleted Content Exclusion**
*For any* search query or feed request, the results should never include content where deleted_at is not null or where the author is blocked by the requesting user
**Validates: Requirements 9.6, 16.6**

**Property 19: Interest Score Decay**
*For any* set of UserInterest records with scores S, after daily decay runs, all scores should equal S * 0.98
**Validates: Requirements 10.6**

**Property 20: Follow Relationship Creation**
*For any* two users A and B, when A follows B, a Follow record should exist with follower_id=A and following_id=B
**Validates: Requirements 11.1**

**Property 21: Follow Relationship Round Trip**
*For any* two users A and B, if A follows then unfollows B, no Follow record should exist between them
**Validates: Requirements 11.2**

**Property 22: Block Prevents Follow**
*For any* two users A and B, if A blocks B, attempting to follow B should be rejected
**Validates: Requirements 11.7**

**Property 23: Duplicate Follow Prevention**
*For any* two users A and B, attempting to follow twice should result in only one Follow record
**Validates: Requirements 11.8**

**Property 24: Block Removes Follow**
*For any* two users A and B where A follows B, when A blocks B, the Follow record should be automatically removed
**Validates: Requirements 11.9**

**Property 25: Notification Idempotency**
*For any* notification event with the same idempotency key, sending it multiple times should result in only one notification being delivered
**Validates: Requirements 12.9**

**Property 26: Duplicate Report Prevention**
*For any* user and content item, attempting to report the same content twice should result in only one Report record
**Validates: Requirements 13.6**

**Property 27: UUID Uniqueness**
*For any* set of generated UUIDs for object keys, all UUIDs should be unique with no collisions
**Validates: Requirements 14.7**

**Property 28: Validation Error Response**
*For any* API request with invalid payload, the response should be HTTP 400 with a detailed error message describing the validation failure
**Validates: Requirements 17.6**

**Property 29: Pagination Response Structure**
*For any* paginated API request, the response should contain a "data" array and a "next_cursor" field (which may be null)
**Validates: Requirements 18.2**

**Property 30: Cursor Encoding Format**
*For any* generated pagination cursor, it should be a valid base64-encoded string that can be decoded to extract sort key and offset
**Validates: Requirements 18.5**

**Property 31: Background Job Retry**
*For any* background job that fails, the system should retry it up to 3 times with exponentially increasing delays between attempts
**Validates: Requirements 19.5**

**Property 32: Cache Invalidation on Update**
*For any* cached content that is updated, the corresponding cache keys should be invalidated so subsequent reads fetch fresh data
**Validates: Requirements 21.7**

**Property 33: Touch Target Minimum Size**
*For any* interactive UI element, its tap area should be at least 44x44 pixels to ensure mobile usability
**Validates: Requirements 23.4**

**Property 34: Primary Action Limit**
*For any* view in the application, there should be at most 2 primary action buttons visible
**Validates: Requirements 24.3**


## Error Handling

### Error Response Format

All API errors follow a consistent JSON structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Specific field error details"
    }
  }
}
```

### HTTP Status Codes

- **400 Bad Request**: Invalid input, validation failures
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: Authenticated but not authorized (e.g., accessing blocked content)
- **404 Not Found**: Resource does not exist or is soft-deleted
- **409 Conflict**: Duplicate resource (e.g., handle already taken)
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Unexpected server error
- **503 Service Unavailable**: Dependency unavailable (database, cache, etc.)

### Error Categories

**Validation Errors**
- Invalid handle format
- Offset out of bounds
- File size exceeds limit
- Invalid content type
- Missing required fields

**Authentication Errors**
- Invalid or expired Clerk token
- Missing authorization header
- User profile not found

**Authorization Errors**
- Accessing blocked user's content
- Modifying another user's content
- Following a blocked user

**Rate Limit Errors**
- Too many whispers per minute
- Too many replies per minute
- Too many publish operations per hour

**Resource Errors**
- Story not found
- Chapter not found
- Whisper not found
- Soft-deleted content accessed

**Conflict Errors**
- Duplicate handle
- Duplicate like
- Duplicate follow
- Duplicate report

**External Service Errors**
- S3 upload failure
- Resend email failure
- Clerk API failure
- Database connection failure
- Cache connection failure

### Error Handling Strategies

**Graceful Degradation**
- If cache is unavailable, fall back to database queries
- If email service fails, retry with exponential backoff
- If S3 is unavailable, return error but don't block other operations

**Transaction Rollback**
- Multi-step operations wrapped in database transactions
- On error, rollback all changes to maintain consistency

**Retry Logic**
- Background jobs retry up to 3 times with exponential backoff
- Email notifications retry on transient failures
- External API calls retry on network errors

**Logging and Monitoring**
- All errors logged with context (user_id, request_id, timestamp)
- Critical errors trigger alerts
- Error rates monitored for anomaly detection


## Testing Strategy

### Dual Testing Approach

The MueJam Library testing strategy employs both unit tests and property-based tests to ensure comprehensive coverage:

- **Unit Tests**: Verify specific examples, edge cases, and integration points
- **Property Tests**: Verify universal properties across randomized inputs

Both approaches are complementary and necessary. Unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across a wide input space.

### Property-Based Testing

**Framework**: Use `hypothesis` for Pytho