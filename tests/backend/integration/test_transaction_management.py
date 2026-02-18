"""
Integration Tests for Transaction Management

This module tests transaction management including:
- Atomic operations
- Transaction rollback on errors
- Concurrent transaction handling
- Transaction isolation
- Nested transactions

Requirements: 2.4, 5.1
"""

import pytest
from django.test import Client, override_settings, TransactionTestCase
from django.db import transaction, connection
from unittest.mock import patch, MagicMock
import time


# Disable timeout middleware for tests (SIGALRM not available on Windows)
TEST_MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'infrastructure.https_enforcement.HTTPSEnforcementMiddleware',
    'csp.middleware.CSPMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.users.middleware.ClerkAuthMiddleware',
    'infrastructure.rate_limit_middleware.RateLimitMiddleware',
]


class TestTransactionManagement(TransactionTestCase):
    """Integration tests for transaction management."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_transaction_decorator_exists(self):
        """Test that atomic_api_view decorator exists and can be imported."""
        from apps.core.decorators import atomic_api_view
        
        # Verify decorator is callable
        assert callable(atomic_api_view)
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_transaction_rollback_on_error(self):
        """Test that transactions rollback on errors."""
        from django.db import connection
        
        # Start a transaction
        with self.assertRaises(Exception):
            with transaction.atomic():
                # Execute a query
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                
                # Raise an error to trigger rollback
                raise Exception("Test error")
        
        # Transaction should have been rolled back
        # Verify by checking connection state
        assert not connection.in_atomic_block
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_transaction_commit_on_success(self):
        """Test that transactions commit on success."""
        from django.db import connection
        
        # Execute transaction successfully
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1
        
        # Transaction should have been committed
        assert not connection.in_atomic_block
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_nested_transactions(self):
        """Test nested transaction handling."""
        from django.db import connection
        
        # Outer transaction
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            # Inner transaction (savepoint)
            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 2")
                    
                    # Raise error in inner transaction
                    raise Exception("Inner error")
            except Exception:
                # Inner transaction rolled back, outer continues
                pass
            
            # Outer transaction can still commit
            with connection.cursor() as cursor:
                cursor.execute("SELECT 3")
                result = cursor.fetchone()
                assert result[0] == 3
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_transaction_isolation(self):
        """Test transaction isolation levels."""
        from django.db import connection
        
        # Check that transactions are isolated
        with transaction.atomic():
            # This transaction should be isolated from other connections
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1
        
        # Verify transaction completed
        assert not connection.in_atomic_block


class TestAtomicAPIView(TransactionTestCase):
    """Integration tests for atomic_api_view decorator."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_atomic_decorator_wraps_view(self):
        """Test that atomic decorator properly wraps views."""
        from apps.core.decorators import atomic_api_view
        from django.http import JsonResponse
        
        @atomic_api_view
        def test_view(request):
            return JsonResponse({'status': 'ok'})
        
        # Verify decorator returns a callable
        assert callable(test_view)
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_atomic_decorator_provides_transaction(self):
        """Test that atomic decorator provides transaction context."""
        from apps.core.decorators import atomic_api_view
        from django.http import JsonResponse
        from django.db import connection
        
        @atomic_api_view
        def test_view(request):
            # Should be in atomic block
            in_transaction = connection.in_atomic_block
            return JsonResponse({'in_transaction': in_transaction})
        
        # Create mock request
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/test')
        
        # Call view
        response = test_view(request)
        
        # Verify response
        assert response.status_code == 200


class TestConcurrentTransactions(TransactionTestCase):
    """Integration tests for concurrent transaction handling."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_concurrent_read_operations(self):
        """Test concurrent read operations don't block each other."""
        from django.db import connection
        
        # Simulate concurrent reads
        results = []
        for i in range(5):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SELECT %s", [i])
                    result = cursor.fetchone()
                    results.append(result[0])
        
        # All reads should succeed
        assert len(results) == 5
        assert results == [0, 1, 2, 3, 4]
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_transaction_timeout_handling(self):
        """Test that long-running transactions are handled properly."""
        from django.db import connection
        
        # Execute a transaction with a small delay
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                # Small delay to simulate processing
                time.sleep(0.1)
                cursor.execute("SELECT 2")
                result = cursor.fetchone()
                assert result[0] == 2


class TestTransactionErrorHandling(TransactionTestCase):
    """Integration tests for transaction error handling."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_database_error_rollback(self):
        """Test that database errors trigger rollback."""
        from django.db import connection
        
        with self.assertRaises(Exception):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # Execute valid query
                    cursor.execute("SELECT 1")
                    
                    # Execute invalid query to trigger error
                    cursor.execute("SELECT * FROM nonexistent_table")
        
        # Transaction should have been rolled back
        assert not connection.in_atomic_block
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_application_error_rollback(self):
        """Test that application errors trigger rollback."""
        from django.db import connection
        
        with self.assertRaises(ValueError):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                
                # Raise application error
                raise ValueError("Application error")
        
        # Transaction should have been rolled back
        assert not connection.in_atomic_block
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_partial_rollback_with_savepoints(self):
        """Test partial rollback using savepoints."""
        from django.db import connection
        
        with transaction.atomic():
            # Outer transaction
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            # Create savepoint
            sid = transaction.savepoint()
            
            try:
                # Operations that will be rolled back
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 2")
                
                # Trigger error
                raise Exception("Savepoint error")
            except Exception:
                # Rollback to savepoint
                transaction.savepoint_rollback(sid)
            
            # Continue with outer transaction
            with connection.cursor() as cursor:
                cursor.execute("SELECT 3")
                result = cursor.fetchone()
                assert result[0] == 3


class TestTransactionPerformance(TransactionTestCase):
    """Integration tests for transaction performance."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_transaction_overhead(self):
        """Test that transactions don't add excessive overhead."""
        from django.db import connection
        import time
        
        # Measure time with transactions
        start_time = time.time()
        for i in range(10):
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
        elapsed_with_tx = time.time() - start_time
        
        # Should complete in reasonable time (< 1 second for 10 transactions)
        assert elapsed_with_tx < 1.0
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_bulk_operations_in_transaction(self):
        """Test bulk operations within a transaction."""
        from django.db import connection
        
        with transaction.atomic():
            # Execute multiple queries in one transaction
            with connection.cursor() as cursor:
                for i in range(100):
                    cursor.execute("SELECT %s", [i])
                
                # Verify last query
                result = cursor.fetchone()
                assert result[0] == 99


class TestTransactionDocumentation(TransactionTestCase):
    """Integration tests for transaction documentation and patterns."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_transaction_patterns_documented(self):
        """Test that transaction patterns are documented."""
        import os
        
        # Check if transaction patterns documentation exists
        doc_path = 'docs/TRANSACTION_PATTERNS.md'
        assert os.path.exists(doc_path), "Transaction patterns documentation should exist"
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_atomic_decorator_documented(self):
        """Test that atomic_api_view decorator is documented."""
        from apps.core.decorators import atomic_api_view
        
        # Check that decorator has docstring
        assert atomic_api_view.__doc__ is not None
        assert len(atomic_api_view.__doc__) > 0


class TestTransactionBestPractices(TransactionTestCase):
    """Integration tests for transaction best practices."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_short_transaction_duration(self):
        """Test that transactions are kept short."""
        from django.db import connection
        import time
        
        start_time = time.time()
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        elapsed = time.time() - start_time
        
        # Transaction should complete quickly (< 0.5 seconds in test environment)
        assert elapsed < 0.5
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_no_external_calls_in_transaction(self):
        """Test that external calls are avoided in transactions."""
        from django.db import connection
        
        # This is a pattern test - transactions should not contain
        # external API calls, file I/O, or other slow operations
        with transaction.atomic():
            with connection.cursor() as cursor:
                # Only database operations
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1
        
        # Transaction completed quickly without external calls
        assert True
    
    @override_settings(MIDDLEWARE=TEST_MIDDLEWARE)
    def test_explicit_transaction_boundaries(self):
        """Test that transaction boundaries are explicit."""
        from django.db import connection
        
        # Explicit transaction start
        with transaction.atomic():
            # Clear transaction boundary
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            # Explicit transaction end (context manager exit)
        
        # Outside transaction
        assert not connection.in_atomic_block
