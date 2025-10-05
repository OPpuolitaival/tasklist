import pytest
from django.db import IntegrityError
from django.contrib.auth.models import User
from tasks.models import Task
from tests.factories import UserFactory, TaskFactory


@pytest.mark.django_db
class TestTaskModel:

    def test_task_creation(self):
        """Test basic task creation"""
        user = UserFactory()
        task = TaskFactory(
            title="Test Task",
            description="Test description",
            user=user
        )

        assert task.title == "Test Task"
        assert task.description == "Test description"
        assert task.user == user
        assert task.completed is False
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_task_str_representation(self):
        """Test task string representation"""
        task = TaskFactory(title="Sample Task")
        assert str(task) == "Sample Task"

    def test_task_ordering(self):
        """Test tasks are ordered by creation date (newest first)"""
        user = UserFactory()
        task1 = TaskFactory(user=user, title="First Task")
        task2 = TaskFactory(user=user, title="Second Task")
        task3 = TaskFactory(user=user, title="Third Task")

        tasks = Task.objects.all()
        assert tasks[0] == task3  # Newest first
        assert tasks[1] == task2
        assert tasks[2] == task1

    def test_task_user_relationship(self):
        """Test user-task relationship"""
        user = UserFactory()
        task1 = TaskFactory(user=user)
        task2 = TaskFactory(user=user)

        assert task1 in user.tasks.all()
        assert task2 in user.tasks.all()
        assert user.tasks.count() == 2

    def test_task_deletion_on_user_deletion(self):
        """Test cascade deletion when user is deleted"""
        user = UserFactory()
        task = TaskFactory(user=user)
        task_id = task.id

        user.delete()

        with pytest.raises(Task.DoesNotExist):
            Task.objects.get(id=task_id)

    def test_task_completed_default(self):
        """Test that completed defaults to False"""
        task = TaskFactory()
        assert task.completed is False

    def test_task_title_max_length(self):
        """Test task title max length constraint"""
        user = UserFactory()
        long_title = "x" * 201  # Exceeds max_length=200

        task = Task(title=long_title, user=user)
        with pytest.raises(Exception):  # ValidationError or database error
            task.full_clean()

    def test_task_description_can_be_empty(self):
        """Test that task description can be empty"""
        user = UserFactory()
        task = Task(title="Test", description="", user=user)
        task.save()

        assert task.description == ""

    def test_task_without_user_fails(self):
        """Test that task cannot exist without a user"""
        with pytest.raises(IntegrityError):
            Task.objects.create(title="Test Task")

    def test_multiple_users_tasks_isolation(self):
        """Test that tasks are isolated per user"""
        user1 = UserFactory(username="user1")
        user2 = UserFactory(username="user2")

        task1 = TaskFactory(user=user1, title="User 1 Task")
        task2 = TaskFactory(user=user2, title="User 2 Task")

        assert task1 in user1.tasks.all()
        assert task1 not in user2.tasks.all()
        assert task2 in user2.tasks.all()
        assert task2 not in user1.tasks.all()

        assert user1.tasks.count() == 1
        assert user2.tasks.count() == 1