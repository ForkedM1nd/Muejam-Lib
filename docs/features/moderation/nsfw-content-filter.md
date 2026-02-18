# NSFW Content Filtering

This module provides comprehensive NSFW content filtering based on user preferences for the MueJam Library platform.

## Overview

The NSFW content filtering system allows users to control how NSFW (Not Safe For Work) content is displayed across the platform. It integrates with the NSFW detection system (Task 24) to apply user preferences to stories, chapters, whispers, and images.

## Components

### NSFWContentFilter Service

**File:** `apps/backend/apps/moderation/nsfw_content_filter.py`

Service for filtering content based on user NSFW preferences.

**Features:**
- Filter stories, chapters, and whispers based on user preferences
- Support for three preference modes: SHOW_ALL, BLUR_NSFW, HIDE_NSFW
- Handle anonymous users (default to BLUR_NSFW)
- Add NSFW metadata to content objects
- Check if content should be blurred or hidden

**Key Methods:**

```python
from apps.moderation.nsfw_content_filter import get_nsfw_content_filter

filter_service = get_nsfw_content_filter()

# Filter stories
filtered_stories = await filter_service.filter_stories(stories, user_id)

# Filter chapters
filtered_chapters = await filter_service.filter_chapters(chapters, user_id)

# Filter whispers
filtered_whispers = await filter_service.filter_whispers(whispers, user_id)

# Filter mixed content list
filtered_content = await filter_service.filter_content_list(content_list, user_id)

# Check if image should be blurred
should_blur = await filter_service.should_blur_image(image_id, user_id)

# Check if content should be hidden
should_hide = await filter_service.should_hide_content(
    NSFWContentType.STORY,
    story_id,
    user_id
)

# Add NSFW metadata to content
story = await filter_service.add_nsfw_metadata(story, NSFWContentType.STORY)
```

### Frontend Components

#### NSFWWarningLabel

**File:** `apps/frontend/src/components/shared/NSFWWarningLabel.tsx`

Visual warning label for NSFW content.

**Variants:**
- `badge`: Small badge for cards and thumbnails
- `banner`: Full-width banner for content pages

**Usage:**
```tsx
import NSFWWarningLabel from "@/components/shared/NSFWWarningLabel";

// Badge variant
<NSFWWarningLabel variant="badge" />

// Banner variant
<NSFWWarningLabel variant="banner" />
```

#### BlurredNSFWImage

**File:** `apps/frontend/src/components/shared/BlurredNSFWImage.tsx`

Blurred image component with click-to-reveal functionality.

**Features:**
- Blurs image by default
- Shows NSFW warning label
- Click to reveal button
- Toggle to hide again after revealing

**Usage:**
```tsx
import BlurredNSFWImage from "@/components/shared/BlurredNSFWImage";

<BlurredNSFWImage
  src={imageUrl}
  alt="Image description"
  aspectRatio="3/2"
/>
```

### API Endpoints

#### Get NSFW Preference

```
GET /api/moderation/nsfw/preference/
```

Get the authenticated user's NSFW content preference.

**Response:**
```json
{
  "nsfw_preference": "BLUR_NSFW"
}
```

**Possible values:**
- `SHOW_ALL`: Display all content without filtering
- `BLUR_NSFW`: Show NSFW content but blur images (default)
- `HIDE_NSFW`: Completely hide NSFW content from feeds and searches

#### Update NSFW Preference

```
PUT /api/moderation/nsfw/preference/update/
```

Update the authenticated user's NSFW content preference.

**Request Body:**
```json
{
  "nsfw_preference": "HIDE_NSFW"
}
```

**Response:**
```json
{
  "id": "uuid",
  "user_id": "user-uuid",
  "nsfw_preference": "HIDE_NSFW",
  "updated_at": "2024-02-17T12:00:00Z"
}
```

## User Preferences

### SHOW_ALL

- All content is displayed without filtering
- NSFW labels are still shown for awareness
- Images are not blurred
- No content is hidden from feeds or searches

### BLUR_NSFW (Default)

- NSFW content is displayed in feeds and searches
- NSFW images are blurred by default
- Click-to-reveal button allows viewing blurred images
- NSFW warning labels are displayed on content cards
- This is the default preference for all users (including anonymous)

### HIDE_NSFW

- NSFW content is completely removed from feeds and searches
- Users will not see NSFW stories, chapters, or whispers
- NSFW images are not displayed
- Most restrictive option for users who want to avoid NSFW content

## Integration Examples

### Story Feed Integration

```python
from apps.moderation.nsfw_content_filter import get_nsfw_content_filter

async def get_story_feed(user_id: Optional[str] = None):
    # Fetch stories
    stories = await fetch_stories()
    
    # Apply NSFW filtering
    filter_service = get_nsfw_content_filter()
    filtered_stories = await filter_service.filter_stories(stories, user_id)
    
    return filtered_stories
```

### Whisper Feed Integration

```python
from apps.moderation.nsfw_content_filter import get_nsfw_content_filter

async def get_whisper_feed(user_id: Optional[str] = None):
    # Fetch whispers
    whispers = await fetch_whispers()
    
    # Apply NSFW filtering
    filter_service = get_nsfw_content_filter()
    filtered_whispers = await filter_service.filter_whispers(whispers, user_id)
    
    return filtered_whispers
```

### Search Results Integration

```python
from apps.moderation.nsfw_content_filter import get_nsfw_content_filter

async def search_content(query: str, user_id: Optional[str] = None):
    # Perform search
    results = await search_database(query)
    
    # Apply NSFW filtering to mixed content
    filter_service = get_nsfw_content_filter()
    filtered_results = await filter_service.filter_content_list(results, user_id)
    
    return filtered_results
```

### Image Display Integration

```python
from apps.moderation.nsfw_content_filter import get_nsfw_content_filter

async def get_image_metadata(image_id: str, user_id: Optional[str] = None):
    # Fetch image
    image = await fetch_image(image_id)
    
    # Check if should be blurred
    filter_service = get_nsfw_content_filter()
    should_blur = await filter_service.should_blur_image(image_id, user_id)
    
    return {
        'image': image,
        'should_blur': should_blur
    }
```

## Frontend Integration

### StoryCard Component

The `StoryCard` component has been updated to support NSFW warnings:

```tsx
// Automatically detects is_nsfw and is_blurred flags
<StoryCard story={story} />
```

**Features:**
- Shows NSFW badge on cover images
- Blurs cover images when is_blurred is true
- Shows NSFW badge in header when no cover image

### WhisperCard Component

The `WhisperCard` component has been updated to support NSFW warnings:

```tsx
// Automatically detects is_nsfw and is_blurred flags
<WhisperCard whisper={whisper} />
```

**Features:**
- Shows NSFW badge in header
- Blurs media images when is_blurred is true
- Click-to-reveal functionality for blurred images

## Requirements Satisfied

✅ **Requirement 8.4**: NSFW images blurred by default with click-to-reveal
✅ **Requirement 8.5**: Users can set content preferences (SHOW_ALL, BLUR_NSFW, HIDE_NSFW)
✅ **Requirement 8.6**: NSFW content excluded from feeds when user has "hide NSFW" preference
✅ **Requirement 8.7**: NSFW warning labels displayed on stories and whispers

## Content Filtering Flow

```
1. User requests content (stories, whispers, etc.)
   ↓
2. Backend fetches content from database
   ↓
3. NSFWContentFilter checks user's preference
   ↓
4. For each content item:
   - Check if content is flagged as NSFW
   - Apply user preference:
     * SHOW_ALL: Include with is_nsfw flag
     * BLUR_NSFW: Include with is_nsfw and is_blurred flags
     * HIDE_NSFW: Exclude from results
   ↓
5. Return filtered content to frontend
   ↓
6. Frontend components render with appropriate warnings/blurring
```

## Anonymous User Handling

Anonymous (unauthenticated) users are treated as having the `BLUR_NSFW` preference:
- NSFW content is shown in feeds
- NSFW images are blurred
- NSFW warning labels are displayed
- This provides a safe default while allowing content discovery

## Performance Considerations

### Caching

Consider caching NSFW flags to reduce database queries:

```python
from django.core.cache import cache

async def is_content_nsfw_cached(content_type, content_id):
    cache_key = f"nsfw:{content_type}:{content_id}"
    cached = cache.get(cache_key)
    
    if cached is not None:
        return cached
    
    is_nsfw = await service.is_content_nsfw(content_type, content_id)
    cache.set(cache_key, is_nsfw, timeout=3600)  # 1 hour
    
    return is_nsfw
```

### Batch Filtering

For large content lists, consider batch querying NSFW flags:

```python
async def filter_stories_batch(stories, user_id):
    # Get all story IDs
    story_ids = [story.id for story in stories]
    
    # Batch query NSFW flags
    flags = await db.nsfwflag.find_many(
        where={
            'content_type': NSFWContentType.STORY,
            'content_id': {'in': story_ids},
            'is_nsfw': True
        }
    )
    
    # Create lookup map
    nsfw_map = {flag.content_id: True for flag in flags}
    
    # Apply filtering
    # ... filter logic
```

## Testing

### Unit Tests

Test the filtering logic for each preference mode:

```python
import pytest
from apps.moderation.nsfw_content_filter import get_nsfw_content_filter
from prisma.enums import NSFWPreference

@pytest.mark.asyncio
async def test_filter_stories_show_all():
    """Test that SHOW_ALL preference includes all content."""
    # Setup
    filter_service = get_nsfw_content_filter()
    stories = [create_test_story(is_nsfw=True), create_test_story(is_nsfw=False)]
    
    # Mock user preference
    mock_preference(user_id, NSFWPreference.SHOW_ALL)
    
    # Execute
    filtered = await filter_service.filter_stories(stories, user_id)
    
    # Assert
    assert len(filtered) == 2

@pytest.mark.asyncio
async def test_filter_stories_hide_nsfw():
    """Test that HIDE_NSFW preference excludes NSFW content."""
    # Setup
    filter_service = get_nsfw_content_filter()
    stories = [create_test_story(is_nsfw=True), create_test_story(is_nsfw=False)]
    
    # Mock user preference
    mock_preference(user_id, NSFWPreference.HIDE_NSFW)
    
    # Execute
    filtered = await filter_service.filter_stories(stories, user_id)
    
    # Assert
    assert len(filtered) == 1
    assert not filtered[0].is_nsfw
```

### Integration Tests

Test the full flow from API to frontend:

1. Create NSFW flagged content
2. Set user preference
3. Request content via API
4. Verify filtering is applied correctly
5. Verify frontend displays warnings/blurring

## Future Enhancements

Potential improvements:

1. **Per-content-type preferences**: Allow users to set different preferences for stories vs whispers
2. **Temporary reveal**: Allow users to temporarily show NSFW content without changing preference
3. **Content creator override**: Allow creators to override automatic NSFW detection
4. **NSFW categories**: Support different NSFW categories (violence, nudity, etc.) with separate preferences
5. **Age-based defaults**: Set stricter defaults for younger users
6. **Analytics**: Track how users interact with NSFW content and preferences

## Related Documentation

- [NSFW Detection](./nsfw-detection.md) - AWS Rekognition integration and detection
- [Moderation Dashboard](./dashboard.md) - Moderator tools for reviewing NSFW flags
- [Content Filters](./content-filters.md) - Automated content filtering system

