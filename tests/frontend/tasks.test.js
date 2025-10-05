/**
 * @jest-environment jsdom
 */

// Mock TaskManager class for testing
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

describe('TaskManager', () => {
    let taskManager;
    let mockAuthManager;

    beforeEach(() => {
        mockAuthManager = {
            getAuthHeaders: jest.fn().mockReturnValue({
                'Authorization': 'Bearer test-token',
                'Content-Type': 'application/json',
            })
        };

        taskManager = new TaskManager(mockAuthManager);
        jest.clearAllMocks();
    });

    describe('constructor', () => {
        test('should initialize with correct properties', () => {
            expect(taskManager.baseURL).toBe('/api/tasks');
            expect(taskManager.authManager).toBe(mockAuthManager);
            expect(taskManager.tasks).toEqual([]);
        });
    });

    describe('getTasks', () => {
        test('should fetch tasks successfully', async () => {
            const mockTasks = [
                { id: 1, title: 'Task 1', completed: false },
                { id: 2, title: 'Task 2', completed: true }
            ];

            fetch.mockResolvedValue({
                ok: true,
                json: jest.fn().mockResolvedValue(mockTasks)
            });

            const result = await taskManager.getTasks();

            expect(fetch).toHaveBeenCalledWith('/api/tasks/', {
                headers: mockAuthManager.getAuthHeaders()
            });

            expect(result.success).toBe(true);
            expect(result.data).toEqual(mockTasks);
            expect(taskManager.tasks).toEqual(mockTasks);
        });

        test('should handle fetch tasks error', async () => {
            const errorResponse = { detail: 'Authentication failed' };

            fetch.mockResolvedValue({
                ok: false,
                json: jest.fn().mockResolvedValue(errorResponse)
            });

            const result = await taskManager.getTasks();

            expect(result.success).toBe(false);
            expect(result.error).toEqual(errorResponse);
        });

        test('should handle network error', async () => {
            fetch.mockRejectedValue(new Error('Network error'));

            const result = await taskManager.getTasks();

            expect(result.success).toBe(false);
            expect(result.error.detail).toBe('Network error occurred');
        });
    });

    describe('createTask', () => {
        test('should create task successfully', async () => {
            const newTask = { id: 3, title: 'New Task', description: 'Description', completed: false };

            fetch.mockResolvedValue({
                ok: true,
                json: jest.fn().mockResolvedValue(newTask)
            });

            const result = await taskManager.createTask('New Task', 'Description');

            expect(fetch).toHaveBeenCalledWith('/api/tasks/', {
                method: 'POST',
                headers: mockAuthManager.getAuthHeaders(),
                body: JSON.stringify({ title: 'New Task', description: 'Description' })
            });

            expect(result.success).toBe(true);
            expect(result.data).toEqual(newTask);
            expect(taskManager.tasks[0]).toEqual(newTask); // Should be at the beginning
        });

        test('should create task with empty description', async () => {
            const newTask = { id: 3, title: 'New Task', description: '', completed: false };

            fetch.mockResolvedValue({
                ok: true,
                json: jest.fn().mockResolvedValue(newTask)
            });

            const result = await taskManager.createTask('New Task');

            expect(fetch).toHaveBeenCalledWith('/api/tasks/', {
                method: 'POST',
                headers: mockAuthManager.getAuthHeaders(),
                body: JSON.stringify({ title: 'New Task', description: '' })
            });

            expect(result.success).toBe(true);
        });

        test('should handle create task validation error', async () => {
            const errorResponse = { title: ['This field is required.'] };

            fetch.mockResolvedValue({
                ok: false,
                json: jest.fn().mockResolvedValue(errorResponse)
            });

            const result = await taskManager.createTask('');

            expect(result.success).toBe(false);
            expect(result.error).toEqual(errorResponse);
            expect(taskManager.tasks).toEqual([]); // Should remain empty
        });
    });

    describe('updateTask', () => {
        beforeEach(() => {
            taskManager.tasks = [
                { id: 1, title: 'Task 1', completed: false },
                { id: 2, title: 'Task 2', completed: true }
            ];
        });

        test('should update task successfully', async () => {
            const updatedTask = { id: 1, title: 'Updated Task', completed: true };

            fetch.mockResolvedValue({
                ok: true,
                json: jest.fn().mockResolvedValue(updatedTask)
            });

            const result = await taskManager.updateTask(1, { title: 'Updated Task', completed: true });

            expect(fetch).toHaveBeenCalledWith('/api/tasks/1/', {
                method: 'PATCH',
                headers: mockAuthManager.getAuthHeaders(),
                body: JSON.stringify({ title: 'Updated Task', completed: true })
            });

            expect(result.success).toBe(true);
            expect(result.data).toEqual(updatedTask);
            expect(taskManager.tasks[0]).toEqual(updatedTask);
        });

        test('should handle task not found in local array', async () => {
            const updatedTask = { id: 999, title: 'Non-existent Task', completed: true };

            fetch.mockResolvedValue({
                ok: true,
                json: jest.fn().mockResolvedValue(updatedTask)
            });

            const result = await taskManager.updateTask(999, { title: 'Non-existent Task' });

            expect(result.success).toBe(true);
            expect(taskManager.tasks).toHaveLength(2); // Original tasks unchanged
        });

        test('should handle update task error', async () => {
            const errorResponse = { detail: 'Not found' };

            fetch.mockResolvedValue({
                ok: false,
                json: jest.fn().mockResolvedValue(errorResponse)
            });

            const result = await taskManager.updateTask(999, { title: 'Updated' });

            expect(result.success).toBe(false);
            expect(result.error).toEqual(errorResponse);
        });
    });

    describe('deleteTask', () => {
        beforeEach(() => {
            taskManager.tasks = [
                { id: 1, title: 'Task 1', completed: false },
                { id: 2, title: 'Task 2', completed: true }
            ];
        });

        test('should delete task successfully', async () => {
            fetch.mockResolvedValue({
                ok: true
            });

            const result = await taskManager.deleteTask(1);

            expect(fetch).toHaveBeenCalledWith('/api/tasks/1/', {
                method: 'DELETE',
                headers: mockAuthManager.getAuthHeaders()
            });

            expect(result.success).toBe(true);
            expect(taskManager.tasks).toHaveLength(1);
            expect(taskManager.tasks[0].id).toBe(2);
        });

        test('should handle delete task error', async () => {
            const errorResponse = { detail: 'Not found' };

            fetch.mockResolvedValue({
                ok: false,
                json: jest.fn().mockResolvedValue(errorResponse)
            });

            const result = await taskManager.deleteTask(999);

            expect(result.success).toBe(false);
            expect(result.error).toEqual(errorResponse);
            expect(taskManager.tasks).toHaveLength(2); // Tasks unchanged
        });
    });

    describe('toggleTask', () => {
        beforeEach(() => {
            taskManager.tasks = [
                { id: 1, title: 'Task 1', completed: false },
                { id: 2, title: 'Task 2', completed: true }
            ];
        });

        test('should toggle task completion status', async () => {
            const toggledTask = { id: 1, title: 'Task 1', completed: true };

            fetch.mockResolvedValue({
                ok: true,
                json: jest.fn().mockResolvedValue(toggledTask)
            });

            const result = await taskManager.toggleTask(1);

            expect(fetch).toHaveBeenCalledWith('/api/tasks/1/', {
                method: 'PATCH',
                headers: mockAuthManager.getAuthHeaders(),
                body: JSON.stringify({ completed: true })
            });

            expect(result.success).toBe(true);
            expect(result.data).toEqual(toggledTask);
        });

        test('should handle task not found locally', async () => {
            const result = await taskManager.toggleTask(999);

            expect(result.success).toBe(false);
            expect(result.error.detail).toBe('Task not found');
            expect(fetch).not.toHaveBeenCalled();
        });
    });
});