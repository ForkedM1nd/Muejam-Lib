"""
Load Balancer for distributing read queries across database replicas.

This module implements weighted round-robin load balancing with dynamic
weight adjustment based on replica performance metrics.
"""

import logging
import time
from typing import List, Optional, Dict
from threading import Lock

from .models import ReplicaInfo
from .health_monitor import HealthMonitor


logger = logging.getLogger(__name__)


class LoadBalancer:
    """
    Distribute read queries across healthy replicas using weighted round-robin.
    
    Responsibilities:
    - Distribute read queries across all healthy Read_Replica instances
    - Implement weighted round-robin based on replica capacity
    - Reduce traffic to replicas at >80% CPU utilization
    - Track query response times and prefer faster replicas
    - Fall back to primary when all replicas are unhealthy
    
    Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
    """
    
    def __init__(
        self,
        primary_instance: str,
        health_monitor: HealthMonitor,
        cpu_threshold: float = 80.0,
        weight_adjustment_factor: float = 0.5
    ):
        """
        Initialize the load balancer.
        
        Args:
            primary_instance: Connection string for primary database (fallback)
            health_monitor: HealthMonitor instance for checking replica health
            cpu_threshold: CPU utilization threshold for traffic reduction (default: 80%)
            weight_adjustment_factor: Factor to reduce weight when CPU is high (default: 0.5)
        """
        self.primary_instance = primary_instance
        self.health_monitor = health_monitor
        self.cpu_threshold = cpu_threshold
        self.weight_adjustment_factor = weight_adjustment_factor
        
        # Replica tracking
        self.replicas: Dict[str, ReplicaInfo] = {}
        self._lock = Lock()
        
        # Round-robin state
        self._current_index = 0
        self._weighted_replica_list: List[str] = []
        
        # Performance tracking
        self._response_times: Dict[str, List[float]] = {}
        self._response_time_window = 100  # Keep last 100 response times
    
    def add_replica(self, replica: ReplicaInfo) -> None:
        """
        Add a replica to the load balancer pool.
        
        Args:
            replica: ReplicaInfo object with replica details
        """
        with self._lock:
            self.replicas[replica.host] = replica
            self._response_times[replica.host] = []
            self._rebuild_weighted_list()
            logger.info(f"Added replica to load balancer: {replica.host}")
    
    def remove_replica(self, replica_host: str) -> None:
        """
        Remove a replica from the load balancer pool.
        
        Args:
            replica_host: Host identifier of the replica to remove
        """
        with self._lock:
            if replica_host in self.replicas:
                del self.replicas[replica_host]
                if replica_host in self._response_times:
                    del self._response_times[replica_host]
                self._rebuild_weighted_list()
                logger.info(f"Removed replica from load balancer: {replica_host}")
    
    def select_replica(self) -> str:
        """
        Select the best replica for the next query using weighted round-robin.
        
        This method:
        1. Filters out unhealthy replicas
        2. Applies weighted round-robin based on replica weights
        3. Falls back to primary if all replicas are unhealthy
        
        Returns:
            Connection string of selected replica or primary (fallback)
        
        Requirements: 9.1, 9.2, 9.5
        """
        with self._lock:
            # Update replica health status from health monitor
            # (only if we have replicas to check)
            if self.replicas:
                self._update_replica_health()
            
            # Get healthy replicas
            healthy_replicas = [
                host for host, replica in self.replicas.items()
                if replica.is_healthy
            ]
            
            # Fallback to primary if no healthy replicas
            if not healthy_replicas:
                logger.warning("No healthy replicas available, falling back to primary")
                return self.primary_instance
            
            # Rebuild weighted list if needed
            if not self._weighted_replica_list:
                self._rebuild_weighted_list()
            
            # If still no weighted list (all weights are 0), use simple round-robin
            if not self._weighted_replica_list:
                self._current_index = (self._current_index + 1) % len(healthy_replicas)
                return healthy_replicas[self._current_index]
            
            # Weighted round-robin selection
            selected = self._weighted_replica_list[self._current_index]
            self._current_index = (self._current_index + 1) % len(self._weighted_replica_list)
            
            # Ensure selected replica is still healthy
            if selected not in healthy_replicas:
                # Rebuild and try again
                self._rebuild_weighted_list()
                if self._weighted_replica_list:
                    selected = self._weighted_replica_list[0]
                    self._current_index = 1
                else:
                    return self.primary_instance
            
            return selected
    
    def update_replica_weight(
        self,
        replica: str,
        cpu_util: float,
        response_time: float
    ) -> None:
        """
        Adjust replica weight based on performance metrics.
        
        Weight calculation:
        - Base weight: 1.0
        - CPU > 80%: weight *= 0.5 (reduce traffic)
        - Response time: weight adjusted inversely proportional to response time
        
        Args:
            replica: Replica host identifier
            cpu_util: CPU utilization percentage (0-100)
            response_time: Average response time in milliseconds
        
        Requirements: 9.2, 9.3, 9.4
        """
        with self._lock:
            if replica not in self.replicas:
                logger.warning(f"Attempted to update weight for unknown replica: {replica}")
                return
            
            replica_info = self.replicas[replica]
            
            # Update metrics
            replica_info.cpu_utilization = cpu_util
            replica_info.avg_response_time = response_time
            
            # Calculate new weight
            base_weight = 1.0
            
            # Reduce weight if CPU is high (Requirement 9.3)
            if cpu_util >= self.cpu_threshold:
                base_weight *= self.weight_adjustment_factor
                logger.info(
                    f"Reducing traffic to {replica} due to high CPU: {cpu_util:.1f}%"
                )
            
            # Adjust weight based on response time (Requirement 9.4)
            # Faster replicas get higher weight
            if response_time > 0:
                # Calculate average response time across all replicas
                all_response_times = [
                    r.avg_response_time for r in self.replicas.values()
                    if r.avg_response_time > 0
                ]
                
                if all_response_times:
                    avg_response_time = sum(all_response_times) / len(all_response_times)
                    
                    # Adjust weight inversely proportional to response time
                    # Faster than average: weight increases
                    # Slower than average: weight decreases
                    if avg_response_time > 0:
                        response_time_factor = avg_response_time / response_time
                        base_weight *= response_time_factor
            
            # Ensure weight is positive and reasonable
            replica_info.weight = max(0.1, min(base_weight, 10.0))
            
            # Rebuild weighted list with new weights
            self._rebuild_weighted_list()
            
            logger.debug(
                f"Updated replica weight: {replica} -> {replica_info.weight:.2f} "
                f"(CPU: {cpu_util:.1f}%, RT: {response_time:.1f}ms)"
            )
    
    def record_response_time(self, replica: str, response_time: float) -> None:
        """
        Record a query response time for a replica.
        
        Args:
            replica: Replica host identifier
            response_time: Response time in milliseconds
        """
        with self._lock:
            if replica not in self._response_times:
                self._response_times[replica] = []
            
            # Add response time and maintain window size
            self._response_times[replica].append(response_time)
            if len(self._response_times[replica]) > self._response_time_window:
                self._response_times[replica].pop(0)
            
            # Update average response time in replica info
            if replica in self.replicas:
                avg_rt = sum(self._response_times[replica]) / len(self._response_times[replica])
                self.replicas[replica].avg_response_time = avg_rt
    
    def mark_unhealthy(self, replica: str) -> None:
        """
        Mark a replica as unhealthy and remove it from the active pool.
        
        Args:
            replica: Replica host identifier
        
        Requirements: 2.3
        """
        with self._lock:
            if replica in self.replicas:
                self.replicas[replica].is_healthy = False
                self._rebuild_weighted_list()
                logger.warning(f"Marked replica as unhealthy: {replica}")
    
    def mark_healthy(self, replica: str) -> None:
        """
        Mark a replica as healthy and add it back to the active pool.
        
        Args:
            replica: Replica host identifier
        """
        with self._lock:
            if replica in self.replicas:
                self.replicas[replica].is_healthy = True
                self._rebuild_weighted_list()
                logger.info(f"Marked replica as healthy: {replica}")
    
    def _update_replica_health(self) -> None:
        """
        Update replica health status from the health monitor.
        
        This method synchronizes the load balancer's view of replica health
        with the health monitor's current status.
        """
        for replica_host in list(self.replicas.keys()):
            health_status = self.health_monitor.check_health(replica_host)
            
            replica_info = self.replicas[replica_host]
            was_healthy = replica_info.is_healthy
            replica_info.is_healthy = health_status.is_healthy
            replica_info.cpu_utilization = health_status.cpu_percent
            
            # Update replication lag if available
            if health_status.replication_lag is not None:
                replica_info.replication_lag = health_status.replication_lag
            
            # Log health status changes
            if was_healthy and not replica_info.is_healthy:
                logger.warning(f"Replica became unhealthy: {replica_host}")
                self._rebuild_weighted_list()
            elif not was_healthy and replica_info.is_healthy:
                logger.info(f"Replica became healthy: {replica_host}")
                self._rebuild_weighted_list()
    
    def _rebuild_weighted_list(self) -> None:
        """
        Rebuild the weighted replica list for round-robin selection.
        
        The weighted list contains multiple copies of each replica based on
        its weight. For example, a replica with weight 2.0 appears twice as
        often as a replica with weight 1.0.
        """
        self._weighted_replica_list = []
        
        # Only include healthy replicas
        healthy_replicas = {
            host: replica for host, replica in self.replicas.items()
            if replica.is_healthy
        }
        
        if not healthy_replicas:
            return
        
        # Calculate how many times each replica should appear
        # We use a multiplier to convert fractional weights to integers
        multiplier = 10
        
        for host, replica in healthy_replicas.items():
            # Number of times this replica appears in the list
            count = max(1, int(replica.weight * multiplier))
            self._weighted_replica_list.extend([host] * count)
        
        # Reset index if it's out of bounds
        if self._current_index >= len(self._weighted_replica_list):
            self._current_index = 0
        
        logger.debug(
            f"Rebuilt weighted replica list: {len(self._weighted_replica_list)} entries "
            f"for {len(healthy_replicas)} healthy replicas"
        )
    
    def get_replica_stats(self) -> Dict[str, ReplicaInfo]:
        """
        Get current statistics for all replicas.
        
        Returns:
            Dictionary mapping replica host to ReplicaInfo
        """
        with self._lock:
            return {host: replica for host, replica in self.replicas.items()}
    
    def get_healthy_replica_count(self) -> int:
        """
        Get the count of currently healthy replicas.
        
        Returns:
            Number of healthy replicas
        """
        with self._lock:
            return sum(1 for replica in self.replicas.values() if replica.is_healthy)
