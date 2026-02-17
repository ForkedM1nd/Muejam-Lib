"""
Unit tests for database router

Tests the ReplicationRouter to ensure proper routing of read and write operations.
"""

import pytest
from unittest.mock import Mock, patch
from infrastructure.database_router import ReplicationRouter, PrimaryOnlyRouter


@pytest.mark.django_db
class TestReplicationRouter:
    """Test suite for ReplicationRouter"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.router = ReplicationRouter()
        self.mock_model = Mock()
        self.mock_model.__name__ = 'TestModel'
    
    def test_db_for_read_routes_to_replica_when_configured(self, settings):
        """Test that read operations route to replica when replicas are configured"""
        settings.DATABASE_REPLICAS = [
            {'HOST': 'replica1', 'PORT': '5432', 'WEIGHT': 1.0}
        ]
        result = self.router.db_for_read(self.mock_model)
        assert result == 'replica'
    
    def test_db_for_read_routes_to_primary_when_no_replicas(self, settings):
        """Test that read operations route to primary when no replicas configured"""
        settings.DATABASE_REPLICAS = []
        result = self.router.db_for_read(self.mock_model)
        assert result == 'default'
    
    def test_db_for_read_routes_to_primary_when_use_primary_hint(self, settings):
        """Test that critical reads route to primary when use_primary hint is set"""
        settings.DATABASE_REPLICAS = [
            {'HOST': 'replica1', 'PORT': '5432', 'WEIGHT': 1.0}
        ]
        result = self.router.db_for_read(self.mock_model, use_primary=True)
        assert result == 'default'
    
    def test_db_for_write_always_routes_to_primary(self):
        """Test that write operations always route to primary"""
        result = self.router.db_for_write(self.mock_model)
        assert result == 'default'
    
    def test_allow_relation_allows_same_database_objects(self):
        """Test that relations are allowed between objects in same database"""
        obj1 = Mock()
        obj1._state.db = 'default'
        obj2 = Mock()
        obj2._state.db = 'replica'
        
        result = self.router.allow_relation(obj1, obj2)
        assert result is True
    
    def test_allow_relation_rejects_different_database_objects(self):
        """Test that relations are rejected for objects in different databases"""
        obj1 = Mock()
        obj1._state.db = 'other'
        obj2 = Mock()
        obj2._state.db = 'another'
        
        result = self.router.allow_relation(obj1, obj2)
        assert result is None
    
    def test_allow_migrate_only_on_primary(self):
        """Test that migrations are only allowed on primary database"""
        assert self.router.allow_migrate('default', 'myapp', 'MyModel') is True
        assert self.router.allow_migrate('replica', 'myapp', 'MyModel') is False
        assert self.router.allow_migrate('other', 'myapp', 'MyModel') is False


@pytest.mark.django_db
class TestPrimaryOnlyRouter:
    """Test suite for PrimaryOnlyRouter fallback"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.router = PrimaryOnlyRouter()
        self.mock_model = Mock()
        self.mock_model.__name__ = 'TestModel'
    
    def test_db_for_read_routes_to_primary(self):
        """Test that all reads route to primary"""
        result = self.router.db_for_read(self.mock_model)
        assert result == 'default'
    
    def test_db_for_write_routes_to_primary(self):
        """Test that all writes route to primary"""
        result = self.router.db_for_write(self.mock_model)
        assert result == 'default'
    
    def test_allow_relation_allows_all(self):
        """Test that all relations are allowed"""
        obj1 = Mock()
        obj1._state.db = 'default'
        obj2 = Mock()
        obj2._state.db = 'default'
        
        result = self.router.allow_relation(obj1, obj2)
        assert result is True
    
    def test_allow_migrate_only_on_primary(self):
        """Test that migrations are only allowed on primary"""
        assert self.router.allow_migrate('default', 'myapp', 'MyModel') is True
        assert self.router.allow_migrate('replica', 'myapp', 'MyModel') is False


@pytest.mark.django_db
class TestDatabaseRouterIntegration:
    """Integration tests for database router with Django settings"""
    
    def test_router_configuration_in_settings(self, settings):
        """Test that router is properly configured in Django settings"""
        # This test verifies the settings configuration
        assert hasattr(settings, 'DATABASE_ROUTERS')
        assert 'infrastructure.database_router.ReplicationRouter' in settings.DATABASE_ROUTERS
    
    def test_replica_configuration_in_settings(self, settings):
        """Test that replica configuration exists in settings"""
        assert hasattr(settings, 'DATABASE_REPLICAS')
        assert isinstance(settings.DATABASE_REPLICAS, list)
        
        # Verify replica structure
        if settings.DATABASE_REPLICAS:
            replica = settings.DATABASE_REPLICAS[0]
            assert 'HOST' in replica
            assert 'PORT' in replica
            assert 'WEIGHT' in replica
    
    def test_connection_pool_settings_configured(self, settings):
        """Test that connection pool settings are configured"""
        assert hasattr(settings, 'DB_POOL_MIN_CONNECTIONS')
        assert hasattr(settings, 'DB_POOL_MAX_CONNECTIONS')
        assert hasattr(settings, 'DB_POOL_IDLE_TIMEOUT')
        
        # Verify reasonable values
        assert settings.DB_POOL_MIN_CONNECTIONS >= 10
        assert settings.DB_POOL_MAX_CONNECTIONS >= settings.DB_POOL_MIN_CONNECTIONS
        assert settings.DB_POOL_IDLE_TIMEOUT > 0
    
    def test_workload_isolation_settings_configured(self, settings):
        """Test that workload isolation settings are configured"""
        assert hasattr(settings, 'MAX_REPLICA_LAG')
        assert hasattr(settings, 'REPLICA_LAG_CHECK_INTERVAL')
        
        # Verify reasonable values
        assert settings.MAX_REPLICA_LAG > 0
        assert settings.REPLICA_LAG_CHECK_INTERVAL > 0
    
    def test_high_availability_settings_configured(self, settings):
        """Test that high availability settings are configured"""
        assert hasattr(settings, 'ENABLE_AUTO_FAILOVER')
        assert hasattr(settings, 'FAILOVER_TIMEOUT')
        assert hasattr(settings, 'HEALTH_CHECK_INTERVAL')
        assert hasattr(settings, 'HEALTH_CHECK_TIMEOUT')
        
        # Verify reasonable values
        assert isinstance(settings.ENABLE_AUTO_FAILOVER, bool)
        assert settings.FAILOVER_TIMEOUT > 0
        assert settings.HEALTH_CHECK_INTERVAL > 0
        assert settings.HEALTH_CHECK_TIMEOUT > 0
    
    def test_failover_notification_settings_configured(self, settings):
        """Test that failover notification settings are configured"""
        assert hasattr(settings, 'FAILOVER_NOTIFICATION_CHANNELS')
        assert isinstance(settings.FAILOVER_NOTIFICATION_CHANNELS, dict)
        
        # Verify channel structure
        channels = settings.FAILOVER_NOTIFICATION_CHANNELS
        assert 'email' in channels
        assert 'slack' in channels
        assert 'pagerduty' in channels
        
        # Verify each channel has required fields
        for channel_name, channel_config in channels.items():
            assert 'enabled' in channel_config
            assert isinstance(channel_config['enabled'], bool)
