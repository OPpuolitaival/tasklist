from locust import HttpUser, task, between
import json
import random


class TaskListUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        """Called when a simulated user starts"""
        self.user_id = random.randint(1000, 9999)
        self.username = f"loadtest_user_{self.user_id}"
        self.email = f"loadtest_{self.user_id}@example.com"
        self.password = "loadtest123"
        self.access_token = None
        self.tasks_created = []

        # Register and login
        self.register_user()
        self.login_user()

    def register_user(self):
        """Register a new user for load testing"""
        response = self.client.post("/api/auth/register/", json={
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "password_confirm": self.password
        })

        if response.status_code == 201:
            data = response.json()
            self.access_token = data["tokens"]["access"]
        else:
            print(f"Registration failed: {response.status_code} - {response.text}")

    def login_user(self):
        """Login user if registration failed (user might already exist)"""
        if not self.access_token:
            response = self.client.post("/api/auth/login/", json={
                "username": self.username,
                "password": self.password
            })

            if response.status_code == 200:
                data = response.json()
                self.access_token = data["tokens"]["access"]
            else:
                print(f"Login failed: {response.status_code} - {response.text}")

    def get_auth_headers(self):
        """Get authorization headers"""
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}

    @task(3)
    def view_homepage(self):
        """Load the main application page"""
        self.client.get("/")

    @task(5)
    def list_tasks(self):
        """Get user's tasks"""
        self.client.get("/api/tasks/", headers=self.get_auth_headers())

    @task(2)
    def create_task(self):
        """Create a new task"""
        task_titles = [
            "Buy groceries",
            "Walk the dog",
            "Finish project",
            "Call dentist",
            "Fix car",
            "Read book",
            "Exercise",
            "Cook dinner",
            "Clean house",
            "Pay bills"
        ]

        task_descriptions = [
            "Remember to check the list twice",
            "Don't forget to bring water",
            "Need to complete by deadline",
            "Schedule for next week",
            "Get estimate first",
            "Chapter 5-8",
            "30 minutes minimum",
            "Try the new recipe",
            "Focus on living room",
            "Due by end of month"
        ]

        response = self.client.post("/api/tasks/",
            json={
                "title": random.choice(task_titles),
                "description": random.choice(task_descriptions),
                "completed": False
            },
            headers=self.get_auth_headers()
        )

        if response.status_code == 201:
            task_data = response.json()
            self.tasks_created.append(task_data["id"])

    @task(2)
    def update_task(self):
        """Update an existing task"""
        if not self.tasks_created:
            return

        task_id = random.choice(self.tasks_created)
        updates = {}

        # Randomly choose what to update
        if random.choice([True, False]):
            updates["completed"] = random.choice([True, False])

        if random.choice([True, False]):
            updates["title"] = f"Updated task {random.randint(1, 100)}"

        if updates:
            self.client.patch(f"/api/tasks/{task_id}/",
                json=updates,
                headers=self.get_auth_headers()
            )

    @task(1)
    def delete_task(self):
        """Delete a task"""
        if not self.tasks_created:
            return

        task_id = self.tasks_created.pop(random.randint(0, len(self.tasks_created) - 1))
        self.client.delete(f"/api/tasks/{task_id}/",
            headers=self.get_auth_headers()
        )

    @task(1)
    def view_specific_task(self):
        """View a specific task"""
        if not self.tasks_created:
            return

        task_id = random.choice(self.tasks_created)
        self.client.get(f"/api/tasks/{task_id}/",
            headers=self.get_auth_headers()
        )


class AnonymousUser(HttpUser):
    """Simulate users who visit the site but don't register"""
    wait_time = between(2, 8)

    @task(5)
    def view_homepage(self):
        """Load the main page"""
        self.client.get("/")

    @task(2)
    def load_css(self):
        """Load CSS file"""
        self.client.get("/static/css/style.css")

    @task(2)
    def load_js_auth(self):
        """Load auth.js file"""
        self.client.get("/static/js/auth.js")

    @task(2)
    def load_js_tasks(self):
        """Load tasks.js file"""
        self.client.get("/static/js/tasks.js")

    @task(2)
    def load_js_app(self):
        """Load app.js file"""
        self.client.get("/static/js/app.js")

    @task(1)
    def attempt_unauthorized_access(self):
        """Try to access protected endpoints without authentication"""
        # This should return 401 Unauthorized
        self.client.get("/api/tasks/")


class HeavyUser(HttpUser):
    """Simulate power users who create many tasks"""
    wait_time = between(0.5, 2)

    def on_start(self):
        self.user_id = random.randint(10000, 99999)
        self.username = f"heavy_user_{self.user_id}"
        self.email = f"heavy_{self.user_id}@example.com"
        self.password = "heavyload123"
        self.access_token = None
        self.tasks_created = []

        # Register and login
        self.register_user()
        self.login_user()

    def register_user(self):
        response = self.client.post("/api/auth/register/", json={
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "password_confirm": self.password
        })

        if response.status_code == 201:
            data = response.json()
            self.access_token = data["tokens"]["access"]

    def login_user(self):
        if not self.access_token:
            response = self.client.post("/api/auth/login/", json={
                "username": self.username,
                "password": self.password
            })

            if response.status_code == 200:
                data = response.json()
                self.access_token = data["tokens"]["access"]

    def get_auth_headers(self):
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}

    @task(10)
    def rapid_task_creation(self):
        """Create tasks rapidly"""
        for i in range(3):  # Create 3 tasks per call
            response = self.client.post("/api/tasks/",
                json={
                    "title": f"Heavy task {random.randint(1, 1000)}",
                    "description": f"Batch created task {i}",
                    "completed": False
                },
                headers=self.get_auth_headers()
            )

            if response.status_code == 201:
                task_data = response.json()
                self.tasks_created.append(task_data["id"])

    @task(5)
    def bulk_task_updates(self):
        """Update multiple tasks"""
        if len(self.tasks_created) < 3:
            return

        # Update multiple tasks in quick succession
        for task_id in random.sample(self.tasks_created, min(3, len(self.tasks_created))):
            self.client.patch(f"/api/tasks/{task_id}/",
                json={"completed": random.choice([True, False])},
                headers=self.get_auth_headers()
            )

    @task(3)
    def frequent_list_refresh(self):
        """Frequently refresh task list"""
        self.client.get("/api/tasks/", headers=self.get_auth_headers())