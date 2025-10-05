# Django Task List Application

A simple task list application built with Django REST Framework backend and pure JavaScript frontend.

## Features

- User registration and authentication
- JWT token-based API authentication
- Create, read, update, and delete tasks
- Mark tasks as complete/incomplete
- Pure JavaScript frontend (no frameworks)
- Responsive design

## Setup

1. Install dependencies:
   ```bash
   pip install -e .
   ```

2. Run database migrations:
   ```bash
   python manage.py migrate
   ```

3. Start the development server:
   ```bash
   python manage.py runserver
   ```

4. Open http://127.0.0.1:8000 in your browser

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login

### Tasks
- `GET /api/tasks/` - List user's tasks
- `POST /api/tasks/` - Create a new task
- `GET /api/tasks/{id}/` - Get a specific task
- `PATCH /api/tasks/{id}/` - Update a task
- `DELETE /api/tasks/{id}/` - Delete a task

## Project Structure

- `tasklist_project/` - Django project settings
- `accounts/` - User authentication app
- `tasks/` - Task management app
- `static/` - Frontend files (HTML, CSS, JavaScript)

## Usage

1. Register a new account or login with existing credentials
2. Add new tasks using the form
3. Mark tasks as complete by clicking the "Complete" button
4. Edit tasks by clicking the "Edit" button
5. Delete tasks by clicking the "Delete" button