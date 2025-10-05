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