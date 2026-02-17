"""
Database Router for Read/Write Splitting

This router integrates with Django's database routing system to automatically
route read queries to replicas and write queries to the primary database.

It works in conjunction with the WorkloadIsolator to provide seamless
query routing based on operation type.
"""

import logging
from typing import Optional, Type
from django.db import models
from django.conf import settings

logger = logging.getLogger(__name__)


class ReplicationRouter:
    """
    Database router that implements read/write splitting.
    
    Routes:
    - Write operations (INSERT, UPDATE, DELETE) → 'default' (primary)
    - Read operations (SELECT) → 'replica' (read replicas)
    
    The actual replica selection is handled by the WorkloadIsolator,
    which considers replica health, lag, and load balancing.
    """
    
    def db_for_read(self, model: Type[models.Model], **hints) -> str:
        """
        Route read operations to replica database.
        
        Args:
            model: The model being queried
            **hints: Additional routing hints
            
        Returns:
            Database alias to use for read operations
        """
        # Check if replicas are configured
        if not hasattr(settings, 'DATABASE_REPLICAS') or not settings.DATABASE_REPLICAS:
            logger.debug("No replicas configured, routing read to primary")
            return 'default'
        
        # Check if this is a critical operation that should go to primary
        if hints.get('use_primary', False):
            logger.debug(f"Critical read for {model.__name__}, routing to primary")
            return 'default'
        
        # Route to replica (WorkloadIsolator will select specific replica)
        logger.debug(f"Routing read for {model.__name__} to replica")
        return 'replica'
    
    def db_for_write(self, model: Type[models.Model], **hints) -> str:
        """
        Route write operations to primary database.
        
        Args:
            model: The model being written
            **hints: Additional routing hints
            
        Returns:
            Database alias to use for write operations
        """
        logger.debug(f"Routing write for {model.__name__} to primary")
        return 'default'
    
    def allow_relation(self, obj1: models.Model, obj2: models.Model, **hints) -> bool:
        """
        Allow relations between objects in the same database.
        
        Args:
            obj1: First model instance
            obj2: Second model instance
            **hints: Additional routing hints
            
        Returns:
            True if relation is allowed
        """
        # Allow relations if both objects are in the same database
        db_set = {'default', 'replica'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None
    
    def allow_migrate(self, db: str, app_label: str, model_name: Optional[str] = None, **hints) -> bool:
        """
        Only allow migrations on the primary database.
        
        Args:
            db: Database alias
            app_label: Application label
            model_name: Model name (optional)
            **hints: Additional routing hints
            
        Returns:
            True if migration is allowed on this database
        """
        # Only run migrations on primary database
        return db == 'default'


class PrimaryOnlyRouter:
    """
    Fallback router that routes everything to primary database.
    
    Use this router when replicas are not available or during
    maintenance windows.
    """
    
    def db_for_read(self, model: Type[models.Model], **hints) -> str:
        """Route all reads to primary."""
        return 'default'
    
    def db_for_write(self, model: Type[models.Model], **hints) -> str:
        """Route all writes to primary."""
        return 'default'
    
    def allow_relation(self, obj1: models.Model, obj2: models.Model, **hints) -> bool:
        """Allow all relations."""
        return True
    
    def allow_migrate(self, db: str, app_label: str, model_name: Optional[str] = None, **hints) -> bool:
        """Allow migrations on primary only."""
        return db == 'default'
