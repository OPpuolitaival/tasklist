class TaskManager {
    constructor(authManager) {
        this.baseURL = '/api/tasks';
        this.authManager = authManager;
        this.tasks = [];
    }

    async getTasks() {
        try {
            const response = await fetch(`${this.baseURL}/`, {
                headers: this.authManager.getAuthHeaders(),
            });

            if (response.ok) {
                this.tasks = await response.json();
                return { success: true, data: this.tasks };
            } else {
                return { success: false, error: await response.json() };
            }
        } catch (error) {
            return { success: false, error: { detail: 'Network error occurred' } };
        }
    }

    async createTask(title, description = '') {
        try {
            const response = await fetch(`${this.baseURL}/`, {
                method: 'POST',
                headers: this.authManager.getAuthHeaders(),
                body: JSON.stringify({ title, description }),
            });

            const data = await response.json();

            if (response.ok) {
                this.tasks.unshift(data);
                return { success: true, data };
            } else {
                return { success: false, error: data };
            }
        } catch (error) {
            return { success: false, error: { detail: 'Network error occurred' } };
        }
    }

    async updateTask(id, updates) {
        try {
            const response = await fetch(`${this.baseURL}/${id}/`, {
                method: 'PATCH',
                headers: this.authManager.getAuthHeaders(),
                body: JSON.stringify(updates),
            });

            const data = await response.json();

            if (response.ok) {
                const index = this.tasks.findIndex(task => task.id === id);
                if (index !== -1) {
                    this.tasks[index] = data;
                }
                return { success: true, data };
            } else {
                return { success: false, error: data };
            }
        } catch (error) {
            return { success: false, error: { detail: 'Network error occurred' } };
        }
    }

    async deleteTask(id) {
        try {
            const response = await fetch(`${this.baseURL}/${id}/`, {
                method: 'DELETE',
                headers: this.authManager.getAuthHeaders(),
            });

            if (response.ok) {
                this.tasks = this.tasks.filter(task => task.id !== id);
                return { success: true };
            } else {
                return { success: false, error: await response.json() };
            }
        } catch (error) {
            return { success: false, error: { detail: 'Network error occurred' } };
        }
    }

    async toggleTask(id) {
        const task = this.tasks.find(task => task.id === id);
        if (task) {
            return await this.updateTask(id, { completed: !task.completed });
        }
        return { success: false, error: { detail: 'Task not found' } };
    }
}