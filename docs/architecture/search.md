# Full-Text Search System

This document describes the full-text search implementation using PostgreSQL's built-in full-text search capabilities.

## Overview

The search system provides fast, relevant search results for stories, authors, and tags with advanced features including:
- Full-text search with relevance ranking
- Search filters (genre, completion status, word count, date)
- Autocomplete suggestions
- Search result caching (5-minute TTL)
- Search analytics and tracking
- Boolean operators and phrase search

## Requirements

Implements the following requirements:
- **Requirement 35.1**: Full-text search using PostgreSQL
- **Requirement 35.2**: Index story titles, descriptions, author names, and tags
- **Requirement 35.3**: Return results within 200ms
- **Requirement 35.4**: Rank results by relevance using TF-IDF
- **Requirement 35.5**: Support search filters
- **Requirement 35.6**: Autocomplete with 100ms response time
- **Requirement 35.7**: Cache popular queries for 5 minutes
- **Requirement 35.8**: Pagination with 20 results per page
- **Requirement 35.9**: Highlight search terms in snippets
- **Requirement 35.10**: Track search queries and clicks
- **Requirement 35.11**: Handle typos with fuzzy matching
- **Requirement 35.12**: Support phrase search and boolean operators
- **Requirement 35.13**: Incremental index updates

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Search API Layer                          │
│  /api/search/stories, /authors, /autocomplete              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Search Service Layer                        │
│  - Query parsing and building                               │
│  - Result ranking and formatting                            │
│  - Cache management (5-min TTL)                             │
│  - Analytics tracking                                       │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
┌───────────────────────┐   ┌───────────────────────┐
│   PostgreSQL FTS      │   │   Redis Cache         │
│   - tsvector indexes  │   │   - Search results    │
│   - GIN indexes       │   │   - Autocomplete      │
│   - Triggers          │   │   - Popular queries   │
└───────────────────────┘   └───────────────────────┘
```

## Components

### 1. Search Indexes (`search_indexes.py`)

PostgreSQL full-text search indexes with automatic updates:

**Story Search Index**:
- Title (weight A - highest)
- Description (weight B - medium)
- Content preview (weight C - lowest)

**Author Search Index**:
- Display name (weight A)
- Username (weight A)
- Bio (weight B)

**Tag Search Index**:
- Name (weight A)
- Description (weight B)

**Filter Indexes**:
- Genre
- Completion status
- Word count
- Update date

### 2. Search Service (`search_service.py`)

Core search functionality:
- `search_stories()` - Search stories with filters
- `search_authors()` - Search authors
- `autocomplete()` - Get autocomplete suggestions
- `get_popular_searches()` - Get popular queries
- `track_click()` - Track result clicks

### 3. Search API (`apps/search/views.py`)

REST API endpoints:
- `GET /api/search/stories` - Search stories
- `GET /api/search/authors` - Search authors
- `GET /api/search/autocomplete` - Autocomplete
- `GET /api/search/popular` - Popular searches
- `POST /api/search/track-click` - Track clicks

## Setup

### 1. Create Search Indexes

```bash
# Run Django management command
python manage.py create_search_indexes
```

This creates:
- tsvector columns on stories, user_profiles, and tags
- GIN indexes for fast full-text search
- Triggers for automatic index updates
- Filter indexes for search refinement
- search_queries table for analytics

### 2. Configure Django Settings

```python
# settings.py

INSTALLED_APPS = [
    # ... other apps ...
    'apps.search',
]

# Search configuration
SEARCH_RESULTS_PER_PAGE = 20
SEARCH_CACHE_TTL = 300  # 5 minutes
SEARCH_AUTOCOMPLETE_TIMEOUT_MS = 100
```

### 3. Add URL Configuration

```python
# urls.py

urlpatterns = [
    # ... other patterns ...
    path('api/search/', include('apps.search.urls')),
]
```

## Usage

### Basic Story Search

```bash
GET /api/search/stories?q=fantasy+adventure&page=1
```

Response:
```json
{
  "results": [
    {
      "id": 123,
      "type": "story",
      "title": "The Fantasy Adventure",
      "description": "An epic tale of magic and adventure",
      "snippet": "...epic tale of <b>fantasy</b> and <b>adventure</b>...",
      "rank": 0.8542,
      "metadata": {
        "genre": "Fantasy",
        "completion_status": "completed",
        "word_count": 125000,
        "updated_at": "2026-02-15T10:30:00Z",
        "author_id": 456
      }
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "total_pages": 3,
  "has_next": true,
  "has_prev": false
}
```

### Search with Filters

```bash
GET /api/search/stories?q=magic&genre=Fantasy&completion_status=completed&min_word_count=50000&page=1
```

### Author Search

```bash
GET /api/search/authors?q=john+smith&page=1
```

### Autocomplete

```bash
GET /api/search/autocomplete?q=dra&limit=10
```

Response:
```json
{
  "suggestions": [
    "Dragon's Quest",
    "Dragon Rider",
    "The Dragon King",
    "Dragons of the North"
  ]
}
```

### Popular Searches

```bash
GET /api/search/popular?days=7&limit=20
```

Response:
```json
{
  "popular_searches": [
    {
      "query": "fantasy adventure",
      "search_count": 1523,
      "avg_results": 42.5,
      "avg_response_time": 85.3
    }
  ]
}
```

### Track Search Click

```bash
POST /api/search/track-click
Content-Type: application/json

{
  "query": "fantasy adventure",
  "result_id": 123,
  "result_type": "story"
}
```

## Advanced Search Features

### Boolean Operators

**AND (default)**:
```
GET /api/search/stories?q=magic+adventure
# Searches for: magic AND adventure
```

**OR**:
```
GET /api/search/stories?q=dragon+OR+wizard
# Searches for: dragon OR wizard
```

**NOT**:
```
GET /api/search/stories?q=fantasy+NOT+romance
# Searches for: fantasy NOT romance
```

### Phrase Search

Use quotes for exact phrase matching:
```
GET /api/search/stories?q="dark+forest"
# Searches for exact phrase: "dark forest"
```

### Combined Search

```
GET /api/search/stories?q="epic+quest"+AND+(dragon+OR+wizard)+NOT+romance
# Complex query with phrases and operators
```

## Search Filters

### Genre Filter

```bash
GET /api/search/stories?q=adventure&genre=Fantasy
```

Available genres: Fantasy, Science Fiction, Romance, Mystery, Thriller, Horror, etc.

### Completion Status Filter

```bash
GET /api/search/stories?q=adventure&completion_status=completed
```

Available statuses: completed, ongoing, hiatus

### Word Count Filter

```bash
# Stories with 50,000 to 150,000 words
GET /api/search/stories?q=adventure&min_word_count=50000&max_word_count=150000
```

### Date Filter

```bash
# Stories updated in the last 30 days
GET /api/search/stories?q=adventure&updated_after=2026-01-18T00:00:00Z
```

### Combined Filters

```bash
GET /api/search/stories?q=magic&genre=Fantasy&completion_status=completed&min_word_count=100000&updated_after=2026-01-01T00:00:00Z
```

## Performance

### Response Times

Target response times (Requirement 35.3, 35.6):
- **Story search**: < 200ms
- **Author search**: < 200ms
- **Autocomplete**: < 100ms

### Caching Strategy

**Cache TTL**: 5 minutes (Requirement 35.7)

**Cached Items**:
- Search results (per query, filters, and page)
- Autocomplete suggestions
- Popular searches (1 hour TTL)

**Cache Invalidation**:
```python
from infrastructure.search_service import search_service

# Invalidate all search caches
search_service.invalidate_search_cache()

# Invalidate specific search type
search_service.invalidate_search_cache('stories')
```

### Optimization Tips

1. **Use filters** to narrow results before full-text search
2. **Cache popular queries** automatically (5-minute TTL)
3. **Limit result count** with pagination
4. **Use autocomplete** to guide users to popular queries

## Search Analytics

### Track Search Queries

All searches are automatically tracked in the `search_queries` table:

```sql
SELECT 
    query,
    COUNT(*) as search_count,
    AVG(result_count) as avg_results,
    AVG(response_time_ms) as avg_response_time
FROM search_queries
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY query
ORDER BY search_count DESC
LIMIT 20;
```

### Track Result Clicks

Track when users click on search results:

```python
search_service.track_click(
    query='fantasy adventure',
    result_id=123,
    result_type='story',
    user_id=456
)
```

### Analyze Search Performance

```sql
-- Average response time by query
SELECT 
    query,
    AVG(response_time_ms) as avg_ms,
    COUNT(*) as count
FROM search_queries
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY query
HAVING AVG(response_time_ms) > 200
ORDER BY avg_ms DESC;

-- Queries with no results
SELECT 
    query,
    COUNT(*) as count
FROM search_queries
WHERE result_count = 0
    AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY query
ORDER BY count DESC;
```

## Relevance Ranking

### Ranking Algorithm

PostgreSQL uses TF-IDF (Term Frequency-Inverse Document Frequency) for relevance ranking:

- **Term Frequency**: How often the search term appears in the document
- **Inverse Document Frequency**: How rare the term is across all documents
- **Weight**: Title matches rank higher than description matches

### Ranking Weights

- **Title (A)**: Highest weight (1.0)
- **Description (B)**: Medium weight (0.4)
- **Content Preview (C)**: Lowest weight (0.1)

### Custom Ranking

Combine text rank with other factors:

```sql
SELECT 
    id, title,
    (ts_rank(search_vector, query) * 0.7 + 
     (view_count / 10000.0) * 0.2 +
     (like_count / 1000.0) * 0.1) AS combined_rank
FROM stories
WHERE search_vector @@ query
ORDER BY combined_rank DESC;
```

## Fuzzy Matching

### Typo Tolerance

Enable fuzzy matching for typos (Requirement 35.11):

```sql
-- Requires pg_trgm extension
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Search with similarity
SELECT 
    id, title,
    similarity(title, 'fantacy') AS sim  -- Typo: fantacy
FROM stories
WHERE similarity(title, 'fantacy') > 0.3
ORDER BY sim DESC;
```

### Autocorrect Suggestions

```python
# Get suggestions for misspelled queries
def get_autocorrect_suggestions(query):
    sql = """
        SELECT DISTINCT title
        FROM stories
        WHERE similarity(title, %s) > 0.3
        ORDER BY similarity(title, %s) DESC
        LIMIT 5
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [query, query])
        return [row[0] for row in cursor.fetchall()]
```

## Monitoring

### Key Metrics

Monitor these metrics:

- **Average response time**: Should be < 200ms
- **Cache hit rate**: Should be > 70%
- **Queries with no results**: Identify missing content
- **Popular queries**: Understand user interests
- **Click-through rate**: Measure result relevance

### Performance Monitoring

```python
# Get search performance metrics
from infrastructure.search_service import search_service

# Popular searches
popular = search_service.get_popular_searches(days=7, limit=20)

# Analyze response times
for search in popular:
    print(f"{search['query']}: {search['avg_response_time']:.1f}ms")
```

## Troubleshooting

### Slow Search Queries

**Symptoms**: Response time > 200ms

**Solutions**:
1. Check if indexes exist: `\d+ stories` in psql
2. Analyze query plan: `EXPLAIN ANALYZE SELECT ...`
3. Rebuild indexes: `REINDEX INDEX idx_stories_search_vector;`
4. Increase cache TTL for popular queries
5. Add more specific filters

### No Search Results

**Symptoms**: Queries return 0 results

**Solutions**:
1. Check if search vectors are populated
2. Verify query syntax (boolean operators)
3. Try simpler queries without operators
4. Check if content is published
5. Review search analytics for similar queries

### Autocomplete Not Working

**Symptoms**: No suggestions returned

**Solutions**:
1. Check if cache is working
2. Verify query length (minimum 2 characters)
3. Check if stories exist with matching titles
4. Review autocomplete query in search_service.py

## Best Practices

### 1. Use Specific Queries

```python
# Good: Specific query
GET /api/search/stories?q=dragon+quest+fantasy

# Bad: Too generic
GET /api/search/stories?q=story
```

### 2. Apply Filters Early

```python
# Good: Filter before search
GET /api/search/stories?q=adventure&genre=Fantasy&completion_status=completed

# Bad: Search all, filter client-side
GET /api/search/stories?q=adventure
```

### 3. Use Autocomplete

Guide users to popular queries with autocomplete:

```javascript
// Frontend autocomplete
const suggestions = await fetch(
  `/api/search/autocomplete?q=${query}`
);
```

### 4. Track User Behavior

Track clicks to improve relevance:

```javascript
// Track when user clicks result
await fetch('/api/search/track-click', {
  method: 'POST',
  body: JSON.stringify({
    query: searchQuery,
    result_id: storyId,
    result_type: 'story'
  })
});
```

### 5. Cache Aggressively

Popular queries are automatically cached for 5 minutes.

## Related Documentation

- [Database indexes](../../apps/backend/infrastructure/database_indexes.py)
- [Database caching](./database-cache.md)
- [Search indexes](../../apps/backend/infrastructure/search_indexes.py)
- [Search service](../../apps/backend/infrastructure/search_service.py)

## Support

For issues or questions:
1. Check search analytics for query patterns
2. Review PostgreSQL logs for slow queries
3. Verify search indexes exist
4. Test queries directly in PostgreSQL
5. Check cache hit rate
