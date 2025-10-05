class TaskListApp {
    constructor() {
        this.authManager = new AuthManager();
        this.taskManager = new TaskManager(this.authManager);
        this.currentEditingTask = null;

        this.initializeElements();
        this.attachEventListeners();
        this.checkAuthState();
    }

    initializeElements() {
        // Auth elements
        this.loginForm = document.getElementById('login-form');
        this.registerForm = document.getElementById('register-form');
        this.authSection = document.getElementById('auth-section');
        this.taskSection = document.getElementById('task-section');
        this.userInfo = document.getElementById('user-info');
        this.usernameSpan = document.getElementById('username');

        // Forms
        this.loginFormEl = document.getElementById('loginForm');
        this.registerFormEl = document.getElementById('registerForm');
        this.taskFormEl = document.getElementById('taskForm');

        // Task elements
        this.tasksContainer = document.getElementById('tasks-container');
        this.errorMessage = document.getElementById('error-message');
    }

    attachEventListeners() {
        // Auth form switching
        document.getElementById('show-register').addEventListener('click', (e) => {
            e.preventDefault();
            this.showRegisterForm();
        });

        document.getElementById('show-login').addEventListener('click', (e) => {
            e.preventDefault();
            this.showLoginForm();
        });

        // Form submissions
        this.loginFormEl.addEventListener('submit', (e) => this.handleLogin(e));
        this.registerFormEl.addEventListener('submit', (e) => this.handleRegister(e));
        this.taskFormEl.addEventListener('submit', (e) => this.handleTaskSubmit(e));

        // Logout
        document.getElementById('logout-btn').addEventListener('click', () => this.handleLogout());
    }

    showLoginForm() {
        this.loginForm.classList.remove('hidden');
        this.registerForm.classList.add('hidden');
    }

    showRegisterForm() {
        this.registerForm.classList.remove('hidden');
        this.loginForm.classList.add('hidden');
    }

    async handleLogin(e) {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;

        const result = await this.authManager.login(username, password);

        if (result.success) {
            this.showTaskSection();
            await this.loadTasks();
        } else {
            this.showError(this.formatError(result.error));
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        const username = document.getElementById('register-username').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        const passwordConfirm = document.getElementById('register-password-confirm').value;

        const result = await this.authManager.register(username, email, password, passwordConfirm);

        if (result.success) {
            this.showTaskSection();
            await this.loadTasks();
        } else {
            this.showError(this.formatError(result.error));
        }
    }

    async handleTaskSubmit(e) {
        e.preventDefault();
        const title = document.getElementById('task-title').value;
        const description = document.getElementById('task-description').value;

        if (this.currentEditingTask) {
            // Update existing task
            const result = await this.taskManager.updateTask(this.currentEditingTask.id, {
                title,
                description
            });

            if (result.success) {
                this.currentEditingTask = null;
                document.getElementById('taskForm').querySelector('button').textContent = 'Add Task';
                this.taskFormEl.reset();
                this.renderTasks();
            } else {
                this.showError(this.formatError(result.error));
            }
        } else {
            // Create new task
            const result = await this.taskManager.createTask(title, description);

            if (result.success) {
                this.taskFormEl.reset();
                this.renderTasks();
            } else {
                this.showError(this.formatError(result.error));
            }
        }
    }

    handleLogout() {
        this.authManager.logout();
        this.showAuthSection();
        this.tasksContainer.innerHTML = '';
        this.taskManager.tasks = [];
    }

    async loadTasks() {
        const result = await this.taskManager.getTasks();
        if (result.success) {
            this.renderTasks();
        } else {
            this.showError('Failed to load tasks');
        }
    }

    renderTasks() {
        this.tasksContainer.innerHTML = '';

        if (this.taskManager.tasks.length === 0) {
            this.tasksContainer.innerHTML = '<p>No tasks yet. Add your first task above!</p>';
            return;
        }

        this.taskManager.tasks.forEach(task => {
            const taskElement = this.createTaskElement(task);
            this.tasksContainer.appendChild(taskElement);
        });
    }

    createTaskElement(task) {
        const taskDiv = document.createElement('div');
        taskDiv.className = `task-item ${task.completed ? 'completed' : ''}`;

        taskDiv.innerHTML = `
            <div class="task-content">
                <div class="task-title">${this.escapeHtml(task.title)}</div>
                ${task.description ? `<div class="task-description">${this.escapeHtml(task.description)}</div>` : ''}
            </div>
            <div class="task-actions">
                <button class="btn-toggle ${task.completed ? 'completed' : ''}" onclick="app.toggleTask(${task.id})">
                    ${task.completed ? 'Undo' : 'Complete'}
                </button>
                <button class="btn-edit" onclick="app.editTask(${task.id})">Edit</button>
                <button class="btn-delete" onclick="app.deleteTask(${task.id})">Delete</button>
            </div>
        `;

        return taskDiv;
    }

    async toggleTask(id) {
        const result = await this.taskManager.toggleTask(id);
        if (result.success) {
            this.renderTasks();
        } else {
            this.showError('Failed to update task');
        }
    }

    editTask(id) {
        const task = this.taskManager.tasks.find(t => t.id === id);
        if (task) {
            this.currentEditingTask = task;
            document.getElementById('task-title').value = task.title;
            document.getElementById('task-description').value = task.description || '';
            document.getElementById('taskForm').querySelector('button').textContent = 'Update Task';
            document.getElementById('task-title').focus();
        }
    }

    async deleteTask(id) {
        if (confirm('Are you sure you want to delete this task?')) {
            const result = await this.taskManager.deleteTask(id);
            if (result.success) {
                this.renderTasks();
            } else {
                this.showError('Failed to delete task');
            }
        }
    }

    showTaskSection() {
        this.authSection.classList.add('hidden');
        this.taskSection.classList.remove('hidden');
        this.userInfo.classList.remove('hidden');
        this.usernameSpan.textContent = this.authManager.getUser().username;
    }

    showAuthSection() {
        this.taskSection.classList.add('hidden');
        this.userInfo.classList.add('hidden');
        this.authSection.classList.remove('hidden');
        this.showLoginForm();
    }

    checkAuthState() {
        if (this.authManager.isAuthenticated()) {
            this.showTaskSection();
            this.loadTasks();
        } else {
            this.showAuthSection();
        }
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.errorMessage.classList.remove('hidden');
        setTimeout(() => {
            this.errorMessage.classList.add('hidden');
        }, 5000);
    }

    formatError(error) {
        if (typeof error === 'string') {
            return error;
        }

        if (error.detail) {
            return error.detail;
        }

        if (error.non_field_errors && error.non_field_errors.length > 0) {
            return error.non_field_errors[0];
        }

        // Handle field-specific errors
        const fieldErrors = [];
        for (const [field, messages] of Object.entries(error)) {
            if (Array.isArray(messages)) {
                fieldErrors.push(`${field}: ${messages[0]}`);
            }
        }

        return fieldErrors.length > 0 ? fieldErrors.join(', ') : 'An error occurred';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.app = new TaskListApp();
});