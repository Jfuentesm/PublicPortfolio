
<template>
    <div class="bg-white rounded-lg shadow-md overflow-hidden border border-gray-200">
    <div class="bg-gray-100 p-4 border-b border-gray-200 flex justify-between items-center">
        <h4 class="text-lg font-semibold text-gray-700 mb-0">Forgot Password</h4>
        <button @click="$emit('close')" class="text-gray-500 hover:text-gray-700 text-xl">&times;</button>
    </div>
    <div class="p-6">
        <p class="text-sm text-gray-600 mb-4">
        Enter the email address associated with your account, and we'll send you a link to reset your password.
        </p>
        <form @submit.prevent="handleRequestReset">
        <div class="mb-4">
            <label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
            <input
            type="email"
            class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm disabled:opacity-50"
            id="email"
            v-model="email"
            required
            :disabled="isLoading || emailSent"
            placeholder="you@example.com"
            />
        </div>

        <button
            type="submit"
            class="w-full flex justify-center items-center px-4 py-2.5 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-primary hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="isLoading || emailSent"
        >
            <svg v-if="isLoading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ buttonText }}
        </button>

        <!-- Success/Error Messages -->
        <div v-if="message" :class="['mt-4 p-3 rounded-md text-center text-sm', messageType === 'success' ? 'bg-green-100 border border-green-300 text-green-700' : 'bg-red-100 border border-red-300 text-red-700']">
            {{ message }}
        </div>
        </form>
        <div class="mt-4 text-center">
            <button @click="$emit('show-login')" class="text-sm text-primary hover:underline">
            Back to Login
            </button>
        </div>
    </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import apiService from '@/services/api'; // Adjust path as needed

const emit = defineEmits(['close', 'show-login']);

const email = ref('');
const isLoading = ref(false);
const message = ref<string | null>(null);
const messageType = ref<'success' | 'error'>('success'); // 'success' or 'error'
const emailSent = ref(false); // Flag to disable form after success

const buttonText = computed(() => {
    if (isLoading.value) return 'Sending...';
    if (emailSent.value) return 'Instructions Sent';
    return 'Send Reset Link';
});

const handleRequestReset = async () => {
    isLoading.value = true;
    message.value = null;
    messageType.value = 'success';

    try {
    const response = await apiService.requestPasswordRecovery(email.value);
    message.value = response.message; // Use message from API
    messageType.value = 'success';
    emailSent.value = true; // Disable form on success
    // Optionally close the form after a delay
    // setTimeout(() => emit('close'), 5000);
    } catch (error: any) {
    console.error('Forgot Password error:', error);
    message.value = error.message || 'An unexpected error occurred.';
    messageType.value = 'error';
    emailSent.value = false; // Keep form enabled on error
    } finally {
    isLoading.value = false;
    }
};
</script>

<style scoped>
/* Add any specific styles if needed */
</style>