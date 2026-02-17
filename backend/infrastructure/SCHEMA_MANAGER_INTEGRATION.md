# SchemaManager Integration Guide

## Overview

The `SchemaManager` class provides safe, transactional database schema migration management with automatic rollback capabilities and version history tracking. It integrates with Prisma Migrate to ensure database schema changes are applied reliably.

## Features

- **Transactional Execution**: All migrations run within transactions (Requirement 8.2)
- **Automatic Rollback**: Failed migrations automatically rollback to previous state (Requirement 8.3)
- **Version History**: Complete tracking of all applied migrations (Requirement 8.1)
- **Rollback Script Generation**: Automatic generation of rollback scripts (Requirement 8.5)
- **Validation**: Pre-execution validation to catch issues early
- **Environment Support**: Different handling for production, staging, and development

## Basic Usage

### Initialize SchemaManager

```python
from infrastructure import SchemaManager, Migration

# Initialize with path to Prisma schema
manager = SchemaManager(prisma_schema_path="backend/prisma/schema.prisma")
```

### Apply a Migration

```python
# Create a migration
migration = Migration(
    id="001_add_users_table",
    name="add_users_table",
    sql="""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE INDEX idx_users_email ON users(email);
    """,
    rollback_sql="""
        DROP INDEX IF EXISTS idx_users_email;
        DROP TABLE IF EXISTS users;
    """
)

# Apply the migration
result = await manager.apply_migration(migration, environment="production")

if result.success:
    print(f"Migration {result.migration_id} applied successfully in {result.execution_time:.2f}s")
else:
    print(f"Migration failed: {result.message}")
    if result.error:
        print(f"Error: {result.error}")
```

### Automatic Rollback Script Generation

If you don't provide a rollback script, SchemaManager will generate one automatically:

```python
migration = Migration(
    id="002_add_email_column",
    name="add_email_column",
    sql="ALTER TABLE users ADD COLUMN email VARCHAR(255);"
    # No rollback_sql provided - will be generated automatically
)

result = await manager.apply_migration(migration)
# Rollback script will be: "ALTER TABLE users DROP COLUMN IF EXISTS email;"
```

### Rollback a Migration

```python
# Rollback a previously applied migration
result = await manager.rollback_migration("001_add_users_table")

if result.success:
    print(f"Migration rolled back successfully")
else:
    print(f"Rollback failed: {result.message}")
```

### View Migration History

```python
# Get all applied migrations
history = manager.get_version_history()

for record in history:
    print(f"Migration: {record.migration_id}")
    print(f"  Name: {record.name}")
    print(f"  Applied: {record.applied_at}")
    print(f"  Status: {record.status}")
    print(f"  Rollback: {record.rollback_script[:50]}...")
```

### Validate a Migration

```python
migration = Migration(
    id="003_complex_migration",
    name="complex_migration",
    sql="DROP DATABASE production;"  # Dangerous!
)

validation = await manager.validate_migration(migration)

if not validation.is_valid:
    print("Validation failed:")
    for error in validation.errors:
        print(f"  - {error}")

if validation.warnings:
    print("Warnings:")
    for warning in validation.warnings:
        print(f"  - {warning}")
```

## Supported SQL Operations

### Automatic Rollback Generation

SchemaManager can automatically generate rollback scripts for:

1. **CREATE TABLE**
   ```sql
   CREATE TABLE users (id INT);
   -- Rollback: DROP TABLE IF EXISTS users CASCADE;
   ```

2. **ALTER TABLE ADD COLUMN**
   ```sql
   ALTER TABLE users ADD COLUMN email VARCHAR(255);
   -- Rollback: ALTER TABLE users DROP COLUMN IF EXISTS email;
   ```

3. **CREATE INDEX**
   ```sql
   CREATE INDEX idx_users_email ON users(email);
   -- Rollback: DROP INDEX IF EXISTS idx_users_email;
   ```

### Operations Requiring Manual Rollback

Some operations cannot be automatically rolled back:

- **DROP TABLE**: Cannot restore dropped data
- **DROP COLUMN**: Cannot restore dropped data
- **TRUNCATE**: Cannot restore deleted data

For these operations, SchemaManager will include a warning in the generated rollback script.

## Error Handling

### Migration Failure

When a migration fails, SchemaManager automatically:

1. Catches the exception
2. Executes the rollback script
3. Restores the database to its previous state
4. Returns a detailed error message

```python
result = await manager.apply_migration(failing_migration)

if not result.success:
    print(f"Migration failed: {result.message}")
    print(f"Error details: {result.error}")
    print(f"Execution time: {result.execution_time:.2f}s")
    # Database is automatically rolled back to previous state
```

### Validation Errors

Validation catches common issues before execution:

- Empty SQL
- Invalid migration ID format
- Duplicate migration IDs
- Dangerous operations (with warnings)

```python
validation = await manager.validate_migration(migration)

if not validation.is_valid:
    # Fix issues before applying
    for error in validation.errors:
        print(f"Error: {error}")
```

## Environment-Specific Behavior

### Production

```python
result = await manager.apply_migration(migration, environment="production")
# Uses: prisma migrate deploy
# - No interactive prompts
# - Applies pending migrations
# - Suitable for CI/CD pipelines
```

### Development/Staging

```python
result = await manager.apply_migration(migration, environment="development")
# Uses: prisma migrate dev
# - Creates migration files
# - Applies migrations
# - Updates Prisma Client
```

## Integration with Prisma

SchemaManager integrates with Prisma Migrate:

1. **Migration Files**: Creates migration files in `prisma/migrations/`
2. **Prisma CLI**: Uses `npx prisma migrate` commands
3. **Transaction Support**: Leverages Prisma's built-in transaction handling
4. **Schema Sync**: Keeps Prisma schema in sync with database

## Best Practices

### 1. Always Provide Rollback Scripts for Critical Migrations

```python
# Good: Explicit rollback for complex operations
migration = Migration(
    id="004_critical_change",
    name="critical_change",
    sql="ALTER TABLE users DROP COLUMN legacy_field;",
    rollback_sql="ALTER TABLE users ADD COLUMN legacy_field VARCHAR(255);"
)
```

### 2. Test in Staging First

```python
# Test in staging
staging_result = await manager.apply_migration(migration, environment="staging")

if staging_result.success:
    # Then apply to production
    prod_result = await manager.apply_migration(migration, environment="production")
```

### 3. Use Descriptive Migration IDs

```python
# Good: Clear, sequential, descriptive
migration = Migration(
    id="001_add_users_table",
    name="add_users_table",
    sql="..."
)

# Bad: Unclear, hard to track
migration = Migration(
    id="migration1",
    name="m1",
    sql="..."
)
```

### 4. Keep Migrations Small and Focused

```python
# Good: Single responsibility
migration1 = Migration(
    id="001_add_users_table",
    name="add_users_table",
    sql="CREATE TABLE users (...);"
)

migration2 = Migration(
    id="002_add_posts_table",
    name="add_posts_table",
    sql="CREATE TABLE posts (...);"
)

# Bad: Too many changes in one migration
migration = Migration(
    id="001_everything",
    name="everything",
    sql="CREATE TABLE users (...); CREATE TABLE posts (...); CREATE TABLE comments (...);"
)
```

### 5. Review Generated Rollback Scripts

```python
migration = Migration(
    id="005_complex",
    name="complex",
    sql="..."
)

# Generate and review rollback
rollback = manager.generate_rollback_script(migration)
print(f"Generated rollback:\n{rollback}")

# If satisfactory, use it
migration.rollback_sql = rollback
```

## Monitoring and Logging

SchemaManager logs important events:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('infrastructure.schema_manager')

# Logs include:
# - Migration application start/completion
# - Validation warnings
# - Rollback execution
# - Error details
```

## Example: Complete Migration Workflow

```python
import asyncio
from infrastructure import SchemaManager, Migration

async def apply_user_table_migration():
    # Initialize manager
    manager = SchemaManager()
    
    # Create migration
    migration = Migration(
        id="001_add_users_table",
        name="add_users_table",
        sql="""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
            CREATE INDEX idx_users_email ON users(email);
        """,
        rollback_sql="""
            DROP INDEX IF EXISTS idx_users_email;
            DROP TABLE IF EXISTS users CASCADE;
        """
    )
    
    # Validate first
    validation = await manager.validate_migration(migration)
    if not validation.is_valid:
        print("Validation failed:")
        for error in validation.errors:
            print(f"  - {error}")
        return
    
    if validation.warnings:
        print("Warnings:")
        for warning in validation.warnings:
            print(f"  - {warning}")
    
    # Apply to staging first
    print("Applying to staging...")
    staging_result = await manager.apply_migration(migration, environment="staging")
    
    if not staging_result.success:
        print(f"Staging failed: {staging_result.message}")
        return
    
    print(f"Staging successful in {staging_result.execution_time:.2f}s")
    
    # Apply to production
    print("Applying to production...")
    prod_result = await manager.apply_migration(migration, environment="production")
    
    if prod_result.success:
        print(f"Production migration successful in {prod_result.execution_time:.2f}s")
        
        # View history
        history = manager.get_version_history()
        print(f"\nTotal migrations applied: {len(history)}")
    else:
        print(f"Production migration failed: {prod_result.message}")
        if prod_result.error:
            print(f"Error: {prod_result.error}")

# Run the migration
asyncio.run(apply_user_table_migration())
```

## Requirements Mapping

- **Requirement 8.1**: Version history tracking via `get_version_history()`
- **Requirement 8.2**: Transactional execution via Prisma Migrate integration
- **Requirement 8.3**: Automatic rollback on failure via `_rollback_transaction()`
- **Requirement 8.5**: Rollback script generation via `generate_rollback_script()`

## Troubleshooting

### Migration Fails to Apply

1. Check validation errors
2. Review SQL syntax
3. Ensure database connectivity
4. Check for conflicting migrations

### Rollback Fails

1. Review rollback script
2. Check for data dependencies
3. Manually intervene if necessary
4. Update rollback script for future use

### Duplicate Migration ID

1. Check version history
2. Use unique, sequential IDs
3. Coordinate with team on migration numbering

## Further Reading

- [Prisma Migrate Documentation](https://www.prisma.io/docs/concepts/components/prisma-migrate)
- [PostgreSQL Transaction Documentation](https://www.postgresql.org/docs/current/tutorial-transactions.html)
- Design Document: `.kiro/specs/db-cache-optimization/design.md`
- Requirements Document: `.kiro/specs/db-cache-optimization/requirements.md`
