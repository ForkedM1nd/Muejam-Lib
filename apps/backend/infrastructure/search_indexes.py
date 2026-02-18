"""
Full-Text Search Indexes for PostgreSQL

This module provides SQL statements to create full-text search indexes
for stories, authors, and tags using PostgreSQL's built-in full-text search.

Requirements: 35.1, 35.2, 35.13
"""

# PostgreSQL Full-Text Search Indexes
# These indexes enable fast full-text search on story titles, descriptions, author names, and tags

SEARCH_INDEXES = [
    # Story full-text search index
    # Combines title (weight A), description (weight B), and content preview (weight C)
    """
    -- Create text search configuration for English
    CREATE TEXT SEARCH CONFIGURATION IF NOT EXISTS english_unaccent (COPY = english);
    
    -- Add tsvector column for story search
    ALTER TABLE stories 
    ADD COLUMN IF NOT EXISTS search_vector tsvector;
    
    -- Create index on search vector
    CREATE INDEX IF NOT EXISTS idx_stories_search_vector 
    ON stories USING GIN(search_vector);
    
    -- Create trigger to automatically update search vector
    CREATE OR REPLACE FUNCTION stories_search_vector_trigger() RETURNS trigger AS $$
    BEGIN
        NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(NEW.content_preview, '')), 'C');
        RETURN NEW;
    END
    $$ LANGUAGE plpgsql;
    
    DROP TRIGGER IF EXISTS stories_search_vector_update ON stories;
    CREATE TRIGGER stories_search_vector_update
    BEFORE INSERT OR UPDATE ON stories
    FOR EACH ROW EXECUTE FUNCTION stories_search_vector_trigger();
    
    -- Update existing rows
    UPDATE stories SET search_vector = 
        setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(content_preview, '')), 'C')
    WHERE search_vector IS NULL;
    """,
    
    # Author full-text search index
    """
    -- Add tsvector column for author search
    ALTER TABLE user_profiles 
    ADD COLUMN IF NOT EXISTS search_vector tsvector;
    
    -- Create index on search vector
    CREATE INDEX IF NOT EXISTS idx_user_profiles_search_vector 
    ON user_profiles USING GIN(search_vector);
    
    -- Create trigger to automatically update search vector
    CREATE OR REPLACE FUNCTION user_profiles_search_vector_trigger() RETURNS trigger AS $$
    BEGIN
        NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.display_name, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.username, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.bio, '')), 'B');
        RETURN NEW;
    END
    $$ LANGUAGE plpgsql;
    
    DROP TRIGGER IF EXISTS user_profiles_search_vector_update ON user_profiles;
    CREATE TRIGGER user_profiles_search_vector_update
    BEFORE INSERT OR UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION user_profiles_search_vector_trigger();
    
    -- Update existing rows
    UPDATE user_profiles SET search_vector = 
        setweight(to_tsvector('english', COALESCE(display_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(username, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(bio, '')), 'B')
    WHERE search_vector IS NULL;
    """,
    
    # Tag full-text search index
    """
    -- Add tsvector column for tag search
    ALTER TABLE tags 
    ADD COLUMN IF NOT EXISTS search_vector tsvector;
    
    -- Create index on search vector
    CREATE INDEX IF NOT EXISTS idx_tags_search_vector 
    ON tags USING GIN(search_vector);
    
    -- Create trigger to automatically update search vector
    CREATE OR REPLACE FUNCTION tags_search_vector_trigger() RETURNS trigger AS $$
    BEGIN
        NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
        RETURN NEW;
    END
    $$ LANGUAGE plpgsql;
    
    DROP TRIGGER IF EXISTS tags_search_vector_update ON tags;
    CREATE TRIGGER tags_search_vector_update
    BEFORE INSERT OR UPDATE ON tags
    FOR EACH ROW EXECUTE FUNCTION tags_search_vector_trigger();
    
    -- Update existing rows
    UPDATE tags SET search_vector = 
        setweight(to_tsvector('english', COALESCE(name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(description, '')), 'B')
    WHERE search_vector IS NULL;
    """,
    
    # Additional indexes for search filters
    """
    -- Index for genre filter
    CREATE INDEX IF NOT EXISTS idx_stories_genre 
    ON stories(genre) WHERE published = true;
    
    -- Index for completion status filter
    CREATE INDEX IF NOT EXISTS idx_stories_completion_status 
    ON stories(completion_status) WHERE published = true;
    
    -- Index for word count filter
    CREATE INDEX IF NOT EXISTS idx_stories_word_count 
    ON stories(word_count) WHERE published = true;
    
    -- Index for update date filter
    CREATE INDEX IF NOT EXISTS idx_stories_updated_at 
    ON stories(updated_at DESC) WHERE published = true;
    
    -- Composite index for filtered search
    CREATE INDEX IF NOT EXISTS idx_stories_search_filters 
    ON stories(published, genre, completion_status, updated_at DESC) 
    WHERE published = true;
    """,
    
    # Search query tracking table
    """
    -- Create search query tracking table
    CREATE TABLE IF NOT EXISTS search_queries (
        id SERIAL PRIMARY KEY,
        query TEXT NOT NULL,
        user_id INTEGER,
        result_count INTEGER,
        clicked_result_id INTEGER,
        clicked_result_type VARCHAR(50),
        search_filters JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        response_time_ms INTEGER
    );
    
    -- Index for query analytics
    CREATE INDEX IF NOT EXISTS idx_search_queries_query 
    ON search_queries(query);
    
    CREATE INDEX IF NOT EXISTS idx_search_queries_created_at 
    ON search_queries(created_at DESC);
    
    CREATE INDEX IF NOT EXISTS idx_search_queries_user_id 
    ON search_queries(user_id, created_at DESC);
    """,
]


def get_search_index_sql() -> str:
    """
    Get all search index SQL statements as a single string.
    
    Returns:
        Combined SQL statements for creating search indexes
    """
    return "\n\n".join(SEARCH_INDEXES)


# Django management command helper
def create_search_indexes(cursor):
    """
    Create all search indexes using a database cursor.
    
    Args:
        cursor: Database cursor for executing SQL
        
    Returns:
        Number of indexes created
    """
    count = 0
    for sql in SEARCH_INDEXES:
        try:
            cursor.execute(sql)
            count += 1
            print(f"✓ Created search index {count}/{len(SEARCH_INDEXES)}")
        except Exception as e:
            print(f"✗ Error creating search index {count + 1}: {e}")
            raise
    
    return count


# Search query examples for testing
SEARCH_QUERY_EXAMPLES = """
-- Example 1: Simple text search
SELECT 
    id, title, description,
    ts_rank(search_vector, to_tsquery('english', 'fantasy')) AS rank
FROM stories
WHERE search_vector @@ to_tsquery('english', 'fantasy')
    AND published = true
ORDER BY rank DESC, updated_at DESC
LIMIT 20;

-- Example 2: Multi-word search with AND
SELECT 
    id, title, description,
    ts_rank(search_vector, to_tsquery('english', 'magic & adventure')) AS rank
FROM stories
WHERE search_vector @@ to_tsquery('english', 'magic & adventure')
    AND published = true
ORDER BY rank DESC
LIMIT 20;

-- Example 3: Search with OR operator
SELECT 
    id, title, description,
    ts_rank(search_vector, to_tsquery('english', 'dragon | wizard')) AS rank
FROM stories
WHERE search_vector @@ to_tsquery('english', 'dragon | wizard')
    AND published = true
ORDER BY rank DESC
LIMIT 20;

-- Example 4: Phrase search
SELECT 
    id, title, description,
    ts_rank(search_vector, phraseto_tsquery('english', 'dark forest')) AS rank
FROM stories
WHERE search_vector @@ phraseto_tsquery('english', 'dark forest')
    AND published = true
ORDER BY rank DESC
LIMIT 20;

-- Example 5: Search with filters
SELECT 
    id, title, description, genre, word_count,
    ts_rank(search_vector, to_tsquery('english', 'adventure')) AS rank
FROM stories
WHERE search_vector @@ to_tsquery('english', 'adventure')
    AND published = true
    AND genre = 'Fantasy'
    AND completion_status = 'completed'
    AND word_count >= 50000
ORDER BY rank DESC
LIMIT 20;

-- Example 6: Author search
SELECT 
    id, display_name, username, bio,
    ts_rank(search_vector, to_tsquery('english', 'author_name')) AS rank
FROM user_profiles
WHERE search_vector @@ to_tsquery('english', 'author_name')
ORDER BY rank DESC
LIMIT 20;

-- Example 7: Tag search
SELECT 
    id, name, description,
    ts_rank(search_vector, to_tsquery('english', 'romance')) AS rank
FROM tags
WHERE search_vector @@ to_tsquery('english', 'romance')
ORDER BY rank DESC
LIMIT 20;

-- Example 8: Fuzzy search (using similarity)
-- Requires pg_trgm extension
CREATE EXTENSION IF NOT EXISTS pg_trgm;

SELECT 
    id, title, description,
    similarity(title, 'fantacy') AS sim  -- Typo: fantacy instead of fantasy
FROM stories
WHERE published = true
    AND similarity(title, 'fantacy') > 0.3
ORDER BY sim DESC
LIMIT 20;

-- Example 9: Autocomplete suggestions
SELECT DISTINCT 
    word,
    COUNT(*) as frequency
FROM (
    SELECT unnest(tsvector_to_array(search_vector)) as word
    FROM stories
    WHERE published = true
) words
WHERE word LIKE 'dra%'  -- Autocomplete for "dra"
GROUP BY word
ORDER BY frequency DESC, word
LIMIT 10;

-- Example 10: Popular search queries
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
"""
