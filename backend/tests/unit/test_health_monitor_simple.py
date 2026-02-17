"""Simple test to verify test collection works."""

import pytest
from infrastructure.health_monitor import HealthMonitor


def test_simple():
    """Simple test."""
    assert True


def test_health_monitor_creation():
    """Test creating a HealthMonitor."""
    monitor = HealthMonitor(
        primary_instance="primary:5432",
        replica_instances=["replica1:5432"],
        check_interval=10
    )
    assert monitor.primary_instance == "primary:5432"
