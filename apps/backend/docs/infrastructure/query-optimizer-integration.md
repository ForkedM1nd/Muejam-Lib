# QueryOptimizer Integration Guide

## Overview

The `QueryOptimizer` class provides comprehensive query analysis, slow query detection, N+1 pattern detection, and index suggestion capabilities for database optimization.

## Features

1. **Query Analysis**: Analyzes execution plans using EXPLAIN ANALYZE
2. **Slow Query Detection**: Automatically detects and logs queries exceeding 100ms threshold
3. **N+1 Pattern Detection**: Identifies N+1 query patterns in request cycles
4. **Index Suggestions**: Recommends indexes based on slow query patterns
5. **Performance Metrics**: Tracks query performance statistics

## Basic Usage

```python
from infrastructure.query_optimizer import QueryOptimizer

# Initialize the optimizer
optimizer = QueryOptimizer(
    slow_query_threshold=100.0,  # milliseconds
    enable_explain_analyze=True,
    max_query_history=1000
)

# Track a query
optimizer.track_query(
    query="SELECT * FROM users WHERE email = ?",
    execution_time=150.0,  # milliseconds
    params={"email": "user@example.com"},
    request_id="req123",
    user_id="user456"
)

# Analyze a query
analysis = optimizer.analyze_query(
    query="SELECT * FROM users WHERE email = ?",
    params={"email": "user@example.com"}
)

print(f"Has index: {analysis.has_index}")
print(f"Is slow: {analysis.is_slow}")
print(f"Suggestions: {analysis.optimization_suggestions}")

# Detect N+1 patterns
patterns = optimizer.detect_n_plus_one(request_id="req123")
for pattern in patterns:
    print(f"N+1 detected: {pattern.count} queries")
    print(f"Recommendation: {pattern.recommendation}")

# Get index suggestions
suggestions = optimizer.suggest_indexes()
for suggestion in suggestions:
    print(f"Suggest index on {suggestion.table_name}.{suggestion.columns}")
    print(f"Reason: {suggestion.reason}")

# Get metrics
metrics = optimizer.get_metrics()
print(f"Total queries: {metrics['total_queries']}")
print(f"Slow query rate: {metrics['slow_query_rate']}%")
```

## Integration with Prisma

To integrate with Prisma query hooks, you need to set up middleware that intercepts queries:

```python
from prisma import Prisma
import time

# Initialize Prisma client and optimizer
prisma = Prisma()
optimizer = QueryOptimizer()

# Set up custom EXPLAIN callback for PostgreSQL
def explain_query(query: str, params: dict):
    """Execute EXPLAIN ANALYZE on PostgreSQL."""
    explain_query = f"EXPLAIN (ANALYZE, FORMAT JSON) {query}"
    result = prisma._execute_raw(explain_query, params)
    return result[0] if result else {}

optimizer.set_explain_callback(explain_query)

# Middleware to track queries
async def query_middleware(params, next):
    start_time = time.time()
    
    # Execute the query
    result = await next(params)
    
    # Calculate execution time
    execution_time = (time.time() - start_time) * 1000  # Convert to ms
    
    # Track the query
    optimizer.track_query(
        query=params.get('query', ''),
        execution_time=execution_time,
        params=params.get('args', {}),
        request_id=get_current_request_id(),  # Your request tracking
        user_id=get_current_user_id()  # Your user tracking
    )
    
    return result

# Register middleware with Prisma
prisma._middleware.append(query_middleware)
```

## Django Integration

For Django applications, you can use database query logging:

```python
from django.db import connection
from django.core.signals import request_started, request_finished
from django.dispatch import receiver
import uuid

# Global optimizer instance
optimizer = QueryOptimizer()

# Track request ID
_request_id = None

@receiver(request_started)
def on_request_started(sender, **kwargs):
    global _request_id
    _request_id = str(uuid.uuid4())

@receiver(request_finished)
def on_request_finished(sender, **kwargs):
    global _request_id
    
    # Detect N+1 patterns for this request
    if _request_id:
        patterns = optimizer.detect_n_plus_one(request_id=_request_id)
        for pattern in patterns:
            logger.warning(f"N+1 pattern detected: {pattern.count} queries")
        
        # Clear request context
        optimizer.clear_request_context(_request_id)
        _request_id = None

# Custom database wrapper to track queries
class QueryTrackingWrapper:
    def __init__(self, cursor):
        self.cursor = cursor
    
    def execute(self, sql, params=None):
        start_time = time.time()
        result = self.cursor.execute(sql, params)
        execution_time = (time.time() - start_time) * 1000
        
        # Track query
        optimizer.track_query(
            query=sql,
            execution_time=execution_time,
            params=params or {},
            request_id=_request_id
        )
        
        return result
```

## Request Context Management

For N+1 detection, track queries within a request context:

```python
# Start of request
request_id = "req123"

# Track queries
optimizer.track_query(
    "SELECT * FROM posts",
    execution_time=10.0,
    request_id=request_id
)

for i in range(10):
    optimizer.track_query(
        f"SELECT * FROM comments WHERE post_id = {i}",
        execution_time=5.0,
        request_id=request_id
    )

# Detect N+1 patterns
patterns = optimizer.detect_n_plus_one(request_id=request_id)

# End of request - clean up
optimizer.clear_request_context(request_id)
```

## Monitoring and Alerting

Set up monitoring for slow queries and N+1 patterns:

```python
import logging

# Configure logging
logger = logging.getLogger('query_optimizer')

# Periodically check metrics
def check_query_health():
    metrics = optimizer.get_metrics()
    
    # Alert on high slow query rate
    if metrics['slow_query_rate'] > 10.0:
        logger.warning(
            f"High slow query rate: {metrics['slow_query_rate']:.2f}%"
        )
    
    # Get index suggestions
    suggestions = optimizer.suggest_indexes()
    if suggestions:
        logger.info(f"Found {len(suggestions)} index suggestions")
        for suggestion in suggestions:
            logger.info(
                f"  - {suggestion.table_name}.{suggestion.columns}: "
                f"{suggestion.reason}"
            )
```

## Configuration Options

```python
optimizer = QueryOptimizer(
    slow_query_threshold=100.0,      # Threshold in milliseconds
    enable_explain_analyze=True,     # Enable execution plan analysis
    max_query_history=1000           # Maximum queries to keep in history
)
```

## Best Practices

1. **Set appropriate thresholds**: Adjust `slow_query_threshold` based on your application's performance requirements
2. **Use request context**: Always provide `request_id` for accurate N+1 detection
3. **Monitor metrics**: Regularly check `get_metrics()` to track query performance trends
4. **Act on suggestions**: Review and implement index suggestions from `suggest_indexes()`
5. **Clean up contexts**: Call `clear_request_context()` after each request to prevent memory leaks
6. **Disable in production**: Consider disabling `enable_explain_analyze` in production to reduce overhead

## Performance Considerations

- The optimizer maintains query history up to `max_query_history` entries
- EXPLAIN ANALYZE adds overhead; consider disabling in high-traffic production environments
- Request contexts are stored in memory; ensure proper cleanup
- Index suggestions are computed on-demand; cache results if needed

## Requirements Validation

The QueryOptimizer satisfies the following requirements:

- **Requirement 1.1**: Analyzes query execution plans for all queries
- **Requirement 1.2**: Logs slow queries exceeding 100ms threshold
- **Requirement 1.3**: Identifies missing indexes based on query patterns
- **Requirement 1.4**: Maintains query performance metrics
- **Requirement 1.5**: Detects N+1 query patterns and recommends batch loading
