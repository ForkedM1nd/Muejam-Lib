"""
Query Optimizer for database query analysis and optimization.

This module implements query performance analysis, slow query detection,
N+1 pattern detection, and index suggestion logic.
"""

import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict
from dataclasses import dataclass

from .models import (
    QueryLog, QueryAnalysis, NPlusOnePattern, IndexSuggestion, QueryType
)


logger = logging.getLogger(__name__)


@dataclass
class QueryContext:
    """Context information for tracking queries in a request cycle."""
    request_id: str
    queries: List[QueryLog]
    start_time: float


class QueryOptimizer:
    """
    Analyze and optimize database queries for performance.
    
    Responsibilities:
    - Analyze query execution plans using EXPLAIN ANALYZE
    - Detect slow queries (execution time > 100ms)
    - Identify N+1 query patterns
    - Suggest indexes based on query patterns
    - Maintain query performance metrics
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
    """
    
    def __init__(
        self,
        slow_query_threshold: float = 100.0,  # milliseconds
        enable_explain_analyze: bool = True,
        max_query_history: int = 1000
    ):
        """
        Initialize the query optimizer.
        
        Args:
            slow_query_threshold: Threshold for slow query detection in milliseconds (default: 100)
            enable_explain_analyze: Whether to run EXPLAIN ANALYZE on queries (default: True)
            max_query_history: Maximum number of queries to keep in history (default: 1000)
        """
        self.slow_query_threshold = slow_query_threshold
        self.enable_explain_analyze = enable_explain_analyze
        self.max_query_history = max_query_history
        
        # Query tracking
        self.query_history: List[QueryLog] = []
        self.slow_queries: List[QueryLog] = []
        
        # Request context tracking for N+1 detection
        self.request_contexts: Dict[str, QueryContext] = {}
        
        # Query pattern tracking for index suggestions
        self.query_patterns: Dict[str, List[QueryLog]] = defaultdict(list)
        
        # Metrics
        self.total_queries = 0
        self.total_slow_queries = 0
        self.total_execution_time = 0.0
        
        # Callbacks for integration (e.g., with Prisma)
        self._explain_callback: Optional[Callable[[str, dict], dict]] = None
    
    def set_explain_callback(self, callback: Callable[[str, dict], dict]) -> None:
        """
        Set custom callback for executing EXPLAIN ANALYZE.
        
        Args:
            callback: Function that takes (query, params) and returns execution plan dict
        """
        self._explain_callback = callback
    
    def analyze_query(self, query: str, params: dict) -> QueryAnalysis:
        """
        Analyze query execution plan and identify optimization opportunities.
        
        This method:
        1. Executes EXPLAIN ANALYZE to get execution plan
        2. Analyzes the plan for performance issues
        3. Identifies missing indexes
        4. Provides optimization suggestions
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            QueryAnalysis object with optimization recommendations
        
        Requirements: 1.1, 1.3, 1.4
        """
        query_id = self._generate_query_id(query)
        
        try:
            # Get execution plan
            execution_plan = self._get_execution_plan(query, params)
            
            # Analyze the plan
            has_index = self._check_index_usage(execution_plan)
            estimated_cost = self._extract_cost(execution_plan, "estimated")
            actual_cost = self._extract_cost(execution_plan, "actual")
            rows_examined = self._extract_rows(execution_plan, "examined")
            rows_returned = self._extract_rows(execution_plan, "returned")
            
            # Generate optimization suggestions
            suggestions = self._generate_suggestions(
                query, execution_plan, has_index, rows_examined, rows_returned
            )
            
            # Determine if query is slow based on actual cost or execution time
            is_slow = actual_cost > self.slow_query_threshold
            
            analysis = QueryAnalysis(
                query_id=query_id,
                has_index=has_index,
                estimated_cost=estimated_cost,
                actual_cost=actual_cost,
                rows_examined=rows_examined,
                rows_returned=rows_returned,
                optimization_suggestions=suggestions,
                is_slow=is_slow
            )
            
            logger.debug(f"Query analysis completed: {query_id}, slow={is_slow}")
            return analysis
            
        except Exception as e:
            logger.error(f"Query analysis failed for {query_id}: {e}", exc_info=True)
            # Return default analysis on error
            return QueryAnalysis(
                query_id=query_id,
                has_index=False,
                estimated_cost=0.0,
                actual_cost=0.0,
                rows_examined=0,
                rows_returned=0,
                optimization_suggestions=[f"Analysis failed: {str(e)}"],
                is_slow=False
            )
    
    def _get_execution_plan(self, query: str, params: dict) -> Dict[str, Any]:
        """
        Execute EXPLAIN ANALYZE to get query execution plan.
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            Execution plan as dictionary
        """
        if not self.enable_explain_analyze:
            return {}
        
        # Use custom callback if provided
        if self._explain_callback:
            return self._explain_callback(query, params)
        
        # Default placeholder implementation
        # In a real implementation, this would execute:
        # EXPLAIN (ANALYZE, FORMAT JSON) <query>
        return {
            "Plan": {
                "Node Type": "Seq Scan",
                "Total Cost": 100.0,
                "Actual Total Time": 50.0,
                "Rows": 100,
                "Plans": []
            }
        }
    
    def _check_index_usage(self, execution_plan: Dict[str, Any]) -> bool:
        """
        Check if the query uses indexes.
        
        Args:
            execution_plan: Execution plan from EXPLAIN ANALYZE
        
        Returns:
            True if query uses indexes, False otherwise
        """
        if not execution_plan:
            return False
        
        plan = execution_plan.get("Plan", {})
        node_type = plan.get("Node Type", "")
        
        # Check for index scan types
        index_scan_types = ["Index Scan", "Index Only Scan", "Bitmap Index Scan"]
        if node_type in index_scan_types:
            return True
        
        # Check nested plans recursively
        for nested_plan in plan.get("Plans", []):
            if self._check_index_usage({"Plan": nested_plan}):
                return True
        
        return False
    
    def _extract_cost(self, execution_plan: Dict[str, Any], cost_type: str) -> float:
        """
        Extract cost from execution plan.
        
        Args:
            execution_plan: Execution plan from EXPLAIN ANALYZE
            cost_type: "estimated" or "actual"
        
        Returns:
            Cost value in milliseconds
        """
        if not execution_plan:
            return 0.0
        
        plan = execution_plan.get("Plan", {})
        
        if cost_type == "estimated":
            return plan.get("Total Cost", 0.0)
        elif cost_type == "actual":
            return plan.get("Actual Total Time", 0.0)
        
        return 0.0
    
    def _extract_rows(self, execution_plan: Dict[str, Any], row_type: str) -> int:
        """
        Extract row counts from execution plan.
        
        Args:
            execution_plan: Execution plan from EXPLAIN ANALYZE
            row_type: "examined" or "returned"
        
        Returns:
            Number of rows
        """
        if not execution_plan:
            return 0
        
        plan = execution_plan.get("Plan", {})
        
        # For PostgreSQL, both examined and returned are in "Rows"
        return plan.get("Rows", 0)
    
    def _generate_suggestions(
        self,
        query: str,
        execution_plan: Dict[str, Any],
        has_index: bool,
        rows_examined: int,
        rows_returned: int
    ) -> List[str]:
        """
        Generate optimization suggestions based on query analysis.
        
        Args:
            query: SQL query string
            execution_plan: Execution plan from EXPLAIN ANALYZE
            has_index: Whether query uses indexes
            rows_examined: Number of rows examined
            rows_returned: Number of rows returned
        
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        # Check for missing indexes
        if not has_index and rows_examined > 100:
            suggestions.append("Consider adding an index to improve query performance")
        
        # Check for full table scans
        plan = execution_plan.get("Plan", {})
        if plan.get("Node Type") == "Seq Scan" and rows_examined > 1000:
            suggestions.append("Query performs a full table scan; consider adding appropriate indexes")
        
        # Check for inefficient row filtering
        if rows_examined > 0 and rows_returned > 0:
            filter_ratio = rows_returned / rows_examined
            if filter_ratio < 0.1 and rows_examined > 100:
                suggestions.append(
                    f"Query examines {rows_examined} rows but returns only {rows_returned}; "
                    "consider adding more selective WHERE conditions or indexes"
                )
        
        # Check for SELECT *
        if re.search(r'\bSELECT\s+\*\s+FROM\b', query, re.IGNORECASE):
            suggestions.append("Avoid SELECT *; specify only needed columns")
        
        # Check for missing LIMIT on large result sets
        if rows_returned > 1000 and not re.search(r'\bLIMIT\b', query, re.IGNORECASE):
            suggestions.append("Consider adding LIMIT clause for large result sets")
        
        return suggestions
    
    def _generate_query_id(self, query: str) -> str:
        """
        Generate a unique ID for a query.
        
        Args:
            query: SQL query string
        
        Returns:
            Query ID string
        """
        # Normalize query by removing extra whitespace and parameters
        normalized = re.sub(r'\s+', ' ', query.strip())
        # Use hash for ID
        return f"q_{hash(normalized) & 0xFFFFFFFF:08x}"
    
    def log_slow_query(self, query: str, execution_time: float, plan: dict) -> None:
        """
        Log slow queries with execution statistics.
        
        Args:
            query: SQL query string
            execution_time: Execution time in milliseconds
            plan: Execution plan dictionary
        
        Requirements: 1.2, 10.3
        """
        query_log = QueryLog(
            query_id=self._generate_query_id(query),
            query_text=query,
            execution_time=execution_time,
            timestamp=datetime.now(),
            execution_plan=plan,
            parameters={},
            query_type=self._detect_query_type(query)
        )
        
        self.slow_queries.append(query_log)
        
        # Maintain max history size
        if len(self.slow_queries) > self.max_query_history:
            self.slow_queries = self.slow_queries[-self.max_query_history:]
        
        logger.warning(
            f"Slow query detected: {query_log.query_id}, "
            f"execution_time={execution_time:.2f}ms, "
            f"query={query[:100]}..."
        )
    
    def track_query(
        self,
        query: str,
        execution_time: float,
        params: dict = None,
        request_id: str = None,
        user_id: str = None
    ) -> None:
        """
        Track a query execution for metrics and pattern analysis.
        
        Args:
            query: SQL query string
            execution_time: Execution time in milliseconds
            params: Query parameters
            request_id: Request ID for N+1 detection
            user_id: User ID who executed the query
        
        Requirements: 1.1, 1.4
        """
        params = params or {}
        
        # Get execution plan if needed
        plan = {}
        if execution_time > self.slow_query_threshold:
            plan = self._get_execution_plan(query, params)
        
        # Create query log
        query_log = QueryLog(
            query_id=self._generate_query_id(query),
            query_text=query,
            execution_time=execution_time,
            timestamp=datetime.now(),
            execution_plan=plan,
            parameters=params,
            user_id=user_id,
            query_type=self._detect_query_type(query)
        )
        
        # Update metrics
        self.total_queries += 1
        self.total_execution_time += execution_time
        
        # Add to history
        self.query_history.append(query_log)
        if len(self.query_history) > self.max_query_history:
            self.query_history = self.query_history[-self.max_query_history:]
        
        # Track slow queries
        if execution_time > self.slow_query_threshold:
            self.total_slow_queries += 1
            self.log_slow_query(query, execution_time, plan)
        
        # Track query patterns for index suggestions
        pattern = self._extract_query_pattern(query)
        self.query_patterns[pattern].append(query_log)
        
        # Track for N+1 detection
        if request_id:
            if request_id not in self.request_contexts:
                self.request_contexts[request_id] = QueryContext(
                    request_id=request_id,
                    queries=[],
                    start_time=time.time()
                )
            self.request_contexts[request_id].queries.append(query_log)
    
    def _detect_query_type(self, query: str) -> QueryType:
        """
        Detect the type of SQL query.
        
        Args:
            query: SQL query string
        
        Returns:
            QueryType enum value
        """
        query_upper = query.strip().upper()
        
        if query_upper.startswith("SELECT"):
            return QueryType.SELECT
        elif query_upper.startswith("INSERT"):
            return QueryType.INSERT
        elif query_upper.startswith("UPDATE"):
            return QueryType.UPDATE
        elif query_upper.startswith("DELETE"):
            return QueryType.DELETE
        else:
            return QueryType.OTHER
    
    def _extract_query_pattern(self, query: str) -> str:
        """
        Extract a normalized pattern from a query for grouping similar queries.
        
        Args:
            query: SQL query string
        
        Returns:
            Normalized query pattern
        """
        # Normalize query by:
        # 1. Converting to uppercase
        # 2. Removing parameter values
        # 3. Normalizing whitespace
        
        pattern = query.upper()
        
        # Replace string literals with placeholder
        pattern = re.sub(r"'[^']*'", "'?'", pattern)
        
        # Replace numeric literals with placeholder
        pattern = re.sub(r'\b\d+\b', '?', pattern)
        
        # Normalize whitespace
        pattern = re.sub(r'\s+', ' ', pattern.strip())
        
        return pattern
    
    def detect_n_plus_one(self, queries: List[str] = None, request_id: str = None) -> List[NPlusOnePattern]:
        """
        Detect N+1 query patterns in a request cycle.
        
        N+1 pattern occurs when:
        1. A parent query fetches N records
        2. For each record, a child query is executed (N queries)
        3. Total: 1 + N queries instead of 1 or 2 queries with JOIN
        
        Args:
            queries: List of query strings to analyze (optional)
            request_id: Request ID to analyze (optional)
        
        Returns:
            List of detected N+1 patterns with recommendations
        
        Requirements: 1.5
        """
        patterns = []
        
        # Get queries to analyze
        if request_id and request_id in self.request_contexts:
            query_logs = self.request_contexts[request_id].queries
            queries_to_analyze = [log.query_text for log in query_logs]
        elif queries:
            queries_to_analyze = queries
        else:
            # Analyze recent queries if no specific context provided
            queries_to_analyze = [log.query_text for log in self.query_history[-100:]]
        
        if len(queries_to_analyze) < 2:
            return patterns
        
        # Group queries by pattern
        query_groups = defaultdict(list)
        for query in queries_to_analyze:
            pattern = self._extract_query_pattern(query)
            query_groups[pattern].append(query)
        
        # Look for repeated patterns (potential N+1)
        for pattern, query_list in query_groups.items():
            if len(query_list) > 5:  # Threshold for N+1 detection
                # Check if these are child queries following a parent query
                if self._is_likely_n_plus_one(pattern, query_list, queries_to_analyze):
                    parent_query = self._find_parent_query(queries_to_analyze, query_list)
                    
                    n_plus_one = NPlusOnePattern(
                        parent_query=parent_query or "Unknown parent query",
                        child_queries=query_list[:3],  # Show first 3 examples
                        count=len(query_list),
                        recommendation=self._generate_n_plus_one_recommendation(pattern)
                    )
                    patterns.append(n_plus_one)
                    
                    logger.warning(
                        f"N+1 query pattern detected: {len(query_list)} similar queries. "
                        f"Pattern: {pattern[:100]}..."
                    )
        
        return patterns
    
    def _is_likely_n_plus_one(self, pattern: str, query_list: List[str], all_queries: List[str]) -> bool:
        """
        Determine if a repeated query pattern is likely an N+1 issue.
        
        Args:
            pattern: Normalized query pattern
            query_list: List of queries matching this pattern
            all_queries: All queries in the request
        
        Returns:
            True if likely N+1 pattern, False otherwise
        """
        # N+1 patterns typically:
        # 1. Are SELECT queries
        # 2. Have WHERE clauses with single ID lookups
        # 3. Appear consecutively or in close proximity
        
        if "SELECT" not in pattern:
            return False
        
        if "WHERE" not in pattern:
            return False
        
        # Check if queries appear in close proximity
        indices = [i for i, q in enumerate(all_queries) if self._extract_query_pattern(q) == pattern]
        if len(indices) < 2:
            return False
        
        # Check if queries are relatively close together
        max_gap = max(indices[i+1] - indices[i] for i in range(len(indices)-1))
        return max_gap <= 10  # Allow up to 10 queries between repeated patterns
    
    def _find_parent_query(self, all_queries: List[str], child_queries: List[str]) -> Optional[str]:
        """
        Find the parent query that likely triggered the N+1 pattern.
        
        Args:
            all_queries: All queries in the request
            child_queries: Child queries in the N+1 pattern
        
        Returns:
            Parent query string, or None if not found
        """
        # Find the first child query
        try:
            first_child_idx = all_queries.index(child_queries[0])
            
            # Look for a SELECT query before the first child
            for i in range(first_child_idx - 1, -1, -1):
                query = all_queries[i]
                if query.strip().upper().startswith("SELECT"):
                    return query
        except (ValueError, IndexError):
            pass
        
        return None
    
    def _generate_n_plus_one_recommendation(self, pattern: str) -> str:
        """
        Generate recommendation for fixing N+1 pattern.
        
        Args:
            pattern: Normalized query pattern
        
        Returns:
            Recommendation string
        """
        recommendations = [
            "Use JOIN to fetch related data in a single query",
            "Implement batch loading with IN clause",
            "Use ORM's select_related() or prefetch_related() for eager loading",
            "Consider using a DataLoader pattern for batching"
        ]
        
        # Provide specific recommendation based on pattern
        if "JOIN" not in pattern:
            return recommendations[0]
        else:
            return recommendations[1]
    
    def suggest_indexes(self, slow_queries: List[QueryLog] = None) -> List[IndexSuggestion]:
        """
        Suggest indexes based on slow query patterns.
        
        Analyzes slow queries to identify:
        1. Tables with frequent sequential scans
        2. Columns used in WHERE clauses
        3. Columns used in JOIN conditions
        4. Columns used in ORDER BY clauses
        
        Args:
            slow_queries: List of slow queries to analyze (optional, uses tracked slow queries if not provided)
        
        Returns:
            List of index suggestions with estimated improvements
        
        Requirements: 1.3
        """
        queries_to_analyze = slow_queries or self.slow_queries
        
        if not queries_to_analyze:
            return []
        
        suggestions = []
        
        # Analyze query patterns
        table_columns = defaultdict(lambda: defaultdict(int))
        
        for query_log in queries_to_analyze:
            query = query_log.query_text
            
            # Extract table names and columns from WHERE clauses
            where_patterns = self._extract_where_columns(query)
            for table, columns in where_patterns.items():
                for column in columns:
                    table_columns[table][column] += 1
            
            # Extract columns from JOIN conditions
            join_patterns = self._extract_join_columns(query)
            for table, columns in join_patterns.items():
                for column in columns:
                    table_columns[table][column] += 1
            
            # Extract columns from ORDER BY
            order_patterns = self._extract_order_columns(query)
            for table, columns in order_patterns.items():
                for column in columns:
                    table_columns[table][column] += 1
        
        # Generate index suggestions for frequently used columns
        for table, columns in table_columns.items():
            # Sort columns by frequency
            sorted_columns = sorted(columns.items(), key=lambda x: x[1], reverse=True)
            
            for column, frequency in sorted_columns:
                if frequency >= 3:  # Threshold for suggesting index
                    # Estimate improvement based on frequency
                    estimated_improvement = min(frequency * 10, 80)  # Cap at 80%
                    
                    suggestion = IndexSuggestion(
                        table_name=table,
                        columns=[column],
                        index_type="btree",
                        reason=f"Column '{column}' used in {frequency} slow queries",
                        estimated_improvement=estimated_improvement
                    )
                    suggestions.append(suggestion)
        
        logger.info(f"Generated {len(suggestions)} index suggestions from {len(queries_to_analyze)} slow queries")
        return suggestions
    
    def _extract_where_columns(self, query: str) -> Dict[str, List[str]]:
        """
        Extract table and column names from WHERE clauses.
        
        Args:
            query: SQL query string
        
        Returns:
            Dictionary mapping table names to lists of column names
        """
        result = defaultdict(list)
        
        # Simple pattern matching for WHERE clauses
        # Format: WHERE table.column = value or WHERE column = value
        where_match = re.search(r'\bWHERE\b(.+?)(?:\bORDER BY\b|\bGROUP BY\b|\bLIMIT\b|$)', query, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)
            
            # Match table.column patterns
            table_column_matches = re.findall(r'\b(\w+)\.(\w+)\s*[=<>]', where_clause, re.IGNORECASE)
            for table, column in table_column_matches:
                result[table].append(column)
            
            # Match standalone column patterns (assume from main table)
            column_matches = re.findall(r'\b(\w+)\s*[=<>]', where_clause, re.IGNORECASE)
            for column in column_matches:
                if column.upper() not in ['AND', 'OR', 'NOT', 'IN', 'IS', 'NULL']:
                    # Try to extract table from FROM clause
                    from_match = re.search(r'\bFROM\s+(\w+)', query, re.IGNORECASE)
                    if from_match:
                        table = from_match.group(1)
                        result[table].append(column)
        
        return result
    
    def _extract_join_columns(self, query: str) -> Dict[str, List[str]]:
        """
        Extract table and column names from JOIN conditions.
        
        Args:
            query: SQL query string
        
        Returns:
            Dictionary mapping table names to lists of column names
        """
        result = defaultdict(list)
        
        # Match JOIN ... ON table.column = table.column patterns
        join_matches = re.findall(
            r'\bJOIN\s+(\w+)\s+(?:\w+\s+)?ON\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)',
            query,
            re.IGNORECASE
        )
        
        for join_table, table1, col1, table2, col2 in join_matches:
            result[table1].append(col1)
            result[table2].append(col2)
        
        return result
    
    def _extract_order_columns(self, query: str) -> Dict[str, List[str]]:
        """
        Extract table and column names from ORDER BY clauses.
        
        Args:
            query: SQL query string
        
        Returns:
            Dictionary mapping table names to lists of column names
        """
        result = defaultdict(list)
        
        # Match ORDER BY patterns
        order_match = re.search(r'\bORDER BY\b(.+?)(?:\bLIMIT\b|$)', query, re.IGNORECASE | re.DOTALL)
        if order_match:
            order_clause = order_match.group(1)
            
            # Match table.column patterns
            table_column_matches = re.findall(r'\b(\w+)\.(\w+)', order_clause, re.IGNORECASE)
            for table, column in table_column_matches:
                result[table].append(column)
        
        return result
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get query performance metrics.
        
        Returns:
            Dictionary with performance metrics
        
        Requirements: 1.4
        """
        avg_execution_time = (
            self.total_execution_time / self.total_queries
            if self.total_queries > 0
            else 0.0
        )
        
        slow_query_rate = (
            self.total_slow_queries / self.total_queries * 100
            if self.total_queries > 0
            else 0.0
        )
        
        return {
            "total_queries": self.total_queries,
            "total_slow_queries": self.total_slow_queries,
            "slow_query_rate": slow_query_rate,
            "avg_execution_time": avg_execution_time,
            "total_execution_time": self.total_execution_time,
            "query_history_size": len(self.query_history),
            "slow_query_history_size": len(self.slow_queries),
            "tracked_patterns": len(self.query_patterns)
        }
    
    def clear_request_context(self, request_id: str) -> None:
        """
        Clear query tracking for a completed request.
        
        Args:
            request_id: Request ID to clear
        """
        if request_id in self.request_contexts:
            del self.request_contexts[request_id]
    
    def reset_metrics(self) -> None:
        """Reset all metrics and query history."""
        self.query_history.clear()
        self.slow_queries.clear()
        self.request_contexts.clear()
        self.query_patterns.clear()
        self.total_queries = 0
        self.total_slow_queries = 0
        self.total_execution_time = 0.0
        logger.info("Query optimizer metrics reset")
    
    def start_request_context(self, request_id: str) -> None:
        """
        Start tracking queries for a request.
        
        Args:
            request_id: Unique identifier for the request
        """
        self.request_contexts[request_id] = QueryContext(
            request_id=request_id,
            queries=[],
            start_time=time.time()
        )
        logger.debug(f"Started query tracking for request {request_id}")
    
    def end_request_context(self, request_id: str) -> Optional[QueryContext]:
        """
        End tracking queries for a request and return the context.
        
        Args:
            request_id: Unique identifier for the request
            
        Returns:
            QueryContext with all tracked queries, or None if not found
        """
        context = self.request_contexts.pop(request_id, None)
        if context:
            duration = time.time() - context.start_time
            logger.debug(
                f"Ended query tracking for request {request_id}: "
                f"{len(context.queries)} queries in {duration:.2f}s"
            )
        return context
