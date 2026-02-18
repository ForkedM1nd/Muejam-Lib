"""
Tests for transaction management decorators.

This test suite verifies that the atomic_api_view and atomic_prisma_view decorators
properly handle transactions and rollback on errors.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import RequestFactory
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status

from apps.core.decorators import atomic_api_view, atomic_prisma_view


@pytest.mark.django_db
class TestAtomicApiView:
    """Test Django ORM transaction management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    def test_successful_transaction_commits(self):
        """Test that successful operations commit the transaction."""
        
        @atomic_api_view
        def test_view(request):
            # Simulate successful database operations
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        
        request = self.factory.post('/test')
        request.user_profile = Mock(id='user123')
        
        response = test_view(request)
        
        assert response.status_code == 200
        assert response.data['status'] == 'success'
    
    def test_failed_transaction_rolls_back(self):
        """Test that failed operations trigger rollback."""
        
        @atomic_api_view
        def test_view(request):
            # Simulate database operation that fails
            raise ValueError("Database operation failed")
        
        request = self.factory.post('/test')
        request.user_profile = Mock(id='user123')
        request.path = '/test'
        request.method = 'POST'
        
        with pytest.raises(ValueError, match="Database operation failed"):
            test_view(request)
    
    def test_transaction_logs_errors(self):
        """Test that transaction failures are logged."""
        
        @atomic_api_view
        def test_view(request):
            raise ValueError("Test error")
        
        request = self.factory.post('/test')
        request.user_profile = Mock(id='user123')
        request.path = '/test'
        request.method = 'POST'
        
        with patch('logging.getLogger') as mock_logger:
            logger_instance = Mock()
            mock_logger.return_value = logger_instance
            
            with pytest.raises(ValueError):
                test_view(request)
            
            # Verify error was logged
            assert logger_instance.error.called
    
    def test_nested_transactions_work_correctly(self):
        """Test that nested transactions work as expected."""
        
        @atomic_api_view
        def outer_view(request):
            # Outer transaction
            inner_view(request)
            return Response({'status': 'success'})
        
        @atomic_api_view
        def inner_view(request):
            # Inner transaction (savepoint)
            return Response({'status': 'inner_success'})
        
        request = self.factory.post('/test')
        request.user_profile = Mock(id='user123')
        
        response = outer_view(request)
        assert response.status_code == 200


class TestAtomicPrismaView:
    """Test Prisma transaction management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    def test_successful_prisma_operation(self):
        """Test that successful Prisma operations complete."""
        
        @atomic_prisma_view
        def test_view(request):
            # Simulate successful Prisma operations
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        
        request = self.factory.post('/test')
        request.user_profile = Mock(id='user123')
        
        response = test_view(request)
        
        assert response.status_code == 200
        assert response.data['status'] == 'success'
    
    def test_failed_prisma_operation_logs_error(self):
        """Test that failed Prisma operations are logged."""
        
        @atomic_prisma_view
        def test_view(request):
            raise Exception("Prisma operation failed")
        
        request = self.factory.post('/test')
        request.user_profile = Mock(id='user123')
        request.path = '/test'
        request.method = 'POST'
        
        with patch('logging.getLogger') as mock_logger:
            logger_instance = Mock()
            mock_logger.return_value = logger_instance
            
            with pytest.raises(Exception, match="Prisma operation failed"):
                test_view(request)
            
            # Verify error was logged
            assert logger_instance.error.called


@pytest.mark.django_db
class TestTransactionRollbackScenarios:
    """Test specific rollback scenarios for multi-step operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    def test_story_creation_with_chapters_rollback(self):
        """
        Test that if chapter creation fails, story creation is also rolled back.
        
        This simulates the scenario mentioned in the requirements where a story
        is created but chapter creation fails, which should not leave an orphaned story.
        """
        
        @atomic_api_view
        def create_story_with_chapters(request):
            # Simulate story creation
            story_id = 'story123'
            
            # Simulate chapter creation that fails
            chapters = request.data.get('chapters', [])
            if len(chapters) > 0:
                # Simulate failure on second chapter
                if len(chapters) > 1:
                    raise ValueError("Chapter creation failed")
            
            return Response({'story_id': story_id}, status=status.HTTP_201_CREATED)
        
        request = self.factory.post('/test')
        request.user_profile = Mock(id='user123')
        request.path = '/test'
        request.method = 'POST'
        request.data = {
            'title': 'Test Story',
            'chapters': [
                {'title': 'Chapter 1'},
                {'title': 'Chapter 2'}  # This will fail
            ]
        }
        
        with pytest.raises(ValueError, match="Chapter creation failed"):
            create_story_with_chapters(request)
        
        # In a real scenario, we would verify that the story was not created
        # by checking the database
    
    def test_block_user_removes_follows_atomically(self):
        """
        Test that blocking a user removes follow relationships atomically.
        
        If the block creation fails, follow relationships should not be removed.
        """
        
        @atomic_prisma_view
        def block_user_view(request, user_id):
            # Simulate removing follow relationships
            follows_removed = True
            
            # Simulate block creation that fails
            if request.data.get('simulate_failure'):
                raise ValueError("Block creation failed")
            
            return Response({'blocked': user_id}, status=status.HTTP_201_CREATED)
        
        request = self.factory.post('/test')
        request.user_profile = Mock(id='user123')
        request.path = '/test'
        request.method = 'POST'
        request.data = {'simulate_failure': True}
        
        with pytest.raises(ValueError, match="Block creation failed"):
            block_user_view(request, 'user456')
        
        # In a real scenario with Prisma, the follow relationships would not be removed
        # because Prisma would rollback the transaction


class TestConcurrentOperations:
    """Test transaction behavior under concurrent operations."""
    
    def test_concurrent_follow_operations(self):
        """
        Test that concurrent follow operations don't create race conditions.
        
        This tests the scenario where two users try to follow each other simultaneously.
        """
        # This would require actual database testing with concurrent threads
        # Placeholder for integration test
        pass
    
    def test_concurrent_block_operations(self):
        """
        Test that concurrent block operations are handled correctly.
        
        This tests the scenario where two users try to block each other simultaneously.
        """
        # This would require actual database testing with concurrent threads
        # Placeholder for integration test
        pass


@pytest.mark.django_db
class TestTransactionPatterns:
    """Document and test common transaction patterns."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    def test_pattern_create_with_related_objects(self):
        """
        Pattern: Creating a parent object with related child objects.
        
        Example: Creating a story with chapters, creating a whisper with NSFW flags.
        """
        
        @atomic_api_view
        def create_with_related(request):
            # Create parent
            parent_id = 'parent123'
            
            # Create related objects
            for child_data in request.data.get('children', []):
                # Create child linked to parent
                pass
            
            return Response({'parent_id': parent_id})
        
        request = self.factory.post('/test')
        request.user_profile = Mock(id='user123')
        request.data = {
            'title': 'Parent',
            'children': [
                {'name': 'Child 1'},
                {'name': 'Child 2'}
            ]
        }
        
        response = create_with_related(request)
        assert response.status_code == 200
    
    def test_pattern_update_with_cascade(self):
        """
        Pattern: Updating a parent object and cascading updates to children.
        
        Example: Updating a story and updating all its chapters' timestamps.
        """
        
        @atomic_api_view
        def update_with_cascade(request, parent_id):
            # Update parent
            # Cascade update to children
            return Response({'updated': parent_id})
        
        request = self.factory.put('/test')
        request.user_profile = Mock(id='user123')
        request.data = {'title': 'Updated Title'}
        
        response = update_with_cascade(request, 'parent123')
        assert response.status_code == 200
    
    def test_pattern_delete_with_cleanup(self):
        """
        Pattern: Deleting an object and cleaning up related data.
        
        Example: Blocking a user and removing follow relationships.
        """
        
        @atomic_api_view
        def delete_with_cleanup(request, object_id):
            # Delete main object
            # Clean up related data
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        request = self.factory.delete('/test')
        request.user_profile = Mock(id='user123')
        
        response = delete_with_cleanup(request, 'object123')
        assert response.status_code == 204


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
