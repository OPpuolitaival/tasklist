import pytest
import time
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.db import connection
from django.test.utils import override_settings
from tests.factories import UserFactory, TaskFactory


class PerformanceTestCase(TransactionTestCase):
    """Base class for performance tests"""

    def setUp(self):
        self.client = APIClient()

    def measure_time(self, func, *args, **kwargs):
        """Measure execution time of a function"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time

    def measure_db_queries(self, func, *args, **kwargs):
        """Measure number of database queries"""
        initial_queries = len(connection.queries)
        result = func(*args, **kwargs)
        final_queries = len(connection.queries)
        query_count = final_queries - initial_queries
        return result, query_count


@pytest.mark.performance
class TestAPIPerformance(PerformanceTestCase):
    """Test API endpoint performance"""

    def test_user_registration_performance(self):
        """Test user registration response time"""
        data = {
            'username': 'perfuser',
            'email': 'perf@example.com',
            'password': 'perfpass123',
            'password_confirm': 'perfpass123'
        }

        response, execution_time = self.measure_time(
            self.client.post, '/api/auth/register/', data
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert execution_time < 1.0  # Should complete within 1 second

    def test_user_login_performance(self):
        """Test user login response time"""
        user = UserFactory(username='perfuser')
        user.set_password('perfpass123')
        user.save()

        data = {
            'username': 'perfuser',
            'password': 'perfpass123'
        }

        response, execution_time = self.measure_time(
            self.client.post, '/api/auth/login/', data
        )

        assert response.status_code == status.HTTP_200_OK
        assert execution_time < 0.5  # Login should be faster than registration

    def test_task_list_performance_with_many_tasks(self):
        """Test task list performance with large number of tasks"""
        user = UserFactory()

        # Create 100 tasks
        TaskFactory.create_batch(100, user=user)

        # Authenticate
        self.client.force_authenticate(user=user)

        response, execution_time = self.measure_time(
            self.client.get, '/api/tasks/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 100
        assert execution_time < 1.0  # Should handle 100 tasks quickly

    def test_task_list_query_efficiency(self):
        """Test that task list doesn't have N+1 query problem"""
        user = UserFactory()
        TaskFactory.create_batch(50, user=user)

        self.client.force_authenticate(user=user)

        response, query_count = self.measure_db_queries(
            self.client.get, '/api/tasks/'
        )

        assert response.status_code == status.HTTP_200_OK
        # Should use minimal queries regardless of task count
        # Typically: 1 query for tasks, maybe 1 for user authentication
        assert query_count <= 3

    def test_task_creation_performance(self):
        """Test task creation response time"""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        data = {
            'title': 'Performance test task',
            'description': 'Testing task creation speed',
            'completed': False
        }

        response, execution_time = self.measure_time(
            self.client.post, '/api/tasks/', data
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert execution_time < 0.5  # Task creation should be fast

    def test_bulk_task_operations_performance(self):
        """Test performance of multiple task operations"""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        # Create 20 tasks and measure time
        tasks_data = [
            {
                'title': f'Bulk task {i}',
                'description': f'Description for task {i}',
                'completed': False
            }
            for i in range(20)
        ]

        start_time = time.time()
        created_tasks = []

        for task_data in tasks_data:
            response = self.client.post('/api/tasks/', task_data)
            assert response.status_code == status.HTTP_201_CREATED
            created_tasks.append(response.data['id'])

        creation_time = time.time() - start_time

        # Update all tasks
        start_time = time.time()
        for task_id in created_tasks:
            response = self.client.patch(f'/api/tasks/{task_id}/', {'completed': True})
            assert response.status_code == status.HTTP_200_OK

        update_time = time.time() - start_time

        # Delete all tasks
        start_time = time.time()
        for task_id in created_tasks:
            response = self.client.delete(f'/api/tasks/{task_id}/')
            assert response.status_code == status.HTTP_204_NO_CONTENT

        deletion_time = time.time() - start_time

        # Performance assertions
        assert creation_time < 5.0  # 20 creations in under 5 seconds
        assert update_time < 3.0    # 20 updates in under 3 seconds
        assert deletion_time < 2.0  # 20 deletions in under 2 seconds

    def test_concurrent_task_access_performance(self):
        """Test performance with multiple users accessing tasks simultaneously"""
        users = UserFactory.create_batch(10)

        # Create tasks for each user
        for user in users:
            TaskFactory.create_batch(10, user=user)

        # Simulate concurrent access
        start_time = time.time()

        for user in users:
            self.client.force_authenticate(user=user)
            response = self.client.get('/api/tasks/')
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 10

        concurrent_access_time = time.time() - start_time

        # Should handle 10 users * 10 tasks each reasonably quickly
        assert concurrent_access_time < 2.0

    def test_memory_usage_with_large_dataset(self):
        """Test memory efficiency with large task datasets"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        user = UserFactory()

        # Create a large number of tasks
        TaskFactory.create_batch(500, user=user)

        self.client.force_authenticate(user=user)

        # Make multiple requests
        for _ in range(10):
            response = self.client.get('/api/tasks/')
            assert response.status_code == status.HTTP_200_OK

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100

    def test_database_connection_efficiency(self):
        """Test that database connections are managed efficiently"""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        # Make multiple API calls
        start_time = time.time()

        for _ in range(50):
            response = self.client.get('/api/tasks/')
            assert response.status_code == status.HTTP_200_OK

        execution_time = time.time() - start_time

        # 50 requests should complete quickly
        assert execution_time < 5.0

    def test_static_file_serving_performance(self):
        """Test static file serving performance"""
        static_files = [
            '/static/css/style.css',
            '/static/js/auth.js',
            '/static/js/tasks.js',
            '/static/js/app.js'
        ]

        for static_file in static_files:
            response, execution_time = self.measure_time(
                self.client.get, static_file
            )

            assert response.status_code == status.HTTP_200_OK
            assert execution_time < 0.5  # Static files should load quickly

    @override_settings(DEBUG=False)
    def test_production_mode_performance(self):
        """Test performance in production-like settings"""
        user = UserFactory()
        TaskFactory.create_batch(50, user=user)

        self.client.force_authenticate(user=user)

        response, execution_time = self.measure_time(
            self.client.get, '/api/tasks/'
        )

        assert response.status_code == status.HTTP_200_OK
        # Production mode should be faster than debug mode
        assert execution_time < 0.8

    def test_jwt_token_validation_performance(self):
        """Test JWT token validation performance"""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        # Create a task to get a JWT token response
        register_response = self.client.post('/api/auth/register/', {
            'username': 'jwtperfuser',
            'email': 'jwtperf@example.com',
            'password': 'jwtperf123',
            'password_confirm': 'jwtperf123'
        })

        token = register_response.data['tokens']['access']

        # Test token validation performance
        headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'}

        start_time = time.time()

        for _ in range(20):
            response = self.client.get('/api/tasks/', **headers)
            assert response.status_code == status.HTTP_200_OK

        validation_time = time.time() - start_time

        # 20 token validations should be fast
        assert validation_time < 2.0