import pytest
import json
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from tasks.models import Task
from tests.factories import UserFactory, TaskFactory


@pytest.mark.django_db
class TestAuthenticationViews:

    def setup_method(self):
        self.client = APIClient()

    def test_user_registration_success(self):
        """Test successful user registration"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }

        response = self.client.post('/api/auth/register/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'tokens' in response.data
        assert response.data['user']['username'] == 'newuser'
        assert response.data['user']['email'] == 'newuser@example.com'
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']

        # Verify user was created
        user = User.objects.get(username='newuser')
        assert user.email == 'newuser@example.com'
        assert user.check_password('testpass123')

    def test_user_registration_invalid_data(self):
        """Test registration with invalid data"""
        data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password': 'testpass123',
            'password_confirm': 'different-pass'
        }

        response = self.client.post('/api/auth/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data or 'non_field_errors' in response.data

    def test_user_login_success(self):
        """Test successful user login"""
        user = UserFactory(username='testuser')
        user.set_password('testpass123')
        user.save()

        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }

        response = self.client.post('/api/auth/login/', data)

        assert response.status_code == status.HTTP_200_OK
        assert 'user' in response.data
        assert 'tokens' in response.data
        assert response.data['user']['username'] == 'testuser'
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']

    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        user = UserFactory(username='testuser')
        user.set_password('testpass123')
        user.save()

        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }

        response = self.client.post('/api/auth/login/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_login_missing_data(self):
        """Test login with missing data"""
        data = {'username': 'testuser'}

        response = self.client.post('/api/auth/login/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTaskViews:

    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory()
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def authenticate(self):
        """Helper method to authenticate requests"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_list_tasks_authenticated(self):
        """Test listing tasks for authenticated user"""
        TaskFactory.create_batch(3, user=self.user)
        other_user = UserFactory()
        TaskFactory.create_batch(2, user=other_user)  # Should not appear

        self.authenticate()
        response = self.client.get('/api/tasks/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        for task_data in response.data:
            # Verify all tasks belong to the authenticated user
            task = Task.objects.get(id=task_data['id'])
            assert task.user == self.user

    def test_list_tasks_unauthenticated(self):
        """Test listing tasks without authentication"""
        response = self.client.get('/api/tasks/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_task_authenticated(self):
        """Test creating a task when authenticated"""
        data = {
            'title': 'New Task',
            'description': 'Task description',
            'completed': False
        }

        self.authenticate()
        response = self.client.post('/api/tasks/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'New Task'
        assert response.data['description'] == 'Task description'
        assert response.data['completed'] is False

        # Verify task was created and assigned to user
        task = Task.objects.get(id=response.data['id'])
        assert task.user == self.user

    def test_create_task_unauthenticated(self):
        """Test creating a task without authentication"""
        data = {
            'title': 'New Task',
            'description': 'Task description'
        }

        response = self.client.post('/api/tasks/', data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_task_invalid_data(self):
        """Test creating a task with invalid data"""
        data = {}  # Missing required title

        self.authenticate()
        response = self.client.post('/api/tasks/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'title' in response.data

    def test_retrieve_task_owner(self):
        """Test retrieving a task by its owner"""
        task = TaskFactory(user=self.user)

        self.authenticate()
        response = self.client.get(f'/api/tasks/{task.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == task.id
        assert response.data['title'] == task.title

    def test_retrieve_task_not_owner(self):
        """Test retrieving a task not owned by user"""
        other_user = UserFactory()
        task = TaskFactory(user=other_user)

        self.authenticate()
        response = self.client.get(f'/api/tasks/{task.id}/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_task_owner(self):
        """Test updating a task by its owner"""
        task = TaskFactory(user=self.user, title="Original Title")

        data = {
            'title': 'Updated Title',
            'completed': True
        }

        self.authenticate()
        response = self.client.patch(f'/api/tasks/{task.id}/', data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Title'
        assert response.data['completed'] is True

        # Verify database was updated
        task.refresh_from_db()
        assert task.title == 'Updated Title'
        assert task.completed is True

    def test_update_task_not_owner(self):
        """Test updating a task not owned by user"""
        other_user = UserFactory()
        task = TaskFactory(user=other_user)

        data = {'title': 'Hacked Title'}

        self.authenticate()
        response = self.client.patch(f'/api/tasks/{task.id}/', data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Verify task was not modified
        task.refresh_from_db()
        assert task.title != 'Hacked Title'

    def test_delete_task_owner(self):
        """Test deleting a task by its owner"""
        task = TaskFactory(user=self.user)
        task_id = task.id

        self.authenticate()
        response = self.client.delete(f'/api/tasks/{task_id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify task was deleted
        with pytest.raises(Task.DoesNotExist):
            Task.objects.get(id=task_id)

    def test_delete_task_not_owner(self):
        """Test deleting a task not owned by user"""
        other_user = UserFactory()
        task = TaskFactory(user=other_user)
        task_id = task.id

        self.authenticate()
        response = self.client.delete(f'/api/tasks/{task_id}/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Verify task was not deleted
        assert Task.objects.filter(id=task_id).exists()

    def test_task_ordering(self):
        """Test tasks are returned in correct order (newest first)"""
        task1 = TaskFactory(user=self.user, title="First")
        task2 = TaskFactory(user=self.user, title="Second")
        task3 = TaskFactory(user=self.user, title="Third")

        self.authenticate()
        response = self.client.get('/api/tasks/')

        assert response.status_code == status.HTTP_200_OK
        titles = [task['title'] for task in response.data]
        assert titles == ["Third", "Second", "First"]  # Newest first