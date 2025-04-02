import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import apiService from '@/services/api'; // Adjust path as needed

interface User {
    username: string;
    // Add other relevant user fields if needed (e.g., email, id)
}

export const useAuthStore = defineStore('auth', () => {
    // --- State ---
    const token = ref<string | null>(localStorage.getItem('authToken'));
    const storedUser = localStorage.getItem('authUser');
    const user = ref<User | null>(storedUser ? JSON.parse(storedUser) : null); // Initialize from localStorage
    const loading = ref(false);
    const error = ref<string | null>(null);

    // --- Getters ---
    const isAuthenticated = computed(() => !!token.value);
    const username = computed(() => user.value?.username || null);

    // --- Actions ---
    async function login(usernameInput: string, passwordInput: string): Promise<void> {
        loading.value = true;
        error.value = null;
        try {
            console.log('AuthStore: Attempting login...');
            const response = await apiService.login(usernameInput, passwordInput);
            token.value = response.access_token;
            user.value = { username: response.username }; // Store username

            // Persist to localStorage
            if (token.value) {
                localStorage.setItem('authToken', token.value);
            } else {
                localStorage.removeItem('authToken'); // Should not happen on success, but safe
            }
            if (user.value) {
                localStorage.setItem('authUser', JSON.stringify(user.value));
            } else {
                 localStorage.removeItem('authUser');
            }

            console.log('AuthStore: Login successful.');
        } catch (err: any) {
            console.error('AuthStore: Login failed:', err);
            token.value = null;
            user.value = null;
            localStorage.removeItem('authToken'); // Ensure removal on error
            localStorage.removeItem('authUser');
            error.value = err.message || 'Login failed. Please check credentials.';
            throw err; // Re-throw for the component to handle
        } finally {
            loading.value = false;
        }
    }

    function logout(): void {
        console.log('AuthStore: Logging out...');
        token.value = null;
        user.value = null;
        error.value = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('authUser');
        // Optionally redirect or clear other stores if needed
        console.log('AuthStore: Logout complete.');
    }

    function checkAuthStatus(): void {
        console.log('AuthStore: Checking auth status from localStorage...');
        const storedToken = localStorage.getItem('authToken');
        const storedUserJson = localStorage.getItem('authUser');

        if (storedToken && storedUserJson) {
            try {
                const parsedUser = JSON.parse(storedUserJson);
                // Basic validation if needed (e.g., check if username exists)
                if (parsedUser && parsedUser.username) {
                    token.value = storedToken;
                    user.value = parsedUser;
                    console.log('AuthStore: Session restored from localStorage.');
                } else {
                    console.warn('AuthStore: Invalid user data in localStorage. Logging out.');
                    logout();
                }
            } catch (e) {
                console.error('AuthStore: Error parsing stored user data. Logging out.');
                logout();
            }
        } else {
            console.log('AuthStore: No token or user found in localStorage.');
            // Ensure state matches localStorage absence
            if (token.value || user.value) {
                logout();
            }
        }
    }

    // Action to get the current token (useful for API service interceptor)
    function getToken(): string | null {
        return token.value;
    }

    return {
        token,
        user,
        loading,
        error,
        isAuthenticated,
        username,
        login,
        logout,
        checkAuthStatus,
        getToken,
    };
});