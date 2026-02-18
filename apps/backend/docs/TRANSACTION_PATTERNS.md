# Transaction Management Patterns

## Overview

This document describes transaction management patterns used in the application to ensure data consistency and prevent partial updates.

## Why Transaction Management?

Without proper transaction management, multi-step operations can fail partway through, leaving the database in an inconsistent state. For example:

- **Story Creation**: If a story is created but chapter creation fails, we end up with an orphaned story record
- **User Blocking**: If follow relationships are removed but block creation fails, users remain connected
- **Whisper Creation**: If a whisper is created but NSFW flag creation fails, content moderation is incomplete

## Decorators

### `@atomic_api_view` (Django ORM)

Use this decorator for views that perform multiple Django ORM operations that should be atomic.

```python
from apps.core.decorators import atomic_api_view
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
@atomic_api_view
def create_story_with_chapters(request):
    """
    Create a story with multiple chapters atomically.
    
    If any chapter creation fails, the entire operation (including story creation)
    will be rolled back.
    """
    # Create story
    story = Story.objects.create(
        title=request.data['title'],
        author_id=request.user_profile.id
    )
    
    # Create chapters
    for chapter_data in request.data.get('chapters', []):
        Chapter.objects.create(
            story=story,
            title=chapter_data['title'],
            content=chapter_data['content']
        )
    
    return Response({'story_id': story.id}, status=201)
```

**Key Features:**
- Wraps the entire view in `transaction.atomic()`
- Automatically rolls back on any exception
- Logs transaction failures with context
- Re-raises exceptions for proper error handling

### `@atomic_prisma_view` (Prisma)

Use this decorator for views that perform multiple Prisma operations that should be atomic.

```python
from apps.core.decorators import atomic_prisma_view
from rest_framework.decorators import api_view
from rest_framework.response import Response
from prisma import Prisma

@api_view(['POST'])
@atomic_prisma_view
def block_user_view(request, user_id):
    """
    Block a user and remove follow relationships atomically.
    
    If block creation fails, follow relationships will not be removed.
    """
    db = Prisma()
    db.connect()
    
    try:
        # Remove follow relationships (both directions)
        db.follow.delete_many(
            where={
                'OR': [
                    {'follower_id': request.user_profile.id, 'following_id': user_id},
                    {'follower_id': user_id, 'following_id': request.user_profile.id}
                ]
            }
        )
        
        # Create block
        block = db.block.create(
            data={
                'blocker_id': request.user_profile.id,
                'blocked_id': user_id
            }
        )
        
        return Response({'blocked': user_id}, status=201)
    finally:
        db.disconnect()
```

**Key Features:**
- Logs Prisma transaction failures with context
- Prisma handles transactions internally when using the same connection
- Re-raises exceptions for proper error handling

## Common Patterns

### Pattern 1: Create Parent with Children

**Use Case**: Creating a story with chapters, creating a whisper with NSFW flags

**Implementation**:
```python
@api_view(['POST'])
@atomic_api_view
def create_parent_with_children(request):
    # Create parent
    parent = Parent.objects.create(...)
    
    # Create children
    for child_data in request.data.get('children', []):
        Child.objects.create(parent=parent, ...)
    
    return Response({'parent_id': parent.id})
```

**Benefits**:
- If any child creation fails, parent is not created
- No orphaned parent records
- Data consistency guaranteed

### Pattern 2: Update with Cascade

**Use Case**: Updating a story and cascading updates to chapters

**Implementation**:
```python
@api_view(['PUT'])
@atomic_api_view
def update_with_cascade(request, parent_id):
    # Update parent
    parent = Parent.objects.get(id=parent_id)
    parent.title = request.data['title']
    parent.save()
    
    # Cascade update to children
    parent.children.all().update(updated_at=timezone.now())
    
    return Response({'updated': parent_id})
```

**Benefits**:
- Parent and children updated together
- No partial updates
- Consistent timestamps

### Pattern 3: Delete with Cleanup

**Use Case**: Blocking a user and removing follow relationships

**Implementation**:
```python
@api_view(['POST'])
@atomic_prisma_view
def delete_with_cleanup(request, object_id):
    db = Prisma()
    db.connect()
    
    try:
        # Clean up related data
        db.related.delete_many(where={'parent_id': object_id})
        
        # Delete main object
        db.parent.delete(where={'id': object_id})
        
        return Response(status=204)
    finally:
        db.disconnect()
```

**Benefits**:
- Related data cleaned up atomically
- No orphaned relationships
- Data integrity maintained

### Pattern 4: Multi-Step Validation and Creation

**Use Case**: Creating content with moderation checks and NSFW flags

**Implementation**:
```python
@api_view(['POST'])
@atomic_prisma_view
def create_with_moderation(request):
    db = Prisma()
    db.connect()
    
    try:
        # Create content
        content = db.content.create(data={...})
        
        # Run moderation checks
        if needs_nsfw_flag:
            db.nsfw_flag.create(data={'content_id': content.id, ...})
        
        if needs_report:
            db.report.create(data={'content_id': content.id, ...})
        
        return Response({'content_id': content.id})
    finally:
        db.disconnect()
```

**Benefits**:
- Content and moderation flags created together
- If moderation flag creation fails, content is not created
- Consistent moderation state

## Testing Transaction Rollback

### Unit Tests

Test that transactions roll back on errors:

```python
def test_transaction_rollback():
    @atomic_api_view
    def failing_view(request):
        Parent.objects.create(name='Test')
        raise ValueError("Simulated failure")
    
    request = RequestFactory().post('/test')
    
    with pytest.raises(ValueError):
        failing_view(request)
    
    # Verify parent was not created
    assert Parent.objects.count() == 0
```

### Integration Tests

Test concurrent operations:

```python
def test_concurrent_operations():
    # Create two threads that try to create the same resource
    # Verify that only one succeeds and the other gets a proper error
    pass
```

## Best Practices

### 1. Use Transactions for Multi-Step Operations

**Always** use transaction decorators when:
- Creating a parent with children
- Updating multiple related objects
- Deleting with cleanup
- Creating with validation/moderation

### 2. Keep Transactions Short

Minimize the work done inside transactions:
- ✅ Database operations
- ❌ External API calls
- ❌ File I/O
- ❌ Long computations

### 3. Handle Exceptions Properly

Let exceptions propagate to trigger rollback:

```python
@atomic_api_view
def my_view(request):
    try:
        # Database operations
        obj = Model.objects.create(...)
        return Response({'id': obj.id})
    except ValidationError as e:
        # Let it propagate to trigger rollback
        raise
```

### 4. Use Single Database Connection

For Prisma, use a single connection for all operations:

```python
@atomic_prisma_view
def my_view(request):
    db = Prisma()
    db.connect()
    try:
        # All operations use the same db connection
        db.model1.create(...)
        db.model2.create(...)
    finally:
        db.disconnect()
```

### 5. Log Transaction Failures

The decorators automatically log failures, but you can add custom logging:

```python
@atomic_api_view
def my_view(request):
    try:
        # Operations
        pass
    except Exception as e:
        logger.error(f"Custom error context: {e}")
        raise
```

## Monitoring

### Metrics to Track

1. **Transaction Failure Rate**: Percentage of transactions that fail
2. **Rollback Frequency**: How often rollbacks occur
3. **Transaction Duration**: Time spent in transactions
4. **Deadlock Frequency**: How often deadlocks occur

### Logging

Transaction failures are automatically logged with:
- View name
- User ID
- Request path
- Request method
- Exception details
- Stack trace

Example log entry:
```
ERROR Transaction failed in create_story_with_chapters: Chapter creation failed
Extra: {
    'view': 'create_story_with_chapters',
    'user': 'user123',
    'path': '/v1/stories',
    'method': 'POST'
}
```

## Troubleshooting

### Issue: Deadlocks

**Symptom**: Transactions timeout or fail with deadlock errors

**Solution**:
- Ensure operations access tables in consistent order
- Keep transactions short
- Use appropriate isolation levels

### Issue: Partial Updates

**Symptom**: Some operations succeed while others fail

**Solution**:
- Verify decorator is applied to the view
- Check that all operations use the same database connection
- Ensure exceptions are not caught and suppressed

### Issue: Performance Degradation

**Symptom**: Slow response times with transactions

**Solution**:
- Move non-database operations outside transactions
- Optimize database queries
- Use appropriate indexes
- Consider breaking into smaller transactions

## Migration Guide

### Converting Existing Views

1. **Identify multi-step operations**:
   - Look for multiple `create()`, `update()`, or `delete()` calls
   - Look for operations that should succeed or fail together

2. **Add decorator**:
   ```python
   # Before
   @api_view(['POST'])
   def my_view(request):
       ...
   
   # After
   @api_view(['POST'])
   @atomic_api_view  # or @atomic_prisma_view
   def my_view(request):
       ...
   ```

3. **Test rollback behavior**:
   - Write tests that simulate failures
   - Verify data consistency

4. **Monitor in production**:
   - Watch for transaction failures
   - Monitor rollback frequency
   - Check for performance impact

## Examples from Codebase

### Example 1: Block User (social/views.py)

```python
async def block_user(blocker_id: str, blocked_id: str):
    """
    Create a block relationship and remove any follow relationships.
    
    This is an atomic operation - if block creation fails, follow relationships
    are not removed.
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Remove follow relationships (both directions)
        await db.follow.delete_many(
            where={
                'OR': [
                    {'follower_id': blocker_id, 'following_id': blocked_id},
                    {'follower_id': blocked_id, 'following_id': blocker_id}
                ]
            }
        )
        
        # Create block relationship
        block = await db.block.create(
            data={
                'blocker_id': blocker_id,
                'blocked_id': blocked_id
            }
        )
        
        await db.disconnect()
        return block
        
    except Exception as e:
        await db.disconnect()
        raise e
```

### Example 2: Create Whisper with Moderation (whispers/views.py)

```python
def _create_whisper(request):
    """
    Create a whisper with content filtering and NSFW flags.
    
    This should be atomic - if NSFW flag creation fails, whisper should not be created.
    """
    db = Prisma()
    db.connect()
    
    try:
        # Create whisper
        whisper = db.whisper.create(data={...})
        
        # Create NSFW flag if needed
        if mark_as_nsfw:
            nsfw_service.mark_content_as_nsfw(
                content_type='WHISPER',
                content_id=whisper.id,
                ...
            )
        
        # Create report if needed
        if needs_report:
            filter_integration.handle_auto_actions(
                content_type='whisper',
                content_id=whisper.id,
                ...
            )
        
        db.disconnect()
        return Response({'data': whisper})
        
    except Exception as e:
        db.disconnect()
        raise
```

## Conclusion

Transaction management is critical for data consistency. Always use the appropriate decorator for multi-step operations, test rollback behavior, and monitor transaction failures in production.
