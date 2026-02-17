"""
Unit tests for SchemaManager class.

Tests migration management, transactional execution, automatic rollback,
version history tracking, and rollback script generation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from infrastructure.schema_manager import SchemaManager, Migration
from infrastructure.models import MigrationRecord, MigrationResult, ValidationResult


class TestSchemaManager:
    """Test suite for SchemaManager class."""
    
    def test_initialization(self):
        """SchemaManager should initialize with correct paths."""
        manager = SchemaManager(prisma_schema_path="backend/prisma/schema.prisma")
        
        assert str(manager.prisma_schema_path).endswith("schema.prisma")
        assert str(manager.migrations_dir).endswith("migrations")
        assert manager.version_history == []
    
    @pytest.mark.asyncio
    async def test_apply_migration_success(self):
        """Successful migration should be recorded in version history."""
        manager = SchemaManager()
        
        migration = Migration(
            id="001_add_users_table",
            name="add_users_table",
            sql="CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(255));",
            rollback_sql="DROP TABLE IF EXISTS users;"
        )
        
        # Mock the Prisma execution
        with patch.object(manager, '_execute_prisma_migration', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = MigrationResult(
                success=True,
                migration_id=migration.id,
                message="Migration applied",
                execution_time=0.1
            )
            
            result = await manager.apply_migration(migration, environment="development")
        
        assert result.success is True
        assert result.migration_id == "001_add_users_table"
        assert len(manager.version_history) == 1
        assert manager.version_history[0].migration_id == "001_add_users_table"
        assert manager.version_history[0].status == "applied"
    
    @pytest.mark.asyncio
    async def test_apply_migration_generates_rollback_if_missing(self):
        """Migration without rollback script should have one generated."""
        manager = SchemaManager()
        
        migration = Migration(
            id="002_add_email_column",
            name="add_email_column",
            sql="ALTER TABLE users ADD COLUMN email VARCHAR(255);"
        )
        
        with patch.object(manager, '_execute_prisma_migration', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = MigrationResult(
                success=True,
                migration_id=migration.id,
                message="Migration applied",
                execution_time=0.1
            )
            
            result = await manager.apply_migration(migration)
        
        assert result.success is True
        # Rollback script should have been generated
        assert migration.rollback_sql is not None
        assert "DROP COLUMN" in migration.rollback_sql or "WARNING" in migration.rollback_sql
    
    @pytest.mark.asyncio
    async def test_apply_migration_validation_failure(self):
        """Migration that fails validation should not be applied."""
        manager = SchemaManager()
        
        # Empty SQL should fail validation
        migration = Migration(
            id="003_invalid",
            name="invalid_migration",
            sql=""
        )
        
        result = await manager.apply_migration(migration)
        
        assert result.success is False
        assert "validation failed" in result.message.lower()
        assert len(manager.version_history) == 0
    
    @pytest.mark.asyncio
    async def test_apply_migration_execution_failure_triggers_rollback(self):
        """Failed migration should trigger automatic rollback."""
        manager = SchemaManager()
        
        migration = Migration(
            id="004_failing_migration",
            name="failing_migration",
            sql="CREATE TABLE test (id INT);",
            rollback_sql="DROP TABLE IF EXISTS test;"
        )
        
        with patch.object(manager, '_execute_prisma_migration', new_callable=AsyncMock) as mock_exec, \
             patch.object(manager, '_rollback_transaction', new_callable=AsyncMock) as mock_rollback:
            
            # Simulate execution failure
            mock_exec.side_effect = Exception("Database connection lost")
            
            result = await manager.apply_migration(migration)
        
        assert result.success is False
        assert "Migration failed" in result.message
        assert mock_rollback.called
        assert len(manager.version_history) == 0
    
    @pytest.mark.asyncio
    async def test_rollback_migration_success(self):
        """Successful rollback should update migration status."""
        manager = SchemaManager()
        
        # Add a migration to history
        record = MigrationRecord(
            migration_id="005_test_migration",
            name="test_migration",
            applied_at=datetime.now(),
            rollback_script="DROP TABLE IF EXISTS test;",
            status="applied"
        )
        manager.version_history.append(record)
        
        with patch.object(manager, '_execute_rollback_script', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = MigrationResult(
                success=True,
                migration_id="005_test_migration",
                message="Rollback successful",
                execution_time=0.1
            )
            
            result = await manager.rollback_migration("005_test_migration")
        
        assert result.success is True
        assert record.status == "rolled_back"
    
    @pytest.mark.asyncio
    async def test_rollback_migration_not_found(self):
        """Rollback of non-existent migration should fail gracefully."""
        manager = SchemaManager()
        
        result = await manager.rollback_migration("999_nonexistent")
        
        assert result.success is False
        assert "not found" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_rollback_already_rolled_back_migration(self):
        """Rollback of already rolled back migration should fail."""
        manager = SchemaManager()
        
        # Add a rolled back migration to history
        record = MigrationRecord(
            migration_id="006_rolled_back",
            name="rolled_back",
            applied_at=datetime.now(),
            rollback_script="DROP TABLE IF EXISTS test;",
            status="rolled_back"
        )
        manager.version_history.append(record)
        
        result = await manager.rollback_migration("006_rolled_back")
        
        assert result.success is False
        assert "already rolled back" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_validate_migration_empty_sql(self):
        """Validation should fail for empty SQL."""
        manager = SchemaManager()
        
        migration = Migration(
            id="007_empty",
            name="empty",
            sql=""
        )
        
        result = await manager.validate_migration(migration)
        
        assert result.is_valid is False
        assert any("empty" in error.lower() for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_migration_dangerous_operations(self):
        """Validation should warn about dangerous operations."""
        manager = SchemaManager()
        
        migration = Migration(
            id="008_dangerous",
            name="dangerous",
            sql="DROP DATABASE production; TRUNCATE TABLE users;"
        )
        
        result = await manager.validate_migration(migration)
        
        # Should have warnings about dangerous operations
        assert len(result.warnings) > 0
        assert any("DROP DATABASE" in warning for warning in result.warnings)
        assert any("TRUNCATE" in warning for warning in result.warnings)
    
    @pytest.mark.asyncio
    async def test_validate_migration_invalid_id(self):
        """Validation should fail for invalid migration ID."""
        manager = SchemaManager()
        
        migration = Migration(
            id="invalid id with spaces!",
            name="invalid",
            sql="CREATE TABLE test (id INT);"
        )
        
        result = await manager.validate_migration(migration)
        
        assert result.is_valid is False
        assert any("alphanumeric" in error.lower() for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_migration_duplicate_id(self):
        """Validation should fail for duplicate migration ID."""
        manager = SchemaManager()
        
        # Add existing migration
        existing = MigrationRecord(
            migration_id="009_duplicate",
            name="duplicate",
            applied_at=datetime.now(),
            rollback_script="",
            status="applied"
        )
        manager.version_history.append(existing)
        
        # Try to apply same ID again
        migration = Migration(
            id="009_duplicate",
            name="duplicate",
            sql="CREATE TABLE test (id INT);"
        )
        
        result = await manager.validate_migration(migration)
        
        assert result.is_valid is False
        assert any("already been applied" in error.lower() for error in result.errors)
    
    def test_get_version_history_empty(self):
        """get_version_history should return empty list initially."""
        manager = SchemaManager()
        
        history = manager.get_version_history()
        
        assert history == []
    
    def test_get_version_history_sorted_by_time(self):
        """get_version_history should return migrations sorted by application time."""
        manager = SchemaManager()
        
        # Add migrations in random order
        record1 = MigrationRecord(
            migration_id="001",
            name="first",
            applied_at=datetime(2024, 1, 1, 12, 0, 0),
            rollback_script="",
            status="applied"
        )
        record2 = MigrationRecord(
            migration_id="002",
            name="second",
            applied_at=datetime(2024, 1, 2, 12, 0, 0),
            rollback_script="",
            status="applied"
        )
        record3 = MigrationRecord(
            migration_id="003",
            name="third",
            applied_at=datetime(2024, 1, 3, 12, 0, 0),
            rollback_script="",
            status="applied"
        )
        
        # Add in reverse order
        manager.version_history.extend([record3, record1, record2])
        
        history = manager.get_version_history()
        
        assert len(history) == 3
        assert history[0].migration_id == "001"
        assert history[1].migration_id == "002"
        assert history[2].migration_id == "003"
    
    def test_generate_rollback_script_create_table(self):
        """Rollback script for CREATE TABLE should be DROP TABLE."""
        manager = SchemaManager()
        
        migration = Migration(
            id="010_create_table",
            name="create_table",
            sql="CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(255));"
        )
        
        rollback = manager.generate_rollback_script(migration)
        
        assert "DROP TABLE" in rollback
        assert "users" in rollback
    
    def test_generate_rollback_script_add_column(self):
        """Rollback script for ADD COLUMN should be DROP COLUMN."""
        manager = SchemaManager()
        
        migration = Migration(
            id="011_add_column",
            name="add_column",
            sql="ALTER TABLE users ADD COLUMN email VARCHAR(255);"
        )
        
        rollback = manager.generate_rollback_script(migration)
        
        assert "DROP COLUMN" in rollback
        assert "email" in rollback
    
    def test_generate_rollback_script_create_index(self):
        """Rollback script for CREATE INDEX should be DROP INDEX."""
        manager = SchemaManager()
        
        migration = Migration(
            id="012_create_index",
            name="create_index",
            sql="CREATE INDEX idx_users_email ON users(email);"
        )
        
        rollback = manager.generate_rollback_script(migration)
        
        assert "DROP INDEX" in rollback
        assert "idx_users_email" in rollback
    
    def test_generate_rollback_script_drop_operations_warning(self):
        """Rollback script for DROP operations should include warning."""
        manager = SchemaManager()
        
        migration = Migration(
            id="013_drop_column",
            name="drop_column",
            sql="ALTER TABLE users DROP COLUMN email;"
        )
        
        rollback = manager.generate_rollback_script(migration)
        
        assert "WARNING" in rollback
        assert "Manual intervention" in rollback or "manual rollback" in rollback.lower()
    
    def test_generate_rollback_script_complex_migration(self):
        """Rollback script for complex migration should handle multiple operations."""
        manager = SchemaManager()
        
        migration = Migration(
            id="014_complex",
            name="complex",
            sql="""
                CREATE TABLE posts (id SERIAL PRIMARY KEY);
                CREATE INDEX idx_posts_id ON posts(id);
                ALTER TABLE users ADD COLUMN post_count INT DEFAULT 0;
            """
        )
        
        rollback = manager.generate_rollback_script(migration)
        
        # Should contain rollback for all operations
        assert "DROP TABLE" in rollback
        assert "posts" in rollback
        assert "DROP INDEX" in rollback
        assert "idx_posts_id" in rollback
        assert "DROP COLUMN" in rollback
        assert "post_count" in rollback
    
    def test_generate_rollback_script_no_recognizable_operations(self):
        """Rollback script for unrecognized operations should include manual note."""
        manager = SchemaManager()
        
        migration = Migration(
            id="015_custom",
            name="custom",
            sql="SELECT * FROM users;"  # Not a DDL operation
        )
        
        rollback = manager.generate_rollback_script(migration)
        
        assert "No automatic rollback" in rollback or "Manual" in rollback


class TestSchemaManagerEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_apply_migration_with_exception_during_rollback(self):
        """Failed migration with failed rollback should report both errors."""
        manager = SchemaManager()
        
        migration = Migration(
            id="016_double_failure",
            name="double_failure",
            sql="CREATE TABLE test (id INT);",
            rollback_sql="DROP TABLE IF EXISTS test;"
        )
        
        with patch.object(manager, '_execute_prisma_migration', new_callable=AsyncMock) as mock_exec, \
             patch.object(manager, '_rollback_transaction', new_callable=AsyncMock) as mock_rollback:
            
            mock_exec.side_effect = Exception("Migration failed")
            mock_rollback.side_effect = Exception("Rollback failed")
            
            result = await manager.apply_migration(migration)
        
        assert result.success is False
        assert "Migration failed" in result.message
        assert "Rollback also failed" in result.message or "Rollback failed" in result.message
    
    @pytest.mark.asyncio
    async def test_validate_migration_with_exception(self):
        """Validation exception should be caught and reported."""
        manager = SchemaManager()
        
        migration = Migration(
            id="017_exception",
            name="exception",
            sql="CREATE TABLE test (id INT);"
        )
        
        # Patch to raise exception during validation
        with patch('re.search', side_effect=Exception("Regex error")):
            result = await manager.validate_migration(migration)
        
        assert result.is_valid is False
        assert any("exception" in error.lower() for error in result.errors)
    
    def test_generate_rollback_script_with_exception(self):
        """Exception during rollback generation should return error message."""
        manager = SchemaManager()
        
        migration = Migration(
            id="018_exception",
            name="exception",
            sql="CREATE TABLE test (id INT);"
        )
        
        # Patch to raise exception
        with patch('re.finditer', side_effect=Exception("Regex error")):
            rollback = manager.generate_rollback_script(migration)
        
        assert "Error generating rollback" in rollback
        assert "Manual rollback required" in rollback
    
    @pytest.mark.asyncio
    async def test_multiple_migrations_in_sequence(self):
        """Multiple migrations should be tracked correctly in history."""
        manager = SchemaManager()
        
        migrations = [
            Migration(id=f"0{i}_migration", name=f"migration_{i}", 
                     sql=f"CREATE TABLE table_{i} (id INT);")
            for i in range(1, 4)
        ]
        
        with patch.object(manager, '_execute_prisma_migration', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = MigrationResult(
                success=True,
                migration_id="",
                message="Success",
                execution_time=0.1
            )
            
            for migration in migrations:
                result = await manager.apply_migration(migration)
                assert result.success is True
        
        assert len(manager.version_history) == 3
        history = manager.get_version_history()
        assert [r.migration_id for r in history] == ["01_migration", "02_migration", "03_migration"]
    
    @pytest.mark.asyncio
    async def test_rollback_migration_with_execution_failure(self):
        """Rollback execution failure should be reported."""
        manager = SchemaManager()
        
        record = MigrationRecord(
            migration_id="019_rollback_fail",
            name="rollback_fail",
            applied_at=datetime.now(),
            rollback_script="DROP TABLE test;",
            status="applied"
        )
        manager.version_history.append(record)
        
        with patch.object(manager, '_execute_rollback_script', new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = Exception("Rollback execution failed")
            
            result = await manager.rollback_migration("019_rollback_fail")
        
        assert result.success is False
        assert "Rollback failed" in result.message
        # Status should not have changed
        assert record.status == "applied"
