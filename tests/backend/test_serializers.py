import pytest
from django.contrib.auth.models import User
from rest_framework.serializers import ValidationError
from accounts.serializers import UserRegistrationSerializer, UserLoginSerializer
from tasks.serializers import TaskSerializer
from tests.factories import UserFactory, TaskFactory


@pytest.mark.django_db
class TestUserRegistrationSerializer:

    def test_valid_registration_data(self):
        """Test serializer with valid registration data"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }

        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()

        user = serializer.save()
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')

    def test_password_mismatch(self):
        """Test validation fails when passwords don't match"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'differentpass'
        }

        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert "Passwords don't match" in str(serializer.errors)

    def test_duplicate_username(self):
        """Test validation fails with duplicate username"""
        UserFactory(username='existinguser')

        data = {
            'username': 'existinguser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }

        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'username' in serializer.errors

    def test_invalid_email(self):
        """Test validation fails with invalid email"""
        data = {
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }

        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_missing_required_fields(self):
        """Test validation fails with missing required fields"""
        data = {'username': 'testuser'}

        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        # Email is optional in Django's User model
        assert 'password' in serializer.errors
        assert 'password_confirm' in serializer.errors


@pytest.mark.django_db
class TestUserLoginSerializer:

    def test_valid_login_data(self):
        """Test serializer with valid login credentials"""
        user = UserFactory(username='testuser')
        user.set_password('testpass123')
        user.save()

        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }

        serializer = UserLoginSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['user'] == user

    def test_invalid_credentials(self):
        """Test validation fails with invalid credentials"""
        UserFactory(username='testuser', password='correctpass')

        data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }

        serializer = UserLoginSerializer(data=data)
        assert not serializer.is_valid()
        assert 'Invalid credentials' in str(serializer.errors)

    def test_nonexistent_user(self):
        """Test validation fails with non-existent user"""
        data = {
            'username': 'nonexistent',
            'password': 'somepass'
        }

        serializer = UserLoginSerializer(data=data)
        assert not serializer.is_valid()
        assert 'Invalid credentials' in str(serializer.errors)

    def test_inactive_user(self):
        """Test validation fails with inactive user"""
        user = UserFactory(username='testuser', is_active=False)
        user.set_password('testpass123')
        user.save()

        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }

        serializer = UserLoginSerializer(data=data)
        assert not serializer.is_valid()
        # Django's authenticate() returns None for inactive users, so it shows as invalid credentials
        assert 'Invalid credentials' in str(serializer.errors)

    def test_missing_credentials(self):
        """Test validation fails with missing username or password"""
        data = {'username': 'testuser'}

        serializer = UserLoginSerializer(data=data)
        assert not serializer.is_valid()
        # Field-level validation shows "This field is required" for missing password
        assert 'password' in serializer.errors


@pytest.mark.django_db
class TestTaskSerializer:

    def test_valid_task_serialization(self):
        """Test task serialization with valid data"""
        task = TaskFactory()
        serializer = TaskSerializer(task)

        data = serializer.data
        assert data['id'] == task.id
        assert data['title'] == task.title
        assert data['description'] == task.description
        assert data['completed'] == task.completed
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_valid_task_deserialization(self):
        """Test task creation from serializer data"""
        user = UserFactory()
        data = {
            'title': 'Test Task',
            'description': 'Test description',
            'completed': False
        }

        mock_request = type('MockRequest', (), {'user': user})()
        serializer = TaskSerializer(data=data, context={'request': mock_request})

        assert serializer.is_valid()
        task = serializer.save()

        assert task.title == 'Test Task'
        assert task.description == 'Test description'
        assert task.completed is False
        assert task.user == user

    def test_task_update(self):
        """Test task update through serializer"""
        task = TaskFactory(title="Original Title")
        data = {
            'title': 'Updated Title',
            'completed': True
        }

        serializer = TaskSerializer(task, data=data, partial=True)
        assert serializer.is_valid()

        updated_task = serializer.save()
        assert updated_task.title == 'Updated Title'
        assert updated_task.completed is True

    def test_missing_title_validation(self):
        """Test validation fails without title"""
        data = {
            'description': 'Test description',
            'completed': False
        }

        serializer = TaskSerializer(data=data)
        assert not serializer.is_valid()
        assert 'title' in serializer.errors

    def test_title_max_length_validation(self):
        """Test validation fails with title too long"""
        data = {
            'title': 'x' * 201,  # Exceeds max_length=200
            'description': 'Test description',
            'completed': False
        }

        serializer = TaskSerializer(data=data)
        assert not serializer.is_valid()
        assert 'title' in serializer.errors

    def test_description_optional(self):
        """Test that description field is optional"""
        user = UserFactory()
        data = {
            'title': 'Test Task',
            'completed': False
        }

        mock_request = type('MockRequest', (), {'user': user})()
        serializer = TaskSerializer(data=data, context={'request': mock_request})

        assert serializer.is_valid()
        task = serializer.save()
        assert task.description == ''

    def test_readonly_fields(self):
        """Test that created_at and updated_at are read-only"""
        task = TaskFactory()
        original_created_at = task.created_at

        data = {
            'title': 'Updated Title',
            'created_at': '2020-01-01T00:00:00Z',
            'updated_at': '2020-01-01T00:00:00Z'
        }

        serializer = TaskSerializer(task, data=data, partial=True)
        assert serializer.is_valid()

        updated_task = serializer.save()
        assert updated_task.created_at == original_created_at  # Should not change