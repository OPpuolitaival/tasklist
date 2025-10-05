/**
 * @jest-environment jsdom
 */

// Mock the AuthManager class for testing
// Note: In a real setup, you'd import the actual AuthManager from your static files
class AuthManager {
    constructor() {
        this.baseURL = '/api/auth';
        this.token = localStorage.getItem('access_token');
        this.user = JSON.parse(localStorage.getItem('user')) || null;
    }

    async login(username, password) {
        try {
            const response = await fetch(`${this.baseURL}/login/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            });

            const data = await response.json();

            if (response.ok) {
                this.token = data.tokens.access;
                this.user = data.user;
                localStorage.setItem('access_token', this.token);
                localStorage.setItem('refresh_token', data.tokens.refresh);
                localStorage.setItem('user', JSON.stringify(this.user));
                return { success: true, data };
            } else {
                return { success: false, error: data };
            }
        } catch (error) {
            return { success: false, error: { detail: 'Network error occurred' } };
        }
    }

    async register(username, email, password, passwordConfirm) {
        try {
            const response = await fetch(`${this.baseURL}/register/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username,
                    email,
                    password,
                    password_confirm: passwordConfirm,
                }),
            });

            const data = await response.json();

            if (response.ok) {
                this.token = data.tokens.access;
                this.user = data.user;
                localStorage.setItem('access_token', this.token);
                localStorage.setItem('refresh_token', data.tokens.refresh);
                localStorage.setItem('user', JSON.stringify(this.user));
                return { success: true, data };
            } else {
                return { success: false, error: data };
            }
        } catch (error) {
            return { success: false, error: { detail: 'Network error occurred' } };
        }
    }

    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    }

    isAuthenticated() {
        return !!this.token && !!this.user;
    }

    getAuthHeaders() {
        return {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json',
        };
    }

    getUser() {
        return this.user;
    }
}

describe('AuthManager', () => {
    let authManager;

    beforeEach(() => {
        authManager = new AuthManager();
        jest.clearAllMocks();
    });

    describe('constructor', () => {
        test('should initialize with correct baseURL', () => {
            expect(authManager.baseURL).toBe('/api/auth');
        });

        test('should load token from localStorage', () => {
            localStorage.getItem.mockReturnValue('test-token');
            const auth = new AuthManager();
            expect(auth.token).toBe('test-token');
        });

        test('should load user from localStorage', () => {
            const userData = { id: 1, username: 'testuser' };
            localStorage.getItem.mockReturnValueOnce(null); // token
            localStorage.getItem.mockReturnValueOnce(JSON.stringify(userData)); // user
            const auth = new AuthManager();
            expect(auth.user).toEqual(userData);
        });
    });

    describe('login', () => {
        test('should handle successful login', async () => {
            const mockResponse = {
                user: { id: 1, username: 'testuser', email: 'test@example.com' },
                tokens: { access: 'access-token', refresh: 'refresh-token' }
            };

            fetch.mockResolvedValue({
                ok: true,
                json: jest.fn().mockResolvedValue(mockResponse)
            });

            const result = await authManager.login('testuser', 'password');

            expect(fetch).toHaveBeenCalledWith('/api/auth/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username: 'testuser', password: 'password' }),
            });

            expect(result.success).toBe(true);
            expect(result.data).toEqual(mockResponse);
            expect(authManager.token).toBe('access-token');
            expect(authManager.user).toEqual(mockResponse.user);
            expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'access-token');
            expect(localStorage.setItem).toHaveBeenCalledWith('refresh_token', 'refresh-token');
            expect(localStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify(mockResponse.user));
        });

        test('should handle failed login', async () => {
            const errorResponse = { detail: 'Invalid credentials' };

            fetch.mockResolvedValue({
                ok: false,
                json: jest.fn().mockResolvedValue(errorResponse)
            });

            const result = await authManager.login('testuser', 'wrongpassword');

            expect(result.success).toBe(false);
            expect(result.error).toEqual(errorResponse);
            expect(authManager.token).toBeNull();
            expect(authManager.user).toBeNull();
        });

        test('should handle network error', async () => {
            fetch.mockRejectedValue(new Error('Network error'));

            const result = await authManager.login('testuser', 'password');

            expect(result.success).toBe(false);
            expect(result.error.detail).toBe('Network error occurred');
        });
    });

    describe('register', () => {
        test('should handle successful registration', async () => {
            const mockResponse = {
                user: { id: 1, username: 'newuser', email: 'new@example.com' },
                tokens: { access: 'access-token', refresh: 'refresh-token' }
            };

            fetch.mockResolvedValue({
                ok: true,
                json: jest.fn().mockResolvedValue(mockResponse)
            });

            const result = await authManager.register(
                'newuser',
                'new@example.com',
                'password123',
                'password123'
            );

            expect(fetch).toHaveBeenCalledWith('/api/auth/register/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: 'newuser',
                    email: 'new@example.com',
                    password: 'password123',
                    password_confirm: 'password123',
                }),
            });

            expect(result.success).toBe(true);
            expect(result.data).toEqual(mockResponse);
            expect(authManager.token).toBe('access-token');
            expect(authManager.user).toEqual(mockResponse.user);
        });

        test('should handle registration validation errors', async () => {
            const errorResponse = {
                username: ['This username is already taken.'],
                email: ['Enter a valid email address.']
            };

            fetch.mockResolvedValue({
                ok: false,
                json: jest.fn().mockResolvedValue(errorResponse)
            });

            const result = await authManager.register(
                'existinguser',
                'invalid-email',
                'password123',
                'password123'
            );

            expect(result.success).toBe(false);
            expect(result.error).toEqual(errorResponse);
        });
    });

    describe('logout', () => {
        test('should clear all authentication data', () => {
            authManager.token = 'test-token';
            authManager.user = { id: 1, username: 'testuser' };

            authManager.logout();

            expect(authManager.token).toBeNull();
            expect(authManager.user).toBeNull();
            expect(localStorage.removeItem).toHaveBeenCalledWith('access_token');
            expect(localStorage.removeItem).toHaveBeenCalledWith('refresh_token');
            expect(localStorage.removeItem).toHaveBeenCalledWith('user');
        });
    });

    describe('isAuthenticated', () => {
        test('should return true when both token and user exist', () => {
            authManager.token = 'test-token';
            authManager.user = { id: 1, username: 'testuser' };

            expect(authManager.isAuthenticated()).toBe(true);
        });

        test('should return false when token is missing', () => {
            authManager.token = null;
            authManager.user = { id: 1, username: 'testuser' };

            expect(authManager.isAuthenticated()).toBe(false);
        });

        test('should return false when user is missing', () => {
            authManager.token = 'test-token';
            authManager.user = null;

            expect(authManager.isAuthenticated()).toBe(false);
        });

        test('should return false when both are missing', () => {
            authManager.token = null;
            authManager.user = null;

            expect(authManager.isAuthenticated()).toBe(false);
        });
    });

    describe('getAuthHeaders', () => {
        test('should return correct authorization headers', () => {
            authManager.token = 'test-access-token';

            const headers = authManager.getAuthHeaders();

            expect(headers).toEqual({
                'Authorization': 'Bearer test-access-token',
                'Content-Type': 'application/json',
            });
        });
    });

    describe('getUser', () => {
        test('should return current user', () => {
            const userData = { id: 1, username: 'testuser', email: 'test@example.com' };
            authManager.user = userData;

            expect(authManager.getUser()).toEqual(userData);
        });

        test('should return null when no user', () => {
            authManager.user = null;

            expect(authManager.getUser()).toBeNull();
        });
    });
});