"""
Unit tests for LoadBalancer class.

Tests weighted round-robin distribution, weight adjustment, and fallback behavior.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from infrastructure.load_balancer import LoadBalancer
from infrastructure.health_monitor import HealthMonitor
from infrastructure.models import ReplicaInfo, HealthStatus


@pytest.fixture
def health_monitor():
    """Create a mock HealthMonitor for testing."""
    monitor = MagicMock(spec=HealthMonitor)
    
    # Default: all instances are healthy
    def mock_check_health(instance):
        return HealthStatus(
            instance=instance,
            is_healthy=True,
            cpu_percent=50.0,
            memory_percent=60.0,
            disk_percent=70.0,
            replication_lag=1.0,
            last_check=datetime.now()
        )
    
    monitor.check_health = mock_check_health
    return monitor


@pytest.fixture
def load_balancer(health_monitor):
    """Create a LoadBalancer instance for testing."""
    return LoadBalancer(
        primary_instance="primary:5432",
        health_monitor=health_monitor,
        cpu_threshold=80.0,
        weight_adjustment_factor=0.5
    )


@pytest.fixture
def replica1():
    """Create a test replica."""
    return ReplicaInfo(
        host="replica1:5432",
        port=5432,
        weight=1.0,
        is_healthy=True,
        cpu_utilization=50.0,
        avg_response_time=10.0,
        replication_lag=1.0
    )


@pytest.fixture
def replica2():
    """Create a test replica."""
    return ReplicaInfo(
        host="replica2:5432",
        port=5432,
        weight=1.0,
        is_healthy=True,
        cpu_utilization=60.0,
        avg_response_time=15.0,
        replication_lag=1.5
    )


@pytest.fixture
def replica3():
    """Create a test replica."""
    return ReplicaInfo(
        host="replica3:5432",
        port=5432,
        weight=1.0,
        is_healthy=True,
        cpu_utilization=40.0,
        avg_response_time=8.0,
        replication_lag=0.5
    )


class TestLoadBalancerInitialization:
    """Test LoadBalancer initialization."""
    
    def test_initialization(self, load_balancer):
        """Test that LoadBalancer initializes correctly."""
        assert load_balancer.primary_instance == "primary:5432"
        assert load_balancer.cpu_threshold == 80.0
        assert load_balancer.weight_adjustment_factor == 0.5
        assert len(load_balancer.replicas) == 0
        assert load_balancer._current_index == 0
    
    def test_add_replica(self, load_balancer, replica1):
        """Test adding a replica to the load balancer."""
        load_balancer.add_replica(replica1)
        
        assert "replica1:5432" in load_balancer.replicas
        assert load_balancer.replicas["replica1:5432"].host == "replica1:5432"
        assert "replica1:5432" in load_balancer._response_times
    
    def test_remove_replica(self, load_balancer, replica1):
        """Test removing a replica from the load balancer."""
        load_balancer.add_replica(replica1)
        load_balancer.remove_replica("replica1:5432")
        
        assert "replica1:5432" not in load_balancer.replicas
        assert "replica1:5432" not in load_balancer._response_times


class TestReplicaSelection:
    """Test replica selection logic."""
    
    def test_select_replica_with_single_replica(self, load_balancer, replica1):
        """Test selecting replica when only one is available."""
        load_balancer.add_replica(replica1)
        
        selected = load_balancer.select_replica()
        assert selected == "replica1:5432"
    
    def test_select_replica_round_robin(self, load_balancer, replica1, replica2, replica3):
        """Test round-robin distribution across replicas."""
        load_balancer.add_replica(replica1)
        load_balancer.add_replica(replica2)
        load_balancer.add_replica(replica3)
        
        # Select multiple times and track distribution
        selections = [load_balancer.select_replica() for _ in range(30)]
        
        # All replicas should be selected
        assert "replica1:5432" in selections
        assert "replica2:5432" in selections
        assert "replica3:5432" in selections
        
        # Distribution should be relatively even (within 50% of expected)
        count1 = selections.count("replica1:5432")
        count2 = selections.count("replica2:5432")
        count3 = selections.count("replica3:5432")
        
        expected = 10  # 30 selections / 3 replicas
        assert 5 <= count1 <= 15
        assert 5 <= count2 <= 15
        assert 5 <= count3 <= 15
    
    def test_select_replica_fallback_to_primary_when_no_replicas(self, load_balancer):
        """Test fallback to primary when no replicas are available."""
        selected = load_balancer.select_replica()
        assert selected == "primary:5432"
    
    def test_select_replica_fallback_to_primary_when_all_unhealthy(
        self, load_balancer, replica1, replica2, health_monitor
    ):
        """Test fallback to primary when all replicas are unhealthy."""
        # Add replicas
        load_balancer.add_replica(replica1)
        load_balancer.add_replica(replica2)
        
        # Mock health monitor to return unhealthy status
        def mock_unhealthy_check(instance):
            return HealthStatus(
                instance=instance,
                is_healthy=False,
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                replication_lag=None,
                last_check=datetime.now(),
                error_message="Connection failed"
            )
        
        health_monitor.check_health = mock_unhealthy_check
        
        selected = load_balancer.select_replica()
        assert selected == "primary:5432"
    
    def test_select_replica_skips_unhealthy_replicas(
        self, load_balancer, replica1, replica2, replica3, health_monitor
    ):
        """Test that unhealthy replicas are skipped."""
        load_balancer.add_replica(replica1)
        load_balancer.add_replica(replica2)
        load_balancer.add_replica(replica3)
        
        # Mock health monitor: replica2 is unhealthy
        def mock_check_health(instance):
            is_healthy = instance != "replica2:5432"
            return HealthStatus(
                instance=instance,
                is_healthy=is_healthy,
                cpu_percent=50.0,
                memory_percent=60.0,
                disk_percent=70.0,
                replication_lag=1.0,
                last_check=datetime.now()
            )
        
        health_monitor.check_health = mock_check_health
        
        # Select multiple times
        selections = [load_balancer.select_replica() for _ in range(20)]
        
        # replica2 should never be selected
        assert "replica2:5432" not in selections
        assert "replica1:5432" in selections
        assert "replica3:5432" in selections


class TestWeightAdjustment:
    """Test replica weight adjustment."""
    
    def test_update_replica_weight_normal_conditions(self, load_balancer, replica1):
        """Test weight update under normal conditions."""
        load_balancer.add_replica(replica1)
        
        # Update with normal metrics
        load_balancer.update_replica_weight("replica1:5432", cpu_util=50.0, response_time=10.0)
        
        # Weight should be updated
        assert load_balancer.replicas["replica1:5432"].cpu_utilization == 50.0
        assert load_balancer.replicas["replica1:5432"].avg_response_time == 10.0
    
    def test_update_replica_weight_high_cpu(self, load_balancer, replica1):
        """Test weight reduction when CPU is high."""
        load_balancer.add_replica(replica1)
        
        # Update with high CPU
        load_balancer.update_replica_weight("replica1:5432", cpu_util=85.0, response_time=10.0)
        
        # Weight should be reduced (base 1.0 * 0.5 = 0.5)
        replica = load_balancer.replicas["replica1:5432"]
        assert replica.cpu_utilization == 85.0
        assert replica.weight < 1.0  # Should be reduced
    
    def test_update_replica_weight_response_time_adjustment(
        self, load_balancer, replica1, replica2
    ):
        """Test weight adjustment based on response time."""
        load_balancer.add_replica(replica1)
        load_balancer.add_replica(replica2)
        
        # Update replica1 with fast response time
        load_balancer.update_replica_weight("replica1:5432", cpu_util=50.0, response_time=5.0)
        
        # Update replica2 with slow response time
        load_balancer.update_replica_weight("replica2:5432", cpu_util=50.0, response_time=20.0)
        
        # Faster replica should have higher weight
        weight1 = load_balancer.replicas["replica1:5432"].weight
        weight2 = load_balancer.replicas["replica2:5432"].weight
        assert weight1 > weight2
    
    def test_update_replica_weight_unknown_replica(self, load_balancer):
        """Test updating weight for unknown replica."""
        # Should not raise exception
        load_balancer.update_replica_weight("unknown:5432", cpu_util=50.0, response_time=10.0)
    
    def test_update_replica_weight_bounds(self, load_balancer, replica1):
        """Test that weight stays within reasonable bounds."""
        load_balancer.add_replica(replica1)
        
        # Update with extreme values
        load_balancer.update_replica_weight("replica1:5432", cpu_util=100.0, response_time=1000.0)
        
        # Weight should be clamped to reasonable range
        weight = load_balancer.replicas["replica1:5432"].weight
        assert 0.1 <= weight <= 10.0


class TestWeightedDistribution:
    """Test weighted round-robin distribution."""
    
    def test_weighted_distribution_favors_higher_weight(
        self, load_balancer, replica1, replica2
    ):
        """Test that replicas with higher weight are selected more often."""
        load_balancer.add_replica(replica1)
        load_balancer.add_replica(replica2)
        
        # Give replica1 higher weight
        load_balancer.replicas["replica1:5432"].weight = 2.0
        load_balancer.replicas["replica2:5432"].weight = 1.0
        load_balancer._rebuild_weighted_list()
        
        # Select many times
        selections = [load_balancer.select_replica() for _ in range(300)]
        
        count1 = selections.count("replica1:5432")
        count2 = selections.count("replica2:5432")
        
        # replica1 should be selected approximately twice as often
        # Allow for some variance (ratio between 1.5 and 2.5)
        ratio = count1 / count2 if count2 > 0 else 0
        assert 1.5 <= ratio <= 2.5
    
    def test_weighted_distribution_with_cpu_threshold(
        self, load_balancer, replica1, replica2
    ):
        """Test that high CPU reduces selection frequency."""
        load_balancer.add_replica(replica1)
        load_balancer.add_replica(replica2)
        
        # replica1 has high CPU, replica2 is normal
        load_balancer.update_replica_weight("replica1:5432", cpu_util=85.0, response_time=10.0)
        load_balancer.update_replica_weight("replica2:5432", cpu_util=50.0, response_time=10.0)
        
        # Select many times
        selections = [load_balancer.select_replica() for _ in range(100)]
        
        count1 = selections.count("replica1:5432")
        count2 = selections.count("replica2:5432")
        
        # replica2 should be selected more often due to lower CPU
        assert count2 > count1


class TestResponseTimeTracking:
    """Test response time tracking."""
    
    def test_record_response_time(self, load_balancer, replica1):
        """Test recording response times."""
        load_balancer.add_replica(replica1)
        
        # Record some response times
        load_balancer.record_response_time("replica1:5432", 10.0)
        load_balancer.record_response_time("replica1:5432", 12.0)
        load_balancer.record_response_time("replica1:5432", 8.0)
        
        # Average should be updated
        avg_rt = load_balancer.replicas["replica1:5432"].avg_response_time
        assert avg_rt == pytest.approx(10.0, rel=0.1)
    
    def test_record_response_time_window_limit(self, load_balancer, replica1):
        """Test that response time window is limited."""
        load_balancer.add_replica(replica1)
        
        # Record more than window size
        for i in range(150):
            load_balancer.record_response_time("replica1:5432", float(i))
        
        # Should only keep last 100
        assert len(load_balancer._response_times["replica1:5432"]) == 100
    
    def test_record_response_time_unknown_replica(self, load_balancer):
        """Test recording response time for unknown replica."""
        # Should not raise exception
        load_balancer.record_response_time("unknown:5432", 10.0)


class TestHealthStatusIntegration:
    """Test integration with HealthMonitor."""
    
    def test_mark_unhealthy(self, load_balancer, replica1):
        """Test marking a replica as unhealthy."""
        load_balancer.add_replica(replica1)
        
        load_balancer.mark_unhealthy("replica1:5432")
        
        assert not load_balancer.replicas["replica1:5432"].is_healthy
    
    def test_mark_healthy(self, load_balancer, replica1):
        """Test marking a replica as healthy."""
        load_balancer.add_replica(replica1)
        
        # First mark as unhealthy
        load_balancer.mark_unhealthy("replica1:5432")
        assert not load_balancer.replicas["replica1:5432"].is_healthy
        
        # Then mark as healthy
        load_balancer.mark_healthy("replica1:5432")
        assert load_balancer.replicas["replica1:5432"].is_healthy
    
    def test_update_replica_health_from_monitor(
        self, load_balancer, replica1, health_monitor
    ):
        """Test updating replica health from health monitor."""
        load_balancer.add_replica(replica1)
        
        # Mock health monitor to return unhealthy status
        def mock_check_health(instance):
            return HealthStatus(
                instance=instance,
                is_healthy=False,
                cpu_percent=90.0,
                memory_percent=80.0,
                disk_percent=70.0,
                replication_lag=5.0,
                last_check=datetime.now(),
                error_message="High load"
            )
        
        health_monitor.check_health = mock_check_health
        
        # Select replica (triggers health update)
        load_balancer.select_replica()
        
        # Replica should be marked unhealthy
        replica = load_balancer.replicas["replica1:5432"]
        assert not replica.is_healthy
        assert replica.cpu_utilization == 90.0


class TestUtilityMethods:
    """Test utility methods."""
    
    def test_get_replica_stats(self, load_balancer, replica1, replica2):
        """Test getting replica statistics."""
        load_balancer.add_replica(replica1)
        load_balancer.add_replica(replica2)
        
        stats = load_balancer.get_replica_stats()
        
        assert len(stats) == 2
        assert "replica1:5432" in stats
        assert "replica2:5432" in stats
    
    def test_get_healthy_replica_count(self, load_balancer, replica1, replica2, replica3):
        """Test getting count of healthy replicas."""
        load_balancer.add_replica(replica1)
        load_balancer.add_replica(replica2)
        load_balancer.add_replica(replica3)
        
        # All healthy initially
        assert load_balancer.get_healthy_replica_count() == 3
        
        # Mark one unhealthy
        load_balancer.mark_unhealthy("replica2:5432")
        assert load_balancer.get_healthy_replica_count() == 2
    
    def test_get_healthy_replica_count_empty(self, load_balancer):
        """Test getting count when no replicas."""
        assert load_balancer.get_healthy_replica_count() == 0


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_select_replica_with_zero_weights(self, load_balancer, replica1, replica2):
        """Test selection when all replicas have zero weight."""
        load_balancer.add_replica(replica1)
        load_balancer.add_replica(replica2)
        
        # Set weights to very low values
        load_balancer.replicas["replica1:5432"].weight = 0.01
        load_balancer.replicas["replica2:5432"].weight = 0.01
        load_balancer._rebuild_weighted_list()
        
        # Should still be able to select
        selected = load_balancer.select_replica()
        assert selected in ["replica1:5432", "replica2:5432"]
    
    def test_concurrent_weight_updates(self, load_balancer, replica1):
        """Test that concurrent weight updates don't cause issues."""
        load_balancer.add_replica(replica1)
        
        # Simulate concurrent updates
        for i in range(10):
            load_balancer.update_replica_weight(
                "replica1:5432",
                cpu_util=50.0 + i,
                response_time=10.0 + i
            )
        
        # Should complete without errors
        assert load_balancer.replicas["replica1:5432"].weight > 0
    
    def test_rebuild_weighted_list_with_no_healthy_replicas(
        self, load_balancer, replica1, replica2, health_monitor
    ):
        """Test rebuilding weighted list when no replicas are healthy."""
        load_balancer.add_replica(replica1)
        load_balancer.add_replica(replica2)
        
        # Mark all unhealthy
        load_balancer.mark_unhealthy("replica1:5432")
        load_balancer.mark_unhealthy("replica2:5432")
        
        # Mock health monitor to return unhealthy status
        def mock_check_health(instance):
            return HealthStatus(
                instance=instance,
                is_healthy=False,
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                replication_lag=None,
                last_check=datetime.now()
            )
        
        health_monitor.check_health = mock_check_health
        
        # Weighted list should be empty
        assert len(load_balancer._weighted_replica_list) == 0
        
        # Selection should fall back to primary
        selected = load_balancer.select_replica()
        assert selected == "primary:5432"


class TestRequirementValidation:
    """Test that specific requirements are met."""
    
    def test_requirement_9_1_distributes_across_healthy_replicas(
        self, load_balancer, replica1, replica2, replica3
    ):
        """Requirement 9.1: Distribute read queries across all healthy replicas."""
        load_balancer.add_replica(replica1)
        load_balancer.add_replica(replica2)
        load_balancer.add_replica(replica3)
        
        selections = [load_balancer.select_replica() for _ in range(30)]
        
        # All healthy replicas should receive queries
        assert "replica1:5432" in selections
        assert "replica2:5432" in selections
        assert "replica3:5432" in selections
    
    def test_requirement_9_2_weighted_round_robin(
        self, load_balancer, replica1, replica2
    ):
        """Requirement 9.2: Implement weighted round-robin based on capacity."""
        load_balancer.add_replica(replica1)
        load_balancer.add_replica(replica2)
        
        # Set different weights
        load_balancer.replicas["replica1:5432"].weight = 3.0
        load_balancer.replicas["replica2:5432"].weight = 1.0
        load_balancer._rebuild_weighted_list()
        
        selections = [load_balancer.select_replica() for _ in range(400)]
        
        count1 = selections.count("replica1:5432")
        count2 = selections.count("replica2:5432")
        
        # Higher weight replica should get more traffic
        assert count1 > count2
    
    def test_requirement_9_3_reduce_traffic_at_80_percent_cpu(
        self, load_balancer, replica1, replica2
    ):
        """Requirement 9.3: Reduce traffic to replicas at >80% CPU."""
        load_balancer.add_replica(replica1)
        load_balancer.add_replica(replica2)
        
        # replica1 has high CPU
        load_balancer.update_replica_weight("replica1:5432", cpu_util=85.0, response_time=10.0)
        load_balancer.update_replica_weight("replica2:5432", cpu_util=50.0, response_time=10.0)
        
        # Check that replica1 has reduced weight
        weight1 = load_balancer.replicas["replica1:5432"].weight
        weight2 = load_balancer.replicas["replica2:5432"].weight
        
        assert weight1 < weight2
    
    def test_requirement_9_4_prefer_faster_replicas(
        self, load_balancer, replica1, replica2
    ):
        """Requirement 9.4: Track response times and prefer faster replicas."""
        load_balancer.add_replica(replica1)
        load_balancer.add_replica(replica2)
        
        # replica1 is faster
        load_balancer.update_replica_weight("replica1:5432", cpu_util=50.0, response_time=5.0)
        load_balancer.update_replica_weight("replica2:5432", cpu_util=50.0, response_time=20.0)
        
        # Faster replica should have higher weight
        weight1 = load_balancer.replicas["replica1:5432"].weight
        weight2 = load_balancer.replicas["replica2:5432"].weight
        
        assert weight1 > weight2
    
    def test_requirement_9_5_fallback_to_primary_when_all_unhealthy(
        self, load_balancer, replica1, replica2, health_monitor
    ):
        """Requirement 9.5: Route to primary when all replicas unhealthy."""
        load_balancer.add_replica(replica1)
        load_balancer.add_replica(replica2)
        
        # Mock all replicas as unhealthy
        def mock_check_health(instance):
            return HealthStatus(
                instance=instance,
                is_healthy=False,
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                replication_lag=None,
                last_check=datetime.now()
            )
        
        health_monitor.check_health = mock_check_health
        
        selected = load_balancer.select_replica()
        assert selected == "primary:5432"
