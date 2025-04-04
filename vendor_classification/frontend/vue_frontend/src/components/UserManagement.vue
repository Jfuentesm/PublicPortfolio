<template>
    <div class="bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
    <div class="bg-gray-100 text-gray-800 p-4 sm:p-5 border-b border-gray-200 flex justify-between items-center">
        <h4 class="text-xl font-semibold mb-0">User Management</h4>
        <button
        @click="openCreateModal"
        class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
        >
        <PlusIcon class="h-5 w-5 mr-2 -ml-1" />
        Create User
        </button>
    </div>

    <div class="p-6 sm:p-8">
        <!-- Loading State -->
        <div v-if="isLoading" class="text-center text-gray-500 py-8">
        <svg class="animate-spin inline-block h-6 w-6 text-primary mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>Loading users...</span>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="p-4 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm flex items-center">
        <ExclamationTriangleIcon class="h-5 w-5 mr-2 text-red-600 flex-shrink-0"/>
        <span>Error loading users: {{ error }}</span>
        </div>

        <!-- Empty State -->
        <div v-else-if="!users || users.length === 0" class="text-center text-gray-500 py-8">
        <p>No users found.</p>
        <p class="text-sm">Click 'Create User' to add the first user.</p>
        </div>

        <!-- User Table -->
        <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
            <tr>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Username</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Full Name</th>
                <th scope="col" class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Active</th>
                <th scope="col" class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Admin</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                <th scope="col" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50">
                <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{{ user.username }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{{ user.email }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600">{{ user.full_name || '-' }}</td>
                <td class="px-4 py-3 whitespace-nowrap text-center">
                <span :class="user.is_active ? 'text-green-600' : 'text-red-600'">
                    <CheckCircleIcon v-if="user.is_active" class="h-5 w-5 inline-block" />
                    <XCircleIcon v-else class="h-5 w-5 inline-block" />
                </span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-center">
                    <span :class="user.is_superuser ? 'text-indigo-600' : 'text-gray-400'">
                    <ShieldCheckIcon v-if="user.is_superuser" class="h-5 w-5 inline-block" />
                    <ShieldExclamationIcon v-else class="h-5 w-5 inline-block" />
                    </span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {{ formatDateTime(user.created_at) }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-right text-sm font-medium space-x-2">
                <button @click="openEditModal(user)" class="text-indigo-600 hover:text-indigo-800" title="Edit User">
                    <PencilSquareIcon class="h-5 w-5 inline-block" />
                </button>
                <button
                    @click="confirmDelete(user)"
                    :disabled="user.username === authStore.username"
                    class="text-red-600 hover:text-red-800 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Delete User"
                >
                    <TrashIcon class="h-5 w-5 inline-block" />
                </button>
                </td>
            </tr>
            </tbody>
        </table>
        </div>
        <!-- TODO: Add Pagination Controls -->
    </div>

    <!-- Create/Edit User Modal -->
    <UserFormModal
        :show="showModal"
        :user-to-edit="userToEdit"
        @close="closeModal"
        @save="handleSaveUser"
    />

    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import apiService, { type UserResponse, type UserCreateData, type UserUpdateData } from '@/services/api';
import { useAuthStore } from '@/stores/auth';
import UserFormModal from './UserFormModal.vue'; // Assume this component exists
import {
    PlusIcon, PencilSquareIcon, TrashIcon, CheckCircleIcon, XCircleIcon,
    ExclamationTriangleIcon, ShieldCheckIcon, ShieldExclamationIcon
} from '@heroicons/vue/24/outline'; // Use outline icons

const authStore = useAuthStore();
const users = ref<UserResponse[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);
const showModal = ref(false);
const userToEdit = ref<UserResponse | null>(null);

const fetchUsers = async () => {
    isLoading.value = true;
    error.value = null;
    try {
    users.value = await apiService.getUsers();
    } catch (err: any) {
    error.value = err.message || 'Failed to load users.';
    } finally {
    isLoading.value = false;
    }
};

const openCreateModal = () => {
    userToEdit.value = null;
    showModal.value = true;
};

const openEditModal = (user: UserResponse) => {
    userToEdit.value = { ...user }; // Clone user data
    showModal.value = true;
};

const closeModal = () => {
    showModal.value = false;
    userToEdit.value = null;
};

const handleSaveUser = async (userData: UserCreateData | UserUpdateData) => {
    isLoading.value = true; // Consider a different loading state for modal actions
    error.value = null; // Clear main table error
    try {
        if (userToEdit.value) {
            // Update user
            await apiService.updateUser(userToEdit.value.id, userData as UserUpdateData);
        } else {
            // Create user
            await apiService.createUser(userData as UserCreateData);
        }
        closeModal();
        await fetchUsers(); // Refresh the user list
    } catch (err: any) {
        // Handle error (maybe display in modal or globally)
        console.error("Failed to save user:", err);
        // For now, log it, ideally show in modal
        alert(`Error saving user: ${err.message}`);
        // error.value = `Error saving user: ${err.message}`;
    } finally {
            isLoading.value = false;
    }
};

const confirmDelete = async (user: UserResponse) => {
    if (user.username === authStore.username) {
    alert("You cannot delete your own account.");
    return;
    }
    if (confirm(`Are you sure you want to delete user "${user.username}" (${user.email})? This action cannot be undone.`)) {
    isLoading.value = true; // Use main loading indicator for now
    error.value = null;
    try {
        await apiService.deleteUser(user.id);
        await fetchUsers(); // Refresh list
    } catch (err: any) {
        error.value = `Failed to delete user: ${err.message}`;
    } finally {
        isLoading.value = false;
    }
    }
};

    const formatDateTime = (isoString: string | null | undefined): string => {
    if (!isoString) return 'N/A';
    try {
        return new Date(isoString).toLocaleDateString(undefined, {
            year: 'numeric', month: 'short', day: 'numeric'
        });
    } catch { return 'Invalid Date'; }
};


onMounted(() => {
    fetchUsers();
});
</script>