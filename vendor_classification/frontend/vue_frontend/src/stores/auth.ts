import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import apiService from '@/services/api'; // Adjust path as needed

interface User {
    username: string;
}

export const useAuthStore = defineStore('auth', () => {
    // --- State ---
    const token = ref<string | null>(localStorage.getItem('authToken'));
    const storedUser = localStorage.getItem('authUser');
    const user = ref<User | null>(storedUser ? JSON.parse(storedUser) : null);
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
            user.value = { username: response.username };

            // --- FIX: Handle null token for localStorage ---
            if (token.value) {
                localStorage.setItem('authToken', token.value);
            } else {
                localStorage.removeItem('authToken'); // Remove if token is null/undefined
            }
            // --- END FIX ---

            // Store user object safely
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
            localStorage.removeItem('authUser'); // Ensure removal on error
            error.value = err.message || 'Login failed. Please check credentials.';
            throw err;
        } finally {
            loading.value = false;
        }
    }

    function logout(): void {
        console.log('AuthStore: Logging out...');
        token.value = null;
        user.value = null;
        error.value = null;
        // --- FIX: Explicitly remove items ---
        localStorage.removeItem('authToken');
        localStorage.removeItem('authUser');
        // --- END FIX ---
        console.log('AuthStore: Logout complete.');
    }

    function checkAuthStatus(): void {
        console.log('AuthStore: Checking auth status from localStorage...');
        const storedToken = localStorage.getItem('authToken');
        const storedUserJson = localStorage.getItem('authUser');

        if (storedToken && storedUserJson) {
            try {
                token.value = storedToken;
                user.value = JSON.parse(storedUserJson);
                console.log('AuthStore: Found valid token and user in localStorage.');
            } catch (e) {
                console.error('AuthStore: Error parsing stored user data. Logging out.');
                logout();
            }
        } else {
            console.log('AuthStore: No token or user found in localStorage.');
            if (token.value || user.value) {
                logout(); // Ensure state is cleared if localStorage is missing items
            }
        }
    }

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