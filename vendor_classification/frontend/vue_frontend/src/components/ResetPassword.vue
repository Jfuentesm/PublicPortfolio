<template>
  <div class="bg-white rounded-lg shadow-md overflow-hidden border border-gray-200">
    <div class="bg-gray-100 p-4 border-b border-gray-200 flex justify-between items-center">
      <h4 class="text-lg font-semibold text-gray-700 mb-0">Reset Your Password</h4>
       <button @click="$emit('close')" class="text-gray-500 hover:text-gray-700 text-xl">&times;</button>
    </div>
    <div class="p-6">
      <p v-if="!tokenValid" class="text-sm text-red-600 mb-4">
        The password reset link is invalid or has expired. Please request a new one.
      </p>
      <form v-else @submit.prevent="handleResetPassword">
        <p class="text-sm text-gray-600 mb-4">
          Enter your new password below.
        </p>
        <div class="mb-4">
          <label for="newPassword" class="block text-sm font-medium text-gray-700 mb-1">New Password</label>
          <input
            type="password"
            class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm disabled:opacity-50"
            id="newPassword"
            v-model="newPassword"
            required
            minlength="8"
            :disabled="isLoading || resetSuccessful"
          />
           <p class="mt-1 text-xs text-gray-500">Minimum 8 characters.</p>
        </div>
         <div class="mb-6">
          <label for="confirmPassword" class="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
          <input
            type="password"
            class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm disabled:opacity-50"
            id="confirmPassword"
            v-model="confirmPassword"
            required
            :disabled="isLoading || resetSuccessful"
          />
           <p v-if="passwordMismatch" class="mt-1 text-xs text-red-500">Passwords do not match.</p>
        </div>

        <button
          type="submit"
          class="w-full flex justify-center items-center px-4 py-2.5 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-primary hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="isLoading || resetSuccessful || passwordMismatch"
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
         <div v-if="resetSuccessful" class="mt-4 text-center">
            <button @click="$emit('show-login')" class="text-sm text-primary hover:underline">
                Proceed to Login
            </button>
         </div>
      </form>
       <div v-if="!tokenValid" class="mt-4 text-center">
          <button @click="$emit('show-forgot-password')" class="text-sm text-primary hover:underline">
            Request New Reset Link
          </button>
           <span class="mx-2 text-gray-400">|</span>
          <button @click="$emit('show-login')" class="text-sm text-primary hover:underline">
            Back to Login
          </button>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import apiService from '@/services/api'; // Adjust path as needed

const props = defineProps({
  token: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(['close', 'show-login', 'show-forgot-password']);

const newPassword = ref('');
const confirmPassword = ref('');
const isLoading = ref(false);
const message = ref<string | null>(null);
const messageType = ref<'success' | 'error'>('success');
const resetSuccessful = ref(false);
const tokenValid = ref(true);

const passwordMismatch = computed<boolean>(() => {
  // Force a boolean so that TypeScript never sees `""`
  return (
    newPassword.value.length > 0 &&
    confirmPassword.value.length > 0 &&
    newPassword.value !== confirmPassword.value
  );
});

const buttonText = computed(() => {
  if (isLoading.value) return 'Resetting...';
  if (resetSuccessful.value) return 'Password Reset';
  return 'Reset Password';
});

onMounted(() => {
  if (!props.token) {
    tokenValid.value = false;
    message.value = "No reset token provided in the link.";
    messageType.value = 'error';
  }
});

const handleResetPassword = async () => {
  if (passwordMismatch.value) {
    message.value = "Passwords do not match.";
    messageType.value = 'error';
    return;
  }
  if (!props.token) {
     message.value = "Reset token is missing.";
     messageType.value = 'error';
     tokenValid.value = false;
     return;
  }

  isLoading.value = true;
  message.value = null;
  messageType.value = 'success';

  try {
    const response = await apiService.resetPassword(props.token, newPassword.value);
    message.value = response.message;
    messageType.value = 'success';
    resetSuccessful.value = true;
  } catch (error: any) {
    console.error('Reset Password error:', error);
    message.value = error.message || 'An unexpected error occurred.';
    messageType.value = 'error';
    resetSuccessful.value = false;
    if (error.message && (error.message.includes('Invalid') || error.message.includes('expired'))) {
        tokenValid.value = false;
    }
  } finally {
    isLoading.value = false;
  }
};
</script>