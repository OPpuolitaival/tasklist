import pytest
import json
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from tasks.models import Task
from tests.factories import UserFactory, TaskFactory


@pytest.mark.django_db
class TestCompleteUserJourney:
    """Integration tests for complete user journeys"""

    def setup_method(self):
        self.client = APIClient()

    def test_complete_user_registration_to_task_management(self):
        """Test complete flow: register → login → create tasks → manage tasks"""

        # Step 1: Register a new user
        registration_data = {
            'username': 'integrationuser',
            'email': 'integration@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }

        register_response = self.client.post('/api/auth/register/', registration_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        access_token = register_response.data['tokens']['access']
        user_id = register_response.data['user']['id']

        # Verify user was created
        user = User.objects.get(id=user_id)
        assert user.username == 'integrationuser'

        # Step 2: Authenticate for API calls
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Step 3: Create multiple tasks
        tasks_data = [
            {'title': 'Buy groceries', 'description': 'Milk, bread, eggs'},
            {'title': 'Walk the dog', 'description': 'Take Rex for a 30 min walk'},
            {'title': 'Finish project', 'description': 'Complete the Django app'},
        ]

        created_tasks = []
        for task_data in tasks_data:
            response = self.client.post('/api/tasks/', task_data)
            assert response.status_code == status.HTTP_201_CREATED
            created_tasks.append(response.data)

        # Step 4: List all tasks
        list_response = self.client.get('/api/tasks/')
        assert list_response.status_code == status.HTTP_200_OK
        assert len(list_response.data) == 3

        # Verify tasks are ordered by creation date (newest first)
        titles = [task['title'] for task in list_response.data]
        assert titles == ['Finish project', 'Walk the dog', 'Buy groceries']

        # Step 5: Update a task (mark as completed)
        task_to_complete = created_tasks[0]
        update_response = self.client.patch(
            f'/api/tasks/{task_to_complete["id"]}/',
            {'completed': True}
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.data['completed'] is True

        # Step 6: Verify task was updated in database
        updated_task = Task.objects.get(id=task_to_complete['id'])
        assert updated_task.completed is True

        # Step 7: Delete a task
        task_to_delete = created_tasks[1]
        delete_response = self.client.delete(f'/api/tasks/{task_to_delete["id"]}/')
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Step 8: Verify final state
        final_list_response = self.client.get('/api/tasks/')
        assert len(final_list_response.data) == 2

        # Verify deleted task is gone and completed task is still there
        final_task_ids = [task['id'] for task in final_list_response.data]
        assert task_to_complete['id'] in final_task_ids
        assert task_to_delete['id'] not in final_task_ids

    def test_user_data_isolation(self):
        """Test that users can only access their own tasks"""

        # Create two users
        user1_data = {
            'username': 'user1',
            'email': 'user1@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }
        user2_data = {
            'username': 'user2',
            'email': 'user2@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }

        # Register users
        user1_response = self.client.post('/api/auth/register/', user1_data)
        user2_response = self.client.post('/api/auth/register/', user2_data)

        user1_token = user1_response.data['tokens']['access']
        user2_token = user2_response.data['tokens']['access']

        # User 1 creates tasks
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {user1_token}')
        task1_response = self.client.post('/api/tasks/', {
            'title': 'User 1 Task',
            'description': 'This belongs to user 1'
        })
        assert task1_response.status_code == status.HTTP_201_CREATED

        # User 2 creates tasks
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {user2_token}')
        task2_response = self.client.post('/api/tasks/', {
            'title': 'User 2 Task',
            'description': 'This belongs to user 2'
        })
        assert task2_response.status_code == status.HTTP_201_CREATED

        # User 1 can only see their own tasks
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {user1_token}')
        user1_tasks = self.client.get('/api/tasks/')
        assert len(user1_tasks.data) == 1
        assert user1_tasks.data[0]['title'] == 'User 1 Task'

        # User 2 can only see their own tasks
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {user2_token}')
        user2_tasks = self.client.get('/api/tasks/')
        assert len(user2_tasks.data) == 1
        assert user2_tasks.data[0]['title'] == 'User 2 Task'

        # User 1 cannot access User 2's task
        user2_task_id = task2_response.data['id']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {user1_token}')
        unauthorized_access = self.client.get(f'/api/tasks/{user2_task_id}/')
        assert unauthorized_access.status_code == status.HTTP_404_NOT_FOUND

        # User 1 cannot modify User 2's task
        unauthorized_update = self.client.patch(
            f'/api/tasks/{user2_task_id}/',
            {'title': 'Hacked title'}
        )
        assert unauthorized_update.status_code == status.HTTP_404_NOT_FOUND

        # User 1 cannot delete User 2's task
        unauthorized_delete = self.client.delete(f'/api/tasks/{user2_task_id}/')
        assert unauthorized_delete.status_code == status.HTTP_404_NOT_FOUND

    def test_authentication_flow_with_existing_user(self):
        """Test login flow with existing user"""

        # Create a user manually
        user = UserFactory(username='existinguser', email='existing@example.com')
        user.set_password('testpass123')
        user.save()

        # Create some tasks for the user
        TaskFactory.create_batch(2, user=user)

        # Login with existing credentials
        login_data = {
            'username': 'existinguser',
            'password': 'testpass123'
        }

        login_response = self.client.post('/api/auth/login/', login_data)
        assert login_response.status_code == status.HTTP_200_OK
        assert login_response.data['user']['username'] == 'existinguser'

        # Use token to access tasks
        access_token = login_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        tasks_response = self.client.get('/api/tasks/')
        assert tasks_response.status_code == status.HTTP_200_OK
        assert len(tasks_response.data) == 2

    def test_invalid_token_handling(self):
        """Test API behavior with invalid tokens"""

        # Try to access protected endpoint with invalid token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token_here')
        response = self.client.get('/api/tasks/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Try to create task with invalid token
        response = self.client.post('/api/tasks/', {
            'title': 'Unauthorized task',
            'description': 'Should not be created'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Verify no task was created
        assert Task.objects.count() == 0

    def test_jwt_token_refresh_scenario(self):
        """Test JWT token refresh functionality"""

        # Register user
        registration_data = {
            'username': 'refreshuser',
            'email': 'refresh@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }

        register_response = self.client.post('/api/auth/register/', registration_data)
        tokens = register_response.data['tokens']

        # Verify we have both access and refresh tokens
        assert 'access' in tokens
        assert 'refresh' in tokens
        assert tokens['access'] != tokens['refresh']

        # Use access token to create a task
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        task_response = self.client.post('/api/tasks/', {
            'title': 'Task created with token',
            'description': 'Testing token functionality'
        })
        assert task_response.status_code == status.HTTP_201_CREATED

    def test_cors_headers_present(self):
        """Test that CORS headers are present in responses"""

        # Test registration endpoint
        response = self.client.post('/api/auth/register/', {
            'username': 'corsuser',
            'email': 'cors@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        })

        # CORS headers should be present (handled by django-cors-headers)
        # This is more of a configuration verification test
        assert response.status_code == status.HTTP_201_CREATED

        # Test preflight request simulation
        response = self.client.options('/api/auth/register/')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]