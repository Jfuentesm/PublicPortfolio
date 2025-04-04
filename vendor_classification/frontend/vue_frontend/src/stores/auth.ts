// frontend/vue_frontend/src/stores/auth.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import apiService from '@/services/api'; // Adjust path as needed
import type { UserResponse } from '@/services/api'; // Import the UserResponse type

// Use the imported UserResponse interface directly
// interface User {
//     username: string;
//     email: string;
//     id: string; // Use string for UUID compatibility
//     is_active: boolean;
//     is_superuser: boolean;
//     full_name: string | null;
//     created_at: string;
//     updated_at: string;
// }

export const useAuthStore = defineStore('auth', () => {
    // --- State ---
    const token = ref<string | null>(localStorage.getItem('authToken'));
    // Use UserResponse type for user state
    const user = ref<UserResponse | null>(null);
    const loading = ref(false);
    const error = ref<string | null>(null);

    // --- Getters ---
    const isAuthenticated = computed(() => !!token.value && !!user.value); // Check user too
    const username = computed(() => user.value?.username || null);
    const isSuperuser = computed(() => user.value?.is_superuser || false); // Getter for superuser status

    // --- Actions ---
    async function login(usernameInput: string, passwordInput: string): Promise<void> {
        loading.value = true;
        error.value = null;
        try {
            console.log('AuthStore: Attempting login...');
            // API now returns user details in 'user' field
            const response = await apiService.login(usernameInput, passwordInput);
            token.value = response.access_token;
            user.value = response.user; // Store the full user object

            // Persist to localStorage
            if (token.value) {
                localStorage.setItem('authToken', token.value);
            } else {
                localStorage.removeItem('authToken');
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
            localStorage.removeItem('authToken');
            localStorage.removeItem('authUser');
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
        localStorage.removeItem('authToken');
        localStorage.removeItem('authUser');
        // Optionally redirect or clear other stores if needed
        console.log('AuthStore: Logout complete.');
            // Reload to ensure clean state, especially if routing depends on auth
            window.location.reload();
    }

    function checkAuthStatus(): void {
        console.log('AuthStore: Checking auth status from localStorage...');
        const storedToken = localStorage.getItem('authToken');
        const storedUserJson = localStorage.getItem('authUser');

        if (storedToken && storedUserJson) {
            try {
                const parsedUser: UserResponse = JSON.parse(storedUserJson);
                // Basic validation
                if (parsedUser && parsedUser.id && parsedUser.username) {
                    token.value = storedToken;
                    user.value = parsedUser;
                    console.log('AuthStore: Session restored from localStorage.');
                } else {
                    console.warn('AuthStore: Invalid user data in localStorage. Logging out.');
                    logout(); // Call logout to clear everything
                }
            } catch (e) {
                console.error('AuthStore: Error parsing stored user data. Logging out.');
                logout(); // Call logout to clear everything
            }
        } else {
            console.log('AuthStore: No token or user found in localStorage.');
            // Ensure state matches localStorage absence
            if (token.value || user.value) {
                token.value = null;
                user.value = null;
                error.value = null; // Clear any lingering errors
            }
        }
    }

    // Action to get the current token (useful for API service interceptor)
    function getToken(): string | null {
        return token.value;
    }

    // --- ADDED: Action to fetch user details (e.g., after login or on refresh) ---
    async function fetchCurrentUserDetails(): Promise<void> {
            if (!isAuthenticated.value) {
                console.log("AuthStore: Not authenticated, cannot fetch user details.");
                return;
            }
            loading.value = true;
            error.value = null;
            try {
                console.log("AuthStore: Fetching current user details...");
                const currentUserDetails = await apiService.getCurrentUser(); // Assuming apiService has this
                user.value = currentUserDetails;
                localStorage.setItem('authUser', JSON.stringify(user.value)); // Update local storage
                console.log("AuthStore: Current user details updated.", currentUserDetails);
            } catch (err: any) {
                console.error("AuthStore: Failed to fetch current user details:", err);
                error.value = err.message || "Failed to load user details.";
                // Optional: Logout if fetching user details fails?
                // logout();
            } finally {
                loading.value = false;
            }
        }


    return {
        token,
        user,
        loading,
        error,
        isAuthenticated,
        username,
        isSuperuser, // Expose the new getter
        login,
        logout,
        checkAuthStatus,
        getToken,
        fetchCurrentUserDetails, // Expose the new action
    };
});
