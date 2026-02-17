# MueJam Library API Client

## Overview

The MueJam Library API client provides a typed, feature-rich interface for interacting with the backend API. It includes automatic authentication, error handling, request/response interceptors, and cursor-based pagination support.

## Features

- ✅ **Automatic Authentication**: Clerk tokens are automatically injected into requests
- ✅ **Type Safety**: Full TypeScript support with typed responses
- ✅ **Error Handling**: Comprehensive error handling with typed error responses
- ✅ **Request/Response Interceptors**: Extensible middleware system
- ✅ **Cursor Pagination**: Built-in support for cursor-based pagination
- ✅ **Query String Building**: Automatic query parameter handling
- ✅ **Network Error Handling**: Graceful handling of network failures
- ✅ **Response Parsing**: Automatic JSON parsing with error recovery

## Basic Usage

### Making API Calls

```typescript
import { api } from '@/lib/api';

// Get stories
const stories = await api.getStories({ tag: 'fantasy', sort: 'trending' });

// Get a specific story
const story = await api.getStory('my-story-slug');

// Create a whisper
const whisper = await api.createWhisper({
  content: 'Great story!',
  scope: 'STORY',
  story_id: storyId,
});
```

### With React Query

```typescript
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

function StoryList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['stories', { tag: 'fantasy' }],
    queryFn: () => api.getStories({ tag: 'fantasy' }),
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {data.results.map(story => (
        <StoryCard key={story.id} story={story} />
      ))}
    </div>
  );
}
```

## Cursor Pagination

### Using usePagination Hook

The `usePagination` hook provides infinite scroll functionality:

```typescript
import { usePagination, flattenPages } from '@/hooks/usePagination';
import { api } from '@/lib/api';

function InfiniteStoryList() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = usePagination({
    queryKey: ['stories', { tag: 'fantasy' }],
    queryFn: ({ pageParam }) => api.getStories({ 
      tag: 'fantasy', 
      cursor: pageParam 
    }),
  });

  // Flatten all pages into a single array
  const stories = flattenPages(data);

  return (
    <div>
      {stories.map(story => (
        <StoryCard key={story.id} story={story} />
      ))}
      
      {hasNextPage && (
        <button onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
          {isFetchingNextPage ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  );
}
```

### Automatic Infinite Scroll

Use `useInfiniteScroll` for automatic loading:

```typescript
import { usePagination, useInfiniteScroll, flattenPages } from '@/hooks/usePagination';

function AutoScrollStoryList() {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = usePagination({
    queryKey: ['stories'],
    queryFn: ({ pageParam }) => api.getStories({ cursor: pageParam }),
  });

  const { ref } = useInfiniteScroll({
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    threshold: 500, // Load when 500px from bottom
  });

  const stories = flattenPages(data);

  return (
    <div>
      {stories.map(story => (
        <StoryCard key={story.id} story={story} />
      ))}
      
      {/* Sentinel element for intersection observer */}
      <div ref={ref} className="h-10" />
      
      {isFetchingNextPage && <div>Loading more...</div>}
    </div>
  );
}
```

## Error Handling

### Catching API Errors

```typescript
import { api } from '@/lib/api';
import type { ApiError } from '@/types';

try {
  await api.createStory({ title: 'My Story' });
} catch (error) {
  const apiError = error as ApiError;
  
  switch (apiError.error.code) {
    case 'UNAUTHORIZED':
      console.error('Please sign in');
      break;
    case 'VALIDATION_ERROR':
      console.error('Invalid data:', apiError.error.details);
      break;
    case 'RATE_LIMIT_EXCEEDED':
      console.error('Too many requests, please try again later');
      break;
    default:
      console.error('Error:', apiError.error.message);
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `BAD_REQUEST` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate) |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_SERVER_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |
| `NETWORK_ERROR` | - | Network request failed |
| `PARSE_ERROR` | - | Failed to parse response |

## Request/Response Interceptors

### Adding Request Interceptor

```typescript
import { addRequestInterceptor } from '@/lib/api';

// Add custom header to all requests
addRequestInterceptor(async (config) => {
  const headers = new Headers(config.headers);
  headers.set('X-Client-Version', '1.0.0');
  return { ...config, headers };
});

// Log all requests in development
if (import.meta.env.DEV) {
  addRequestInterceptor(async (config) => {
    console.log('Request:', config.method, config.url);
    return config;
  });
}
```

### Adding Response Interceptor

```typescript
import { addResponseInterceptor } from '@/lib/api';

// Log response times
addResponseInterceptor(async (response) => {
  const duration = response.headers.get('X-Response-Time');
  if (duration) {
    console.log('Response time:', duration);
  }
  return response;
});
```

### Adding Error Interceptor

```typescript
import { addErrorInterceptor } from '@/lib/api';
import { toast } from 'sonner';

// Show toast notifications for errors
addErrorInterceptor(async (error) => {
  if (error.error.code === 'RATE_LIMIT_EXCEEDED') {
    toast.error('Too many requests. Please slow down.');
  } else if (error.error.code === 'UNAUTHORIZED') {
    toast.error('Please sign in to continue');
  }
  return error;
});
```

## API Reference

### Authentication

```typescript
// Get current user profile
api.getMe(): Promise<UserProfile>

// Update current user profile
api.updateMe(body: Partial<UserProfile>): Promise<UserProfile>

// Get user profile by handle
api.getProfile(handle: string): Promise<UserProfile>
```

### Stories

```typescript
// List stories with filters
api.getStories(params?: {
  sort?: string;
  tag?: string;
  q?: string;
  cursor?: string;
  page_size?: number;
}): Promise<CursorPage<Story>>

// Get story by slug
api.getStory(slug: string): Promise<Story>

// Get story chapters
api.getStoryChapters(storyId: string): Promise<Chapter[]>

// Create story
api.createStory(body: {
  title: string;
  blurb?: string;
  tags?: string[];
  cover_key?: string;
}): Promise<Story>

// Update story
api.updateStory(id: string, body: Partial<Story>): Promise<Story>

// Publish story
api.publishStory(id: string): Promise<Story>

// Delete story
api.deleteStory(id: string): Promise<void>
```

### Chapters

```typescript
// Get chapter
api.getChapter(chapterId: string): Promise<Chapter>

// Create chapter
api.createChapter(storyId: string, body: {
  title: string;
  content?: string;
  chapter_number?: number;
}): Promise<Chapter>

// Update chapter
api.updateChapter(id: string, body: Partial<Chapter>): Promise<Chapter>

// Publish chapter
api.publishChapter(id: string): Promise<Chapter>

// Delete chapter
api.deleteChapter(id: string): Promise<void>
```

### Whispers

```typescript
// List whispers
api.getWhispers(params?: {
  scope?: string;
  story_id?: string;
  highlight_id?: string;
  cursor?: string;
  page_size?: number;
}): Promise<CursorPage<Whisper>>

// Create whisper
api.createWhisper(body: {
  content: string;
  scope?: string;
  story_id?: string;
  highlight_id?: string;
  media_key?: string;
}): Promise<Whisper>

// Reply to whisper
api.replyWhisper(id: string, body: { content: string }): Promise<Whisper>

// Get whisper replies
api.getWhisperReplies(id: string, cursor?: string): Promise<CursorPage<Whisper>>

// Like whisper
api.likeWhisper(id: string): Promise<void>

// Unlike whisper
api.unlikeWhisper(id: string): Promise<void>

// Delete whisper
api.deleteWhisper(id: string): Promise<void>
```

### Library

```typescript
// Get shelves
api.getShelves(): Promise<Shelf[]>

// Create shelf
api.createShelf(body: {
  name: string;
  description?: string;
  is_public?: boolean;
}): Promise<Shelf>

// Update shelf
api.updateShelf(id: string, body: Partial<Shelf>): Promise<Shelf>

// Delete shelf
api.deleteShelf(id: string): Promise<void>

// Get shelf items
api.getShelfItems(id: string): Promise<ShelfItem[]>

// Add story to shelf
api.addToShelf(shelfId: string, storyId: string): Promise<void>

// Remove story from shelf
api.removeFromShelf(shelfId: string, storyId: string): Promise<void>
```

### Reading

```typescript
// Get chapter highlights
api.getChapterHighlights(chapterId: string): Promise<Highlight[]>

// Create highlight
api.createHighlight(chapterId: string, body: {
  start_offset: number;
  end_offset: number;
  quote_text: string;
}): Promise<Highlight>

// Delete highlight
api.deleteHighlight(id: string): Promise<void>

// Get chapter bookmarks
api.getChapterBookmarks(chapterId: string): Promise<any[]>

// Create bookmark
api.createBookmark(chapterId: string, body: { offset: number }): Promise<any>

// Delete bookmark
api.deleteBookmark(id: string): Promise<void>

// Get reading progress
api.getProgress(chapterId: string): Promise<{ offset: number }>

// Update reading progress
api.updateProgress(chapterId: string, offset: number): Promise<void>
```

### Social

```typescript
// Follow user
api.followUser(userId: string): Promise<void>

// Unfollow user
api.unfollowUser(userId: string): Promise<void>

// Block user
api.blockUser(userId: string): Promise<void>

// Unblock user
api.unblockUser(userId: string): Promise<void>

// Get followers
api.getFollowers(userId: string, cursor?: string): Promise<CursorPage<UserProfile>>

// Get following
api.getFollowing(userId: string, cursor?: string): Promise<CursorPage<UserProfile>>
```

### Notifications

```typescript
// Get notifications
api.getNotifications(cursor?: string): Promise<CursorPage<Notification>>

// Mark notification as read
api.markNotificationRead(id: string): Promise<void>

// Mark all notifications as read
api.markAllNotificationsRead(): Promise<void>
```

### Discovery

```typescript
// Get discovery feed
api.getDiscoverFeed(params?: {
  tab?: 'trending' | 'new' | 'for-you';
  tag?: string;
  q?: string;
  cursor?: string;
  page_size?: number;
}): Promise<CursorPage<Story>>
```

### Search

```typescript
// Search
api.search(params: {
  q: string;
  type?: string;
  cursor?: string;
  page_size?: number;
}): Promise<CursorPage<Story | UserProfile>>

// Search suggestions
api.searchSuggest(q: string, limit?: number): Promise<SearchSuggestion>
```

### Uploads

```typescript
// Get presigned upload URL
api.presign(body: {
  type: 'avatar' | 'cover' | 'whisper_media';
  content_type: string;
  size_bytes: number;
}): Promise<PresignResponse>
```

### Reports

```typescript
// Submit report
api.report(body: {
  target_type: string;
  target_id: string;
  reason: string;
}): Promise<void>
```

### Health

```typescript
// Health check
api.health(): Promise<{ status: string }>
```

## Best Practices

### 1. Use React Query for Data Fetching

```typescript
// ✅ Good
const { data } = useQuery({
  queryKey: ['story', slug],
  queryFn: () => api.getStory(slug),
});

// ❌ Avoid
const [story, setStory] = useState(null);
useEffect(() => {
  api.getStory(slug).then(setStory);
}, [slug]);
```

### 2. Handle Loading and Error States

```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['stories'],
  queryFn: api.getStories,
});

if (isLoading) return <Skeleton />;
if (error) return <ErrorMessage error={error} />;
return <StoryList stories={data.results} />;
```

### 3. Use Optimistic Updates

```typescript
const mutation = useMutation({
  mutationFn: (id: string) => api.likeWhisper(id),
  onMutate: async (id) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['whispers'] });
    
    // Snapshot previous value
    const previous = queryClient.getQueryData(['whispers']);
    
    // Optimistically update
    queryClient.setQueryData(['whispers'], (old: any) => ({
      ...old,
      results: old.results.map((w: Whisper) =>
        w.id === id ? { ...w, is_liked: true, like_count: w.like_count + 1 } : w
      ),
    }));
    
    return { previous };
  },
  onError: (err, id, context) => {
    // Rollback on error
    queryClient.setQueryData(['whispers'], context?.previous);
  },
});
```

### 4. Invalidate Queries After Mutations

```typescript
const mutation = useMutation({
  mutationFn: api.createStory,
  onSuccess: () => {
    // Invalidate and refetch
    queryClient.invalidateQueries({ queryKey: ['stories'] });
  },
});
```

### 5. Use Appropriate Stale Times

```typescript
// Frequently changing data (5 seconds)
useQuery({
  queryKey: ['notifications'],
  queryFn: api.getNotifications,
  staleTime: 5_000,
});

// Rarely changing data (5 minutes)
useQuery({
  queryKey: ['story', slug],
  queryFn: () => api.getStory(slug),
  staleTime: 5 * 60 * 1000,
});
```

## Troubleshooting

### Authentication Errors

If you're getting 401 errors:

1. Check that Clerk is properly configured
2. Verify the token getter is set in App.tsx
3. Check browser console for Clerk errors

### CORS Errors

If you're getting CORS errors:

1. Verify backend CORS configuration
2. Check that `VITE_API_BASE_URL` is correct
3. Ensure backend is running

### Type Errors

If TypeScript is complaining about types:

1. Check that types in `src/types/index.ts` match backend responses
2. Update types if backend API has changed
3. Use `as` type assertion as a last resort

## Support

For API client issues or questions, contact: support@muejam.com
