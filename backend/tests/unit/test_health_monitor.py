"""
Unit tests for HealthMonitor class.

Tests health monitoring, failover logic, and alert notifications.
"""

import asyncio
import time
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from infrastructure.health_monitor import HealthMonitor, AlertChannel
from infrastructure.models import HealthStatus, HealthEvent


@pytest.fixture
def health_monitor():
    """Create a HealthMonitor instance for testing."""
    return HealthMonitor(
        primary_instance="primary:5432",
        replica_instances=["replica1:5432", "replica2:5432", "replica3:5432"],
        check_interval=1,  # Short interval for testing
        failover_timeout=2,  # Short timeout for testing
        replication_lag_threshold=5.0,
        min_replicas=3,
        auto_resync_lag_threshold=10.0
    )


@pytest.fixture
def email_channel():
    """Create an email alert channel."""
    return AlertChannel(
        name="email",
        channel_type="email",
        config={"smtp_host": "smtp.example.com", "recipients": ["admin@example.com"]},
        enabled=True
    )


@pytest.fixture
def slack_channel():
    """Create a Slack alert channel."""
    return AlertChannel(
        name="slack",
        channel_type="slack",
        config={"webhook_url": "https://hooks.slack.com/services/xxx"},
        enabled=True
    )


@pytest.fixture
def pagerduty_channel():
    """Create a PagerDuty alert channel."""
    return AlertChannel(
        name="pagerduty",
        channel_type="pagerduty",
        config={"integration_key": "xxx"},
        enabled=True
    )


class TestHealthMonitorInitialization:
    """Test HealthMonitor initialization."""
    
    def test_initialization(self, health_monitor):
        """Test that HealthMonitor initializes correctly."""
        assert health_monitor.primary_instance == "primary:5432"
        assert len(health_monitor.replica_instances) == 3
        assert health_monitor.check_interval == 1
        assert health_monitor.failover_timeout == 2
        assert health_monitor.replication_lag_threshold == 5.0
        assert health_monitor.min_replicas == 3
        assert health_monitor.auto_resync_lag_threshold == 10.0
        assert not health_monitor.failover_in_progress
        assert health_monitor.primary_failure_detected_at is None
        assert health_monitor.resync_in_progress == {}
        assert health_monitor.last_resync_time == {}
    
    def test_add_alert_channel(self, health_monitor, email_channel):
        """Test adding alert channels."""
        health_monitor.add_alert_channel(email_channel)
        assert len(health_monitor.alert_channels) == 1
        assert health_monitor.alert_channels[0].name == "email"


class TestHealthChecks:
    """Test health check functionality."""
    
    @pytest.mark.asyncio
    async def test_check_health_returns_status(self, health_monitor):
        """Test that check_health returns health status."""
        # Set up a mock health status
        mock_status = HealthStatus(
            instance="primary:5432",
            is_healthy=True,
            cpu_percent=50.0,
            memory_percent=60.0,
            disk_percent=70.0,
            last_check=datetime.now()
        )
        health_monitor.health_status["primary:5432"] = mock_status
        
        status = health_monitor.check_health("primary:5432")
        assert status.instance == "primary:5432"
        assert status.is_healthy
        assert status.cpu_percent == 50.0
    
    @pytest.mark.asyncio
    async def test_check_health_unknown_instance(self, health_monitor):
        """Test check_health for unknown instance returns unhealthy status."""
        status = health_monitor.check_health("unknown:5432")
        assert status.instance == "unknown:5432"
        assert not status.is_healthy
        assert status.error_message == "No health check data available"
    
    @pytest.mark.asyncio
    async def test_monitor_replication_lag(self, health_monitor):
        """Test monitoring replication lag."""
        # Set up replica with replication lag
        mock_status = HealthStatus(
            instance="replica1:5432",
            is_healthy=True,
            cpu_percent=30.0,
            memory_percent=40.0,
            disk_percent=50.0,
            replication_lag=2.5,
            last_check=datetime.now()
        )
        health_monitor.health_status["replica1:5432"] = mock_status
        
        lag = health_monitor.monitor_replication_lag("replica1:5432")
        assert lag == 2.5
    
    @pytest.mark.asyncio
    async def test_monitor_replication_lag_not_available(self, health_monitor):
        """Test monitoring replication lag when not available."""
        lag = health_monitor.monitor_replication_lag("unknown:5432")
        assert lag == -1.0


class TestFailover:
    """Test failover functionality."""
    
    @pytest.mark.asyncio
    async def test_trigger_failover_selects_best_replica(self, health_monitor):
        """Test that failover selects the best replica."""
        # Set up healthy replicas with different metrics
        health_monitor.health_status["replica1:5432"] = HealthStatus(
            instance="replica1:5432",
            is_healthy=True,
            cpu_percent=80.0,
            memory_percent=70.0,
            disk_percent=60.0,
            replication_lag=3.0,
            last_check=datetime.now()
        )
        health_monitor.health_status["replica2:5432"] = HealthStatus(
            instance="replica2:5432",
            is_healthy=True,
            cpu_percent=40.0,
            memory_percent=50.0,
            disk_percent=60.0,
            replication_lag=1.0,  # Best replica (lowest lag)
            last_check=datetime.now()
        )
        health_monitor.health_status["replica3:5432"] = HealthStatus(
            instance="replica3:5432",
            is_healthy=True,
            cpu_percent=60.0,
            memory_percent=65.0,
            disk_percent=70.0,
            replication_lag=2.0,
            last_check=datetime.now()
        )
        
        # Mock the failover callback
        failover_called = []
        def mock_failover(replica):
            failover_called.append(replica)
        
        health_monitor.set_failover_callback(mock_failover)
        
        await health_monitor.trigger_failover()
        
        # Should select replica2 (lowest lag)
        assert len(failover_called) == 1
        assert failover_called[0] == "replica2:5432"
        assert health_monitor.primary_instance == "replica2:5432"
        assert "replica2:5432" not in health_monitor.replica_instances
    
    @pytest.mark.asyncio
    async def test_trigger_failover_no_healthy_replicas(self, health_monitor):
        """Test failover when no healthy replicas are available."""
        # Set all replicas as unhealthy
        for replica in health_monitor.replica_instances:
            health_monitor.health_status[replica] = HealthStatus(
                instance=replica,
                is_healthy=False,
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                last_check=datetime.now(),
                error_message="Connection failed"
            )
        
        # Failover should fail gracefully
        await health_monitor.trigger_failover()
        
        # Primary should remain unchanged
        assert health_monitor.primary_instance == "primary:5432"
    
    @pytest.mark.asyncio
    async def test_failover_in_progress_prevents_concurrent_failover(self, health_monitor):
        """Test that concurrent failover attempts are prevented."""
        health_monitor.failover_in_progress = True
        
        original_primary = health_monitor.primary_instance
        await health_monitor.trigger_failover()
        
        # Primary should remain unchanged
        assert health_monitor.primary_instance == original_primary


class TestAlertNotifications:
    """Test alert notification functionality."""
    
    @pytest.mark.asyncio
    async def test_notify_administrators(self, health_monitor, email_channel):
        """Test sending notifications to administrators."""
        health_monitor.add_alert_channel(email_channel)
        
        event = HealthEvent(
            event_type="test_event",
            instance="primary:5432",
            timestamp=datetime.now(),
            severity="warning",
            message="Test alert message"
        )
        
        # Should not raise any exceptions
        await health_monitor.notify_administrators(event)
    
    @pytest.mark.asyncio
    async def test_notify_administrators_multiple_channels(self, health_monitor, email_channel, slack_channel, pagerduty_channel):
        """Test sending notifications through multiple channels."""
        health_monitor.add_alert_channel(email_channel)
        health_monitor.add_alert_channel(slack_channel)
        health_monitor.add_alert_channel(pagerduty_channel)
        
        event = HealthEvent(
            event_type="primary_failure",
            instance="primary:5432",
            timestamp=datetime.now(),
            severity="critical",
            message="Primary database failure"
        )
        
        await health_monitor.notify_administrators(event)
        
        # All channels should be configured
        assert len(health_monitor.alert_channels) == 3
    
    @pytest.mark.asyncio
    async def test_notify_administrators_disabled_channel(self, health_monitor):
        """Test that disabled channels are skipped."""
        disabled_channel = AlertChannel(
            name="disabled",
            channel_type="email",
            config={},
            enabled=False
        )
        health_monitor.add_alert_channel(disabled_channel)
        
        event = HealthEvent(
            event_type="test",
            instance="test:5432",
            timestamp=datetime.now(),
            severity="info",
            message="Test"
        )
        
        # Should not raise exceptions even with disabled channel
        await health_monitor.notify_administrators(event)


class TestMonitoringLoop:
    """Test the monitoring loop functionality."""
    
    @pytest.mark.asyncio
    async def test_start_and_stop_monitoring(self, health_monitor):
        """Test starting and stopping the monitoring loop."""
        # Set up a simple health check callback
        def mock_health_check(instance):
            return HealthStatus(
                instance=instance,
                is_healthy=True,
                cpu_percent=50.0,
                memory_percent=60.0,
                disk_percent=70.0,
                replication_lag=1.0 if "replica" in instance else None,
                last_check=datetime.now()
            )
        
        health_monitor.set_health_check_callback(mock_health_check)
        
        # Start monitoring
        await health_monitor.start_monitoring()
        assert health_monitor._running
        
        # Let it run for a short time
        await asyncio.sleep(0.5)
        
        # Stop monitoring
        await health_monitor.stop_monitoring()
        assert not health_monitor._running
    
    @pytest.mark.asyncio
    async def test_monitoring_loop_performs_health_checks(self, health_monitor):
        """Test that monitoring loop performs health checks."""
        check_count = {"count": 0}
        
        def mock_health_check(instance):
            check_count["count"] += 1
            return HealthStatus(
                instance=instance,
                is_healthy=True,
                cpu_percent=50.0,
                memory_percent=60.0,
                disk_percent=70.0,
                replication_lag=1.0 if "replica" in instance else None,
                last_check=datetime.now()
            )
        
        health_monitor.set_health_check_callback(mock_health_check)
        
        await health_monitor.start_monitoring()
        await asyncio.sleep(1.5)  # Wait for at least one check cycle
        await health_monitor.stop_monitoring()
        
        # Should have performed health checks (4 instances: 1 primary + 3 replicas)
        assert check_count["count"] >= 4
    
    @pytest.mark.asyncio
    async def test_high_replication_lag_triggers_alert(self, health_monitor):
        """Test that high replication lag triggers an alert."""
        alerts_sent = []
        
        def mock_health_check(instance):
            lag = 10.0 if instance == "replica1:5432" else 1.0  # High lag on replica1
            return HealthStatus(
                instance=instance,
                is_healthy=True,
                cpu_percent=50.0,
                memory_percent=60.0,
                disk_percent=70.0,
                replication_lag=lag if "replica" in instance else None,
                last_check=datetime.now()
            )
        
        health_monitor.set_health_check_callback(mock_health_check)
        
        # Override notify_administrators to track alerts
        original_notify = health_monitor.notify_administrators
        async def mock_notify(event):
            alerts_sent.append(event)
            await original_notify(event)
        
        health_monitor.notify_administrators = mock_notify
        
        await health_monitor.start_monitoring()
        await asyncio.sleep(1.5)
        await health_monitor.stop_monitoring()
        
        # Should have sent alert for high replication lag
        lag_alerts = [a for a in alerts_sent if a.event_type == "high_replication_lag"]
        assert len(lag_alerts) > 0


class TestPrimaryFailureHandling:
    """Test primary database failure handling."""
    
    @pytest.mark.asyncio
    async def test_primary_failure_detection(self, health_monitor):
        """Test that primary failure is detected."""
        def mock_health_check(instance):
            is_healthy = instance != "primary:5432"  # Primary is unhealthy
            return HealthStatus(
                instance=instance,
                is_healthy=is_healthy,
                cpu_percent=50.0,
                memory_percent=60.0,
                disk_percent=70.0,
                replication_lag=1.0 if "replica" in instance else None,
                last_check=datetime.now(),
                error_message="Connection failed" if not is_healthy else None
            )
        
        health_monitor.set_health_check_callback(mock_health_check)
        
        # Perform one health check cycle
        await health_monitor._perform_health_checks()
        
        # Primary failure should be detected
        assert health_monitor.primary_failure_detected_at is not None
    
    @pytest.mark.asyncio
    async def test_primary_failure_triggers_failover_after_timeout(self, health_monitor):
        """Test that failover is triggered after timeout."""
        failover_triggered = []
        
        def mock_health_check(instance):
            is_healthy = instance != "primary:5432"
            return HealthStatus(
                instance=instance,
                is_healthy=is_healthy,
                cpu_percent=50.0,
                memory_percent=60.0,
                disk_percent=70.0,
                replication_lag=1.0 if "replica" in instance else None,
                last_check=datetime.now()
            )
        
        def mock_failover(replica):
            failover_triggered.append(replica)
        
        health_monitor.set_health_check_callback(mock_health_check)
        health_monitor.set_failover_callback(mock_failover)
        
        await health_monitor.start_monitoring()
        await asyncio.sleep(2.5)  # Wait for failover timeout (2s) + buffer
        await health_monitor.stop_monitoring()
        
        # Failover should have been triggered
        assert len(failover_triggered) > 0


class TestUtilityMethods:
    """Test utility methods."""
    
    def test_get_all_health_status(self, health_monitor):
        """Test getting all health statuses."""
        mock_status = HealthStatus(
            instance="primary:5432",
            is_healthy=True,
            cpu_percent=50.0,
            memory_percent=60.0,
            disk_percent=70.0,
            last_check=datetime.now()
        )
        health_monitor.health_status["primary:5432"] = mock_status
        
        all_status = health_monitor.get_all_health_status()
        assert "primary:5432" in all_status
        assert all_status["primary:5432"].is_healthy
    
    def test_is_instance_healthy(self, health_monitor):
        """Test checking if instance is healthy."""
        mock_status = HealthStatus(
            instance="primary:5432",
            is_healthy=True,
            cpu_percent=50.0,
            memory_percent=60.0,
            disk_percent=70.0,
            last_check=datetime.now()
        )
        health_monitor.health_status["primary:5432"] = mock_status
        
        assert health_monitor.is_instance_healthy("primary:5432")
        assert not health_monitor.is_instance_healthy("unknown:5432")



class TestReplicationLagMonitoring:
    """Test replication lag monitoring and management."""
    
    def test_replica_capacity_check_passes(self, health_monitor):
        """Test that replica capacity check passes with sufficient replicas."""
        # 3 replicas meets minimum requirement of 3
        assert health_monitor.check_replica_capacity()
    
    def test_replica_capacity_check_fails(self):
        """Test that replica capacity check fails with insufficient replicas."""
        monitor = HealthMonitor(
            primary_instance="primary:5432",
            replica_instances=["replica1:5432", "replica2:5432"],  # Only 2 replicas
            min_replicas=3
        )
        assert not monitor.check_replica_capacity()
    
    def test_replica_capacity_warning_on_init(self, caplog):
        """Test that warning is logged when replica capacity is insufficient."""
        import logging
        caplog.set_level(logging.WARNING)
        
        monitor = HealthMonitor(
            primary_instance="primary:5432",
            replica_instances=["replica1:5432"],  # Only 1 replica
            min_replicas=3
        )
        
        # Check that warning was logged
        assert any("Replica capacity" in record.message for record in caplog.records)
    
    @pytest.mark.asyncio
    async def test_automatic_resync_triggered_on_high_lag(self, health_monitor):
        """Test that automatic resync is triggered when lag exceeds threshold."""
        resync_called = []
        
        def mock_resync(replica):
            resync_called.append(replica)
        
        health_monitor.set_resync_callback(mock_resync)
        
        # Simulate high lag (15s > 10s threshold)
        await health_monitor._handle_replica_resync("replica1:5432", 15.0)
        
        assert len(resync_called) == 1
        assert resync_called[0] == "replica1:5432"
        assert health_monitor.last_resync_time.get("replica1:5432") is not None
    
    @pytest.mark.asyncio
    async def test_resync_not_triggered_if_already_in_progress(self, health_monitor):
        """Test that resync is not triggered if already in progress."""
        resync_called = []
        
        def mock_resync(replica):
            resync_called.append(replica)
        
        health_monitor.set_resync_callback(mock_resync)
        health_monitor.resync_in_progress["replica1:5432"] = True
        
        await health_monitor._handle_replica_resync("replica1:5432", 15.0)
        
        # Should not trigger resync
        assert len(resync_called) == 0
    
    @pytest.mark.asyncio
    async def test_resync_throttled_after_recent_resync(self, health_monitor):
        """Test that resync is throttled if recently performed."""
        resync_called = []
        
        def mock_resync(replica):
            resync_called.append(replica)
        
        health_monitor.set_resync_callback(mock_resync)
        
        # Simulate recent resync (1 second ago)
        health_monitor.last_resync_time["replica1:5432"] = time.time() - 1
        
        await health_monitor._handle_replica_resync("replica1:5432", 15.0)
        
        # Should not trigger resync (too soon)
        assert len(resync_called) == 0
    
    @pytest.mark.asyncio
    async def test_resync_allowed_after_cooldown_period(self, health_monitor):
        """Test that resync is allowed after cooldown period."""
        resync_called = []
        
        def mock_resync(replica):
            resync_called.append(replica)
        
        health_monitor.set_resync_callback(mock_resync)
        
        # Simulate resync 6 minutes ago (beyond 5 minute cooldown)
        health_monitor.last_resync_time["replica1:5432"] = time.time() - 360
        
        await health_monitor._handle_replica_resync("replica1:5432", 15.0)
        
        # Should trigger resync
        assert len(resync_called) == 1
    
    @pytest.mark.asyncio
    async def test_resync_failure_handled_gracefully(self, health_monitor):
        """Test that resync failures are handled gracefully."""
        def mock_resync_fail(replica):
            raise Exception("Resync failed")
        
        health_monitor.set_resync_callback(mock_resync_fail)
        
        # Should not raise exception
        await health_monitor._handle_replica_resync("replica1:5432", 15.0)
        
        # Resync should no longer be in progress
        assert not health_monitor.resync_in_progress.get("replica1:5432", False)
    
    @pytest.mark.asyncio
    async def test_resync_completion_sends_notification(self, health_monitor):
        """Test that successful resync sends notification."""
        notifications = []
        
        def mock_resync(replica):
            pass  # Successful resync
        
        async def mock_notify(event):
            notifications.append(event)
        
        health_monitor.set_resync_callback(mock_resync)
        health_monitor.notify_administrators = mock_notify
        
        await health_monitor._handle_replica_resync("replica1:5432", 15.0)
        
        # Should have sent notification
        assert len(notifications) == 1
        assert notifications[0].event_type == "replica_resync_completed"
    
    @pytest.mark.asyncio
    async def test_resync_failure_sends_notification(self, health_monitor):
        """Test that failed resync sends notification."""
        notifications = []
        
        def mock_resync_fail(replica):
            raise Exception("Resync failed")
        
        async def mock_notify(event):
            notifications.append(event)
        
        health_monitor.set_resync_callback(mock_resync_fail)
        health_monitor.notify_administrators = mock_notify
        
        await health_monitor._handle_replica_resync("replica1:5432", 15.0)
        
        # Should have sent failure notification
        assert len(notifications) == 1
        assert notifications[0].event_type == "replica_resync_failed"
    
    def test_get_replication_status(self, health_monitor):
        """Test getting comprehensive replication status."""
        # Set up some replica statuses
        health_monitor.health_status["replica1:5432"] = HealthStatus(
            instance="replica1:5432",
            is_healthy=True,
            cpu_percent=50.0,
            memory_percent=60.0,
            disk_percent=70.0,
            replication_lag=2.0,
            last_check=datetime.now()
        )
        health_monitor.health_status["replica2:5432"] = HealthStatus(
            instance="replica2:5432",
            is_healthy=True,
            cpu_percent=40.0,
            memory_percent=50.0,
            disk_percent=60.0,
            replication_lag=8.0,
            last_check=datetime.now()
        )
        
        status = health_monitor.get_replication_status()
        
        assert status["primary"] == "primary:5432"
        assert status["replica_count"] == 3
        assert status["min_replicas"] == 3
        assert status["meets_capacity_requirement"]
        assert status["lag_threshold"] == 5.0
        assert status["auto_resync_threshold"] == 10.0
        assert len(status["replicas"]) == 2  # Only replicas with health status
    
    @pytest.mark.asyncio
    async def test_monitoring_loop_triggers_resync_on_high_lag(self, health_monitor):
        """Test that monitoring loop triggers resync for high lag replicas."""
        resync_called = []
        
        def mock_health_check(instance):
            # Replica1 has critically high lag
            lag = 15.0 if instance == "replica1:5432" else 1.0
            return HealthStatus(
                instance=instance,
                is_healthy=True,
                cpu_percent=50.0,
                memory_percent=60.0,
                disk_percent=70.0,
                replication_lag=lag if "replica" in instance else None,
                last_check=datetime.now()
            )
        
        def mock_resync(replica):
            resync_called.append(replica)
        
        health_monitor.set_health_check_callback(mock_health_check)
        health_monitor.set_resync_callback(mock_resync)
        
        await health_monitor.start_monitoring()
        await asyncio.sleep(1.5)  # Wait for at least one check cycle
        await health_monitor.stop_monitoring()
        
        # Should have triggered resync for replica1
        assert "replica1:5432" in resync_called
    
    @pytest.mark.asyncio
    async def test_lag_alert_triggered_before_resync_threshold(self, health_monitor):
        """Test that lag alerts are triggered before resync threshold."""
        alerts_sent = []
        
        def mock_health_check(instance):
            # Replica1 has high lag (7s) but not critical (< 10s)
            lag = 7.0 if instance == "replica1:5432" else 1.0
            return HealthStatus(
                instance=instance,
                is_healthy=True,
                cpu_percent=50.0,
                memory_percent=60.0,
                disk_percent=70.0,
                replication_lag=lag if "replica" in instance else None,
                last_check=datetime.now()
            )
        
        health_monitor.set_health_check_callback(mock_health_check)
        
        # Override notify_administrators to track alerts
        async def mock_notify(event):
            alerts_sent.append(event)
        
        health_monitor.notify_administrators = mock_notify
        
        await health_monitor.start_monitoring()
        await asyncio.sleep(1.5)
        await health_monitor.stop_monitoring()
        
        # Should have sent lag alert (7s > 5s threshold)
        lag_alerts = [a for a in alerts_sent if a.event_type == "high_replication_lag"]
        assert len(lag_alerts) > 0
        
        # Should NOT have sent resync notification (7s < 10s threshold)
        resync_alerts = [a for a in alerts_sent if "resync" in a.event_type]
        assert len(resync_alerts) == 0


class TestReplicaCapacityValidation:
    """Test replica capacity validation (Requirement 6.4)."""
    
    def test_minimum_three_replicas_supported(self):
        """Test that system supports minimum of 3 replicas."""
        monitor = HealthMonitor(
            primary_instance="primary:5432",
            replica_instances=["replica1:5432", "replica2:5432", "replica3:5432"],
            min_replicas=3
        )
        assert monitor.check_replica_capacity()
    
    def test_more_than_minimum_replicas_supported(self):
        """Test that system supports more than minimum replicas."""
        monitor = HealthMonitor(
            primary_instance="primary:5432",
            replica_instances=[
                "replica1:5432",
                "replica2:5432",
                "replica3:5432",
                "replica4:5432",
                "replica5:5432"
            ],
            min_replicas=3
        )
        assert monitor.check_replica_capacity()
        assert len(monitor.replica_instances) == 5
    
    def test_capacity_check_in_replication_status(self):
        """Test that capacity check is included in replication status."""
        monitor = HealthMonitor(
            primary_instance="primary:5432",
            replica_instances=["replica1:5432", "replica2:5432"],
            min_replicas=3
        )
        
        status = monitor.get_replication_status()
        assert "meets_capacity_requirement" in status
        assert not status["meets_capacity_requirement"]  # Only 2 replicas, need 3
