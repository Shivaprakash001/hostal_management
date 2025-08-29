// static/js/auth.js
import { BASE_URL } from "./config.js";

export class AuthManager {
    constructor() {
        this.token = localStorage.getItem('auth_token');
        this.username = localStorage.getItem('username');
        this.role = localStorage.getItem('user_role');
    }

    isAuthenticated() {
        return !!this.token;
    }

    isAdmin() {
        return this.role === 'admin';
    }

    async login(username, password) {
        try {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);
            formData.append('grant_type', 'password');

            const response = await fetch(`${BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Login failed');
            }

            const data = await response.json();
            this.token = data.access_token;
            this.username = username;
            
            // Get user info to determine role
            const userInfo = await this.getCurrentUser();
            this.role = userInfo.role;

            // Store in localStorage
            localStorage.setItem('auth_token', this.token);
            localStorage.setItem('username', this.username);
            localStorage.setItem('user_role', this.role);

            return { success: true, user: userInfo };
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, error: error.message };
        }
    }

    async getCurrentUser() {
        try {
            const response = await fetch(`${BASE_URL}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to get user info');
            }

            return await response.json();
        } catch (error) {
            console.error('Get user info error:', error);
            throw error;
        }
    }

    logout() {
        this.token = null;
        this.username = null;
        this.role = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('username');
        localStorage.removeItem('user_role');
    }

    getAuthHeaders() {
        return this.token ? { 'Authorization': `Bearer ${this.token}` } : {};
    }
}

export const authManager = new AuthManager();
