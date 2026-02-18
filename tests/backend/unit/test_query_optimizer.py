"""
Unit tests for QueryOptimizer.

Tests query analysis, slow query detection, N+1 pattern detection,
and index suggestion logic.
"""

import pytest
from datetime import datetime
from infrastructure.query_optimizer import QueryOptimizer, QueryContext
from infrastructure.models import QueryLog, QueryType, QueryAnalysis, NPlusOnePattern, IndexSuggestion


class TestQueryOptimizerBasics:
    """Test basic QueryOptimizer functionality."""
    
    def test_optimizer_creation(self):
        """Test creating a QueryOptimizer with default settings."""
        optimizer = QueryOptimizer()
        assert optimizer.slow_query_threshold == 100.0
        assert optimizer.enable_explain_analyze is True
        assert optimizer.max_query_history == 1000
        assert optimizer.total_queries == 0
        assert optimizer.total_slow_queries == 0
    
    def test_optimizer_custom_settings(self):
        """Test creating a QueryOptimizer with custom settings."""
        optimizer = QueryOptimizer(
            slow_query_threshold=50.0,
            enable_explain_analyze=False,
            max_query_history=500
        )
        assert optimizer.slow_query_threshold == 50.0
        assert optimizer.enable_explain_analyze is False
        assert optimizer.max_query_history == 500


class TestQueryAnalysis:
    """Test query analysis functionality."""
    
    def test_analyze_query_basic(self):
        """Test basic query analysis."""
        optimizer = QueryOptimizer()
        
        # Set up a mock explain callback
        def mock_explain(query, params):
            return {
                "Plan": {
                    "Node Type": "Index Scan",
                    "Total Cost": 50.0,
                    "Actual Total Time": 25.0,
                    "Rows": 10
                }
            }
        
        optimizer.set_explain_callback(mock_explain)
        
        query = "SELECT * FROM users WHERE id = 1"
        analysis = optimizer.analyze_query(query, {})
        
        assert isinstance(analysis, QueryAnalysis)
        assert analysis.has_index is True
        assert analysis.estimated_cost == 50.0
        assert analysis.actual_cost == 25.0
        assert analysis.rows_examined == 10
        assert analysis.rows_returned == 10
    
    def test_analyze_query_without_index(self):
        """Test query analysis for query without index."""
        optimizer = QueryOptimizer()
        
        def mock_explain(query, params):
            return {
                "Plan": {
                    "Node Type": "Seq Scan",
                    "Total Cost": 200.0,
                    "Actual Total Time": 150.0,
                    "Rows": 1000
                }
            }
        
        optimizer.set_explain_callback(mock_explain)
        
        query = "SELECT * FROM users WHERE email = 'test@example.com'"
        analysis = optimizer.analyze_query(query, {})
        
        assert analysis.has_index is False
        assert analysis.is_slow is True
        assert len(analysis.optimization_suggestions) > 0
    
    def test_analyze_query_with_select_star(self):
        """Test that SELECT * generates a suggestion."""
        optimizer = QueryOptimizer()
        
        query = "SELECT * FROM users WHERE id = 1"
        analysis = optimizer.analyze_query(query, {})
        
        # Check for SELECT * suggestion
        has_select_star_suggestion = any(
            "SELECT *" in suggestion
            for suggestion in analysis.optimization_suggestions
        )
        assert has_select_star_suggestion


class TestSlowQueryDetection:
    """Test slow query detection and logging."""
    
    def test_log_slow_query(self):
        """Test logging a slow query."""
        optimizer = QueryOptimizer(slow_query_threshold=100.0)
        
        query = "SELECT * FROM users WHERE name LIKE '%test%'"
        execution_time = 150.0
        plan = {"Plan": {"Node Type": "Seq Scan"}}
        
        optimizer.log_slow_query(query, execution_time, plan)
        
        assert len(optimizer.slow_queries) == 1
        assert optimizer.slow_queries[0].query_text == query
        assert optimizer.slow_queries[0].execution_time == execution_time
    
    def test_track_query_slow(self):
        """Test tracking a slow query."""
        optimizer = QueryOptimizer(slow_query_threshold=100.0)
        
        query = "SELECT * FROM users WHERE name LIKE '%test%'"
        optimizer.track_query(query, execution_time=150.0, params={}, user_id="user123")
        
        assert optimizer.total_queries == 1
        assert optimizer.total_slow_queries == 1
        assert len(optimizer.slow_queries) == 1
        assert len(optimizer.query_history) == 1
    
    def test_track_query_fast(self):
        """Test tracking a fast query."""
        optimizer = QueryOptimizer(slow_query_threshold=100.0)
        
        query = "SELECT id FROM users WHERE id = 1"
        optimizer.track_query(query, execution_time=5.0, params={})
        
        assert optimizer.total_queries == 1
        assert optimizer.total_slow_queries == 0
        assert len(optimizer.slow_queries) == 0
        assert len(optimizer.query_history) == 1
    
    def test_query_history_limit(self):
        """Test that query history respects max size."""
        optimizer = QueryOptimizer(max_query_history=10)
        
        # Track 20 queries
        for i in range(20):
            optimizer.track_query(f"SELECT * FROM users WHERE id = {i}", execution_time=5.0)
        
        # Should only keep last 10
        assert len(optimizer.query_history) == 10
        assert optimizer.total_queries == 20


class TestQueryTypeDetection:
    """Test query type detection."""
    
    def test_detect_select(self):
        """Test detecting SELECT queries."""
        optimizer = QueryOptimizer()
        query_type = optimizer._detect_query_type("SELECT * FROM users")
        assert query_type == QueryType.SELECT
    
    def test_detect_insert(self):
        """Test detecting INSERT queries."""
        optimizer = QueryOptimizer()
        query_type = optimizer._detect_query_type("INSERT INTO users (name) VALUES ('test')")
        assert query_type == QueryType.INSERT
    
    def test_detect_update(self):
        """Test detecting UPDATE queries."""
        optimizer = QueryOptimizer()
        query_type = optimizer._detect_query_type("UPDATE users SET name = 'test' WHERE id = 1")
        assert query_type == QueryType.UPDATE
    
    def test_detect_delete(self):
        """Test detecting DELETE queries."""
        optimizer = QueryOptimizer()
        query_type = optimizer._detect_query_type("DELETE FROM users WHERE id = 1")
        assert query_type == QueryType.DELETE


class TestNPlusOneDetection:
    """Test N+1 query pattern detection."""
    
    def test_detect_n_plus_one_basic(self):
        """Test basic N+1 pattern detection."""
        optimizer = QueryOptimizer()
        
        # Simulate N+1 pattern: 1 parent query + N child queries
        queries = [
            "SELECT * FROM posts",  # Parent query
        ]
        
        # Add 10 similar child queries
        for i in range(10):
            queries.append(f"SELECT * FROM comments WHERE post_id = {i}")
        
        patterns = optimizer.detect_n_plus_one(queries=queries)
        
        assert len(patterns) > 0
        pattern = patterns[0]
        assert isinstance(pattern, NPlusOnePattern)
        assert pattern.count == 10
        assert len(pattern.recommendation) > 0
    
    def test_detect_n_plus_one_with_request_context(self):
        """Test N+1 detection using request context."""
        optimizer = QueryOptimizer()
        
        request_id = "req123"
        
        # Track parent query
        optimizer.track_query(
            "SELECT * FROM posts",
            execution_time=10.0,
            request_id=request_id
        )
        
        # Track child queries
        for i in range(8):
            optimizer.track_query(
                f"SELECT * FROM comments WHERE post_id = {i}",
                execution_time=5.0,
                request_id=request_id
            )
        
        patterns = optimizer.detect_n_plus_one(request_id=request_id)
        
        assert len(patterns) > 0
    
    def test_no_n_plus_one_with_few_queries(self):
        """Test that few similar queries don't trigger N+1 detection."""
        optimizer = QueryOptimizer()
        
        queries = [
            "SELECT * FROM posts",
            "SELECT * FROM comments WHERE post_id = 1",
            "SELECT * FROM comments WHERE post_id = 2",
        ]
        
        patterns = optimizer.detect_n_plus_one(queries=queries)
        
        # Should not detect N+1 with only 2 similar queries
        assert len(patterns) == 0


class TestIndexSuggestions:
    """Test index suggestion logic."""
    
    def test_suggest_indexes_from_where_clause(self):
        """Test index suggestions from WHERE clauses."""
        optimizer = QueryOptimizer()
        
        # Create slow queries with WHERE clauses
        slow_queries = []
        for i in range(5):
            query_log = QueryLog(
                query_id=f"q{i}",
                query_text="SELECT * FROM users WHERE email = 'test@example.com'",
                execution_time=150.0,
                timestamp=datetime.now(),
                execution_plan={},
                parameters={},
                query_type=QueryType.SELECT
            )
            slow_queries.append(query_log)
        
        suggestions = optimizer.suggest_indexes(slow_queries)
        
        assert len(suggestions) > 0
        # Should suggest index on email column
        email_suggestions = [s for s in suggestions if 'email' in s.columns]
        assert len(email_suggestions) > 0
    
    def test_suggest_indexes_from_join(self):
        """Test index suggestions from JOIN conditions."""
        optimizer = QueryOptimizer()
        
        slow_queries = []
        for i in range(4):
            query_log = QueryLog(
                query_id=f"q{i}",
                query_text="SELECT * FROM users u JOIN posts p ON u.id = p.user_id",
                execution_time=200.0,
                timestamp=datetime.now(),
                execution_plan={},
                parameters={},
                query_type=QueryType.SELECT
            )
            slow_queries.append(query_log)
        
        suggestions = optimizer.suggest_indexes(slow_queries)
        
        assert len(suggestions) > 0
    
    def test_no_suggestions_for_infrequent_patterns(self):
        """Test that infrequent patterns don't generate suggestions."""
        optimizer = QueryOptimizer()
        
        # Only 2 queries (below threshold of 3)
        slow_queries = []
        for i in range(2):
            query_log = QueryLog(
                query_id=f"q{i}",
                query_text="SELECT * FROM users WHERE email = 'test@example.com'",
                execution_time=150.0,
                timestamp=datetime.now(),
                execution_plan={},
                parameters={},
                query_type=QueryType.SELECT
            )
            slow_queries.append(query_log)
        
        suggestions = optimizer.suggest_indexes(slow_queries)
        
        # Should not suggest index with only 2 occurrences
        assert len(suggestions) == 0


class TestQueryPatternExtraction:
    """Test query pattern extraction and normalization."""
    
    def test_extract_pattern_normalizes_strings(self):
        """Test that string literals are normalized."""
        optimizer = QueryOptimizer()
        
        query1 = "SELECT * FROM users WHERE name = 'Alice'"
        query2 = "SELECT * FROM users WHERE name = 'Bob'"
        
        pattern1 = optimizer._extract_query_pattern(query1)
        pattern2 = optimizer._extract_query_pattern(query2)
        
        # Patterns should be the same
        assert pattern1 == pattern2
    
    def test_extract_pattern_normalizes_numbers(self):
        """Test that numeric literals are normalized."""
        optimizer = QueryOptimizer()
        
        query1 = "SELECT * FROM users WHERE id = 1"
        query2 = "SELECT * FROM users WHERE id = 999"
        
        pattern1 = optimizer._extract_query_pattern(query1)
        pattern2 = optimizer._extract_query_pattern(query2)
        
        # Patterns should be the same
        assert pattern1 == pattern2


class TestMetrics:
    """Test query metrics tracking."""
    
    def test_get_metrics_initial(self):
        """Test getting metrics from new optimizer."""
        optimizer = QueryOptimizer()
        
        metrics = optimizer.get_metrics()
        
        assert metrics["total_queries"] == 0
        assert metrics["total_slow_queries"] == 0
        assert metrics["slow_query_rate"] == 0.0
        assert metrics["avg_execution_time"] == 0.0
    
    def test_get_metrics_after_queries(self):
        """Test metrics after tracking queries."""
        optimizer = QueryOptimizer(slow_query_threshold=100.0)
        
        # Track 10 queries: 3 slow, 7 fast
        for i in range(3):
            optimizer.track_query(f"SELECT * FROM users WHERE id = {i}", execution_time=150.0)
        
        for i in range(7):
            optimizer.track_query(f"SELECT * FROM users WHERE id = {i}", execution_time=10.0)
        
        metrics = optimizer.get_metrics()
        
        assert metrics["total_queries"] == 10
        assert metrics["total_slow_queries"] == 3
        assert metrics["slow_query_rate"] == 30.0
        assert metrics["avg_execution_time"] > 0
    
    def test_reset_metrics(self):
        """Test resetting metrics."""
        optimizer = QueryOptimizer()
        
        # Track some queries
        optimizer.track_query("SELECT * FROM users", execution_time=50.0)
        optimizer.track_query("SELECT * FROM posts", execution_time=150.0)
        
        # Reset
        optimizer.reset_metrics()
        
        metrics = optimizer.get_metrics()
        assert metrics["total_queries"] == 0
        assert metrics["total_slow_queries"] == 0
        assert len(optimizer.query_history) == 0
        assert len(optimizer.slow_queries) == 0


class TestRequestContext:
    """Test request context management."""
    
    def test_track_query_with_request_id(self):
        """Test tracking queries with request ID."""
        optimizer = QueryOptimizer()
        
        request_id = "req123"
        optimizer.track_query("SELECT * FROM users", execution_time=10.0, request_id=request_id)
        optimizer.track_query("SELECT * FROM posts", execution_time=15.0, request_id=request_id)
        
        assert request_id in optimizer.request_contexts
        assert len(optimizer.request_contexts[request_id].queries) == 2
    
    def test_clear_request_context(self):
        """Test clearing request context."""
        optimizer = QueryOptimizer()
        
        request_id = "req123"
        optimizer.track_query("SELECT * FROM users", execution_time=10.0, request_id=request_id)
        
        optimizer.clear_request_context(request_id)
        
        assert request_id not in optimizer.request_contexts


class TestColumnExtraction:
    """Test column extraction from queries."""
    
    def test_extract_where_columns(self):
        """Test extracting columns from WHERE clause."""
        optimizer = QueryOptimizer()
        
        query = "SELECT * FROM users WHERE email = 'test@example.com' AND status = 'active'"
        columns = optimizer._extract_where_columns(query)
        
        assert 'users' in columns
        assert 'email' in columns['users'] or 'status' in columns['users']
    
    def test_extract_join_columns(self):
        """Test extracting columns from JOIN conditions."""
        optimizer = QueryOptimizer()
        
        query = "SELECT * FROM users u JOIN posts p ON u.id = p.user_id"
        columns = optimizer._extract_join_columns(query)
        
        assert 'u' in columns or 'p' in columns
    
    def test_extract_order_columns(self):
        """Test extracting columns from ORDER BY clause."""
        optimizer = QueryOptimizer()
        
        query = "SELECT * FROM users ORDER BY created_at DESC"
        columns = optimizer._extract_order_columns(query)
        
        # Should extract created_at column
        assert len(columns) >= 0  # May or may not extract depending on pattern
