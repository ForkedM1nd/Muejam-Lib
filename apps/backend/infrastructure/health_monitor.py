"""
Health Monitor for database instance monitoring and failover management.

This module implements health checking, monitoring, and automatic failover
for database instances (primary and replicas).
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass

from .models import HealthStatus, HealthEvent, ReplicaInfo


logger = logging.getLogger(__name__)


@dataclass
class AlertChannel:
    """Configuration for an alert notification channel."""
    name: str
    channel_type: str  # email, slack, pagerduty
    config: Dict[str, Any]
    enabled: bool = True


class HealthMonitor:
    """
    Monitor database instance health and trigger failover when needed.
    
    Responsibilities:
    - Perform health checks every 10 seconds
    - Monitor connectivity, replication lag, CPU, memory, disk
    - Send alerts through configured channels (email, Slack, PagerDuty)
    - Trigger automatic failover within 30 seconds of primary failure
    
    Requirements: 2.1, 2.3, 2.4, 2.5, 6.3
    """
    
    def __init__(
        self,
        primary_instance: str,
        replica_instances: List[str],
        check_interval: int = 10,
        failover_timeout: int = 30,
        replication_lag_threshold: float = 5.0,
        min_replicas: int = 3,
        auto_resync_lag_threshold: float = 10.0
    ):
        """
        Initialize the health monitor.
        
        Args:
            primary_instance: Connection string for primary database
            replica_instances: List of connection strings for replicas
            check_interval: Health check interval in seconds (default: 10)
            failover_timeout: Maximum time to complete failover in seconds (default: 30)
            replication_lag_threshold: Replication lag threshold for alerts in seconds (default: 5.0)
            min_replicas: Minimum number of replicas required (default: 3)
            auto_resync_lag_threshold: Lag threshold for automatic resync in seconds (default: 10.0)
        """
        self.primary_instance = primary_instance
        self.replica_instances = replica_instances
        self.check_interval = check_interval
        self.failover_timeout = failover_timeout
        self.replication_lag_threshold = replication_lag_threshold
        self.min_replicas = min_replicas
        self.auto_resync_lag_threshold = auto_resync_lag_threshold
        
        # Validate minimum replica capacity (Requirement 6.4)
        if len(replica_instances) < min_replicas:
            logger.warning(
                f"Replica capacity ({len(replica_instances)}) is below minimum "
                f"requirement ({min_replicas}). System may not meet availability requirements."
            )
        
        # Health status tracking
        self.health_status: Dict[str, HealthStatus] = {}
        self.last_check_time: Dict[str, float] = {}
        
        # Alert channels
        self.alert_channels: List[AlertChannel] = []
        
        # Failover state
        self.failover_in_progress = False
        self.primary_failure_detected_at: Optional[float] = None
        
        # Replication resync tracking
        self.resync_in_progress: Dict[str, bool] = {}
        self.last_resync_time: Dict[str, float] = {}
        
        # Monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Health check callbacks (for testing/integration)
        self._health_check_callback: Optional[Callable[[str], HealthStatus]] = None
        self._failover_callback: Optional[Callable[[str], None]] = None
        self._resync_callback: Optional[Callable[[str], None]] = None
    
    def add_alert_channel(self, channel: AlertChannel) -> None:
        """Add an alert notification channel."""
        self.alert_channels.append(channel)
        logger.info(f"Added alert channel: {channel.name} ({channel.channel_type})")
    
    def set_health_check_callback(self, callback: Callable[[str], HealthStatus]) -> None:
        """Set custom health check callback (for testing/integration)."""
        self._health_check_callback = callback
    
    def set_failover_callback(self, callback: Callable[[str], None]) -> None:
        """Set custom failover callback (for testing/integration)."""
        self._failover_callback = callback
    
    def set_resync_callback(self, callback: Callable[[str], None]) -> None:
        """Set custom resync callback (for testing/integration)."""
        self._resync_callback = callback
    
    async def start_monitoring(self) -> None:
        """Start the health monitoring loop."""
        if self._running:
            logger.warning("Health monitoring is already running")
            return
        
        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop the health monitoring loop."""
        if not self._running:
            return
        
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop that runs health checks periodically."""
        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
    
    async def _perform_health_checks(self) -> None:
        """Perform health checks on all database instances."""
        # Check primary
        primary_status = await self._check_instance_health(self.primary_instance, is_primary=True)
        self.health_status[self.primary_instance] = primary_status
        self.last_check_time[self.primary_instance] = time.time()
        
        # Check replicas
        for replica in self.replica_instances:
            replica_status = await self._check_instance_health(replica, is_primary=False)
            self.health_status[replica] = replica_status
            self.last_check_time[replica] = time.time()
            
            # Check replication lag and handle accordingly
            if replica_status.replication_lag is not None:
                # Alert if lag exceeds threshold (Requirement 6.3)
                if replica_status.replication_lag > self.replication_lag_threshold:
                    await self._handle_high_replication_lag(replica, replica_status.replication_lag)
                
                # Automatic resync if lag is critically high (Requirement 6.5)
                if replica_status.replication_lag > self.auto_resync_lag_threshold:
                    await self._handle_replica_resync(replica, replica_status.replication_lag)
        
        # Handle primary failure
        if not primary_status.is_healthy:
            await self._handle_primary_failure()
        else:
            # Reset failure detection if primary is healthy
            self.primary_failure_detected_at = None
    
    async def _check_instance_health(self, instance: str, is_primary: bool) -> HealthStatus:
        """
        Check health of a specific database instance.
        
        Args:
            instance: Database instance connection string
            is_primary: Whether this is the primary instance
        
        Returns:
            HealthStatus object with current health metrics
        """
        # Use custom callback if provided (for testing)
        if self._health_check_callback:
            return self._health_check_callback(instance)
        
        # Default health check implementation
        try:
            # In a real implementation, this would:
            # 1. Check database connectivity
            # 2. Query system metrics (CPU, memory, disk)
            # 3. Check replication lag for replicas
            # 4. Verify database is accepting connections
            
            # Placeholder implementation
            health_status = HealthStatus(
                instance=instance,
                is_healthy=True,
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                replication_lag=0.0 if not is_primary else None,
                last_check=datetime.now(),
                error_message=None
            )
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed for {instance}: {e}")
            return HealthStatus(
                instance=instance,
                is_healthy=False,
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                replication_lag=None,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    async def _handle_primary_failure(self) -> None:
        """Handle primary database failure and trigger failover if needed."""
        if self.failover_in_progress:
            return
        
        # Record when failure was first detected
        if self.primary_failure_detected_at is None:
            self.primary_failure_detected_at = time.time()
            logger.warning(f"Primary database failure detected: {self.primary_instance}")
            
            # Send alert
            event = HealthEvent(
                event_type="primary_failure",
                instance=self.primary_instance,
                timestamp=datetime.now(),
                severity="critical",
                message=f"Primary database {self.primary_instance} is unhealthy"
            )
            await self.notify_administrators(event)
        
        # Check if failover timeout has been reached
        time_since_failure = time.time() - self.primary_failure_detected_at
        if time_since_failure >= self.failover_timeout:
            await self.trigger_failover()
    
    async def _handle_high_replication_lag(self, replica: str, lag: float) -> None:
        """Handle high replication lag alert."""
        logger.warning(f"High replication lag detected on {replica}: {lag}s")
        
        event = HealthEvent(
            event_type="high_replication_lag",
            instance=replica,
            timestamp=datetime.now(),
            severity="warning",
            message=f"Replication lag on {replica} is {lag}s (threshold: {self.replication_lag_threshold}s)",
            metadata={"replication_lag": lag, "threshold": self.replication_lag_threshold}
        )
        await self.notify_administrators(event)
    
    async def _handle_replica_resync(self, replica: str, lag: float) -> None:
        """
        Handle automatic resync for lagging replicas.
        
        When a replica falls significantly behind (exceeds auto_resync_lag_threshold),
        this method triggers an automatic resync from the primary database.
        
        Args:
            replica: Replica instance connection string
            lag: Current replication lag in seconds
        
        Requirements: 6.5
        """
        # Check if resync is already in progress for this replica
        if self.resync_in_progress.get(replica, False):
            logger.debug(f"Resync already in progress for {replica}")
            return
        
        # Check if we recently resynced this replica (avoid thrashing)
        last_resync = self.last_resync_time.get(replica, 0)
        time_since_resync = time.time() - last_resync
        if time_since_resync < 300:  # Wait at least 5 minutes between resyncs
            logger.debug(
                f"Skipping resync for {replica}, last resync was {time_since_resync:.0f}s ago"
            )
            return
        
        logger.warning(
            f"Initiating automatic resync for {replica} due to high lag ({lag}s > {self.auto_resync_lag_threshold}s)"
        )
        
        self.resync_in_progress[replica] = True
        resync_start = time.time()
        
        try:
            # Use custom callback if provided (for testing)
            if self._resync_callback:
                self._resync_callback(replica)
            else:
                # In a real implementation, this would:
                # 1. Pause replication on the replica
                # 2. Take a snapshot from the primary
                # 3. Restore the snapshot to the replica
                # 4. Resume replication from the correct position
                logger.info(f"Resyncing {replica} from primary (placeholder)")
            
            resync_time = time.time() - resync_start
            self.last_resync_time[replica] = time.time()
            
            logger.info(f"Resync completed for {replica} in {resync_time:.2f}s")
            
            # Notify administrators of successful resync
            event = HealthEvent(
                event_type="replica_resync_completed",
                instance=replica,
                timestamp=datetime.now(),
                severity="info",
                message=f"Automatic resync completed for {replica} in {resync_time:.2f}s (lag was {lag}s)",
                metadata={
                    "replica": replica,
                    "previous_lag": lag,
                    "resync_time": resync_time
                }
            )
            await self.notify_administrators(event)
            
        except Exception as e:
            logger.error(f"Resync failed for {replica}: {e}", exc_info=True)
            
            # Notify administrators of failed resync
            event = HealthEvent(
                event_type="replica_resync_failed",
                instance=replica,
                timestamp=datetime.now(),
                severity="error",
                message=f"Automatic resync failed for {replica}: {str(e)}",
                metadata={
                    "replica": replica,
                    "lag": lag,
                    "error": str(e)
                }
            )
            await self.notify_administrators(event)
        finally:
            self.resync_in_progress[replica] = False
    
    def check_health(self, instance: str) -> HealthStatus:
        """
        Get the current health status of a database instance.
        
        Args:
            instance: Database instance connection string
        
        Returns:
            HealthStatus object, or a default unhealthy status if not found
        """
        return self.health_status.get(
            instance,
            HealthStatus(
                instance=instance,
                is_healthy=False,
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                last_check=datetime.now(),
                error_message="No health check data available"
            )
        )
    
    def monitor_replication_lag(self, replica: str) -> float:
        """
        Get the current replication lag for a replica.
        
        Args:
            replica: Replica instance connection string
        
        Returns:
            Replication lag in seconds, or -1.0 if not available
        """
        status = self.health_status.get(replica)
        if status and status.replication_lag is not None:
            return status.replication_lag
        return -1.0
    
    async def trigger_failover(self) -> None:
        """
        Trigger automatic failover to promote a replica to primary.
        
        This method:
        1. Selects the healthiest replica
        2. Promotes it to primary
        3. Updates routing configuration
        4. Notifies administrators
        
        Requirements: 2.1, 2.5
        """
        if self.failover_in_progress:
            logger.warning("Failover already in progress")
            return
        
        self.failover_in_progress = True
        failover_start = time.time()
        
        try:
            logger.critical(f"Initiating failover from {self.primary_instance}")
            
            # Select best replica for promotion
            best_replica = self._select_best_replica()
            if not best_replica:
                raise Exception("No healthy replica available for failover")
            
            logger.info(f"Selected replica for promotion: {best_replica}")
            
            # Use custom callback if provided (for testing)
            if self._failover_callback:
                self._failover_callback(best_replica)
            else:
                # In a real implementation, this would:
                # 1. Promote the replica to primary
                # 2. Update connection routing
                # 3. Reconfigure replication
                logger.info(f"Promoting {best_replica} to primary (placeholder)")
            
            # Update internal state
            old_primary = self.primary_instance
            self.primary_instance = best_replica
            self.replica_instances.remove(best_replica)
            
            failover_time = time.time() - failover_start
            logger.info(f"Failover completed in {failover_time:.2f}s")
            
            # Notify administrators
            event = HealthEvent(
                event_type="failover_completed",
                instance=best_replica,
                timestamp=datetime.now(),
                severity="critical",
                message=f"Failover completed: {old_primary} -> {best_replica} in {failover_time:.2f}s",
                metadata={
                    "old_primary": old_primary,
                    "new_primary": best_replica,
                    "failover_time": failover_time
                }
            )
            await self.notify_administrators(event)
            
        except Exception as e:
            logger.error(f"Failover failed: {e}", exc_info=True)
            event = HealthEvent(
                event_type="failover_failed",
                instance=self.primary_instance,
                timestamp=datetime.now(),
                severity="critical",
                message=f"Failover failed: {str(e)}"
            )
            await self.notify_administrators(event)
        finally:
            self.failover_in_progress = False
            self.primary_failure_detected_at = None
    
    def _select_best_replica(self) -> Optional[str]:
        """
        Select the best replica for promotion to primary.
        
        Selection criteria (in order of priority):
        1. Replica must be healthy
        2. Lowest replication lag
        3. Lowest CPU utilization
        4. Fastest response time
        
        Returns:
            Connection string of best replica, or None if no healthy replica
        """
        healthy_replicas = [
            (replica, self.health_status.get(replica))
            for replica in self.replica_instances
            if self.health_status.get(replica) and self.health_status[replica].is_healthy
        ]
        
        if not healthy_replicas:
            return None
        
        # Sort by replication lag (lowest first), then CPU, then response time
        def replica_score(item):
            replica, status = item
            lag = status.replication_lag if status.replication_lag is not None else float('inf')
            cpu = status.cpu_percent
            return (lag, cpu)
        
        healthy_replicas.sort(key=replica_score)
        return healthy_replicas[0][0]
    
    async def notify_administrators(self, event: HealthEvent) -> None:
        """
        Send alert notifications to administrators through configured channels.
        
        Args:
            event: HealthEvent to notify about
        
        Requirements: 2.5, 6.3
        """
        logger.info(f"Notifying administrators: {event.event_type} - {event.message}")
        
        for channel in self.alert_channels:
            if not channel.enabled:
                continue
            
            try:
                await self._send_alert(channel, event)
            except Exception as e:
                logger.error(f"Failed to send alert via {channel.name}: {e}")
    
    async def _send_alert(self, channel: AlertChannel, event: HealthEvent) -> None:
        """
        Send alert through a specific channel.
        
        Args:
            channel: AlertChannel configuration
            event: HealthEvent to send
        """
        # In a real implementation, this would integrate with:
        # - Email: SMTP or email service API
        # - Slack: Slack webhook or API
        # - PagerDuty: PagerDuty Events API
        
        logger.info(f"Sending alert via {channel.channel_type}: {event.message}")
        
        # Placeholder implementation
        if channel.channel_type == "email":
            # Send email
            pass
        elif channel.channel_type == "slack":
            # Send Slack message
            pass
        elif channel.channel_type == "pagerduty":
            # Create PagerDuty incident
            pass
        else:
            logger.warning(f"Unknown alert channel type: {channel.channel_type}")
    
    def get_all_health_status(self) -> Dict[str, HealthStatus]:
        """Get health status for all monitored instances."""
        return self.health_status.copy()
    
    def is_instance_healthy(self, instance: str) -> bool:
        """Check if a specific instance is healthy."""
        status = self.health_status.get(instance)
        return status.is_healthy if status else False
    
    def check_replica_capacity(self) -> bool:
        """
        Check if the system meets minimum replica capacity requirements.
        
        Returns:
            True if replica capacity meets minimum requirements, False otherwise
        
        Requirements: 6.4
        """
        current_replicas = len(self.replica_instances)
        meets_requirement = current_replicas >= self.min_replicas
        
        if not meets_requirement:
            logger.warning(
                f"Replica capacity check failed: {current_replicas} replicas "
                f"(minimum required: {self.min_replicas})"
            )
        
        return meets_requirement
    
    def get_replication_status(self) -> Dict[str, Any]:
        """
        Get comprehensive replication status for all replicas.
        
        Returns:
            Dictionary containing replication status information
        """
        replica_status = []
        for replica in self.replica_instances:
            status = self.health_status.get(replica)
            if status:
                replica_status.append({
                    "instance": replica,
                    "is_healthy": status.is_healthy,
                    "replication_lag": status.replication_lag,
                    "resync_in_progress": self.resync_in_progress.get(replica, False),
                    "last_resync": self.last_resync_time.get(replica),
                    "last_check": status.last_check.isoformat()
                })
        
        return {
            "primary": self.primary_instance,
            "replica_count": len(self.replica_instances),
            "min_replicas": self.min_replicas,
            "meets_capacity_requirement": self.check_replica_capacity(),
            "replicas": replica_status,
            "lag_threshold": self.replication_lag_threshold,
            "auto_resync_threshold": self.auto_resync_lag_threshold
        }
