<template>
  <div class="bg-white rounded-lg shadow-md mb-5 overflow-hidden border border-gray-200">
    <div class="bg-primary text-white p-4">
      <h4 class="text-xl font-semibold mb-0 text-center">Create New Account</h4>
    </div>
    <div class="p-6">
      <form @submit.prevent="handleRegister">
        <!-- Username -->
        <div class="mb-4">
          <label for="reg-username" class="block text-sm font-medium text-gray-700 mb-1">Username <span class="text-red-500">*</span></label>
          <input
            type="text"
            class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm disabled:opacity-50"
            id="reg-username"
            v-model="formData.username"
            required
            minlength="3"
            maxlength="50"
            :disabled="isLoading"
            placeholder="Choose a username"
          />
        </div>

        <!-- Email -->
        <div class="mb-4">
          <label for="reg-email" class="block text-sm font-medium text-gray-700 mb-1">Email Address <span class="text-red-500">*</span></label>
          <input
            type="email"
            class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm disabled:opacity-50"
            id="reg-email"
            v-model="formData.email"
            required
            :disabled="isLoading"
            placeholder="you@example.com"
          />
        </div>

        <!-- Full Name (Optional) -->
        <div class="mb-4">
          <label for="reg-fullname" class="block text-sm font-medium text-gray-700 mb-1">Full Name (Optional)</label>
          <input
            type="text"
            class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm disabled:opacity-50"
            id="reg-fullname"
            v-model="formData.full_name"
            :disabled="isLoading"
            placeholder="Your full name"
          />
        </div>

        <!-- Password -->
        <div class="mb-4">
          <label for="reg-password" class="block text-sm font-medium text-gray-700 mb-1">Password <span class="text-red-500">*</span></label>
          <input
            type="password"
            class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm disabled:opacity-50"
            id="reg-password"
            v-model="formData.password"
            required
            minlength="8"
            :disabled="isLoading"
            placeholder="Minimum 8 characters"
          />
        </div>

        <!-- Confirm Password -->
        <div class="mb-6">
          <label for="reg-confirmPassword" class="block text-sm font-medium text-gray-700 mb-1">Confirm Password <span class="text-red-500">*</span></label>
          <input
            type="password"
            class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm disabled:opacity-50"
            id="reg-confirmPassword"
            v-model="confirmPassword"
            required
            :disabled="isLoading"
          />
          <p v-if="passwordMismatch" class="mt-1 text-xs text-red-500">Passwords do not match.</p>
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          class="w-full flex justify-center items-center px-4 py-2.5 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-primary hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="isLoading || passwordMismatch"
        >
          <svg v-if="isLoading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ isLoading ? 'Creating Account...' : 'Register' }}
        </button>

        <!-- Error/Success Message -->
        <div v-if="message" :class="['mt-4 p-3 rounded-md text-center text-sm', messageType === 'success' ? 'bg-green-100 border border-green-300 text-green-700' : 'bg-red-100 border border-red-300 text-red-700']">
          {{ message }}
        </div>
      </form>

      <!-- Back to Login Link -->
      <div class="mt-4 text-center">
        <button @click="$emit('show-login')" class="text-sm text-primary hover:underline">
          Already have an account? Login
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import apiService, { type UserCreateData } from '@/services/api'; // Adjust path as needed

const emit = defineEmits(['registration-successful', 'show-login']);

const formData = ref<UserCreateData>({
  username: '',
  email: '',
  full_name: '',
  password: '',
  // Defaults for new users (backend handles these, but good practice)
  is_active: true,
  is_superuser: false,
});
const confirmPassword = ref('');
const isLoading = ref(false);
const message = ref<string | null>(null);
const messageType = ref<'success' | 'error'>('success');

const passwordMismatch = computed<boolean>(() => {
  return (
    formData.value.password!.length > 0 && // Use non-null assertion as password is required
    confirmPassword.value.length > 0 &&
    formData.value.password !== confirmPassword.value
  );
});

const handleRegister = async () => {
  if (passwordMismatch.value) {
    message.value = "Passwords do not match.";
    messageType.value = 'error';
    return;
  }
  if (!formData.value.password || formData.value.password.length < 8) {
    message.value = "Password is required and must be at least 8 characters.";
    messageType.value = 'error';
    return;
  }

  isLoading.value = true;
  message.value = null;
  messageType.value = 'success';

  // Prepare data, ensuring full_name is null if empty
  const dataToSend: UserCreateData = {
    ...formData.value,
    full_name: formData.value.full_name?.trim() || null,
  };

  try {
    const newUser = await apiService.registerUser(dataToSend);
    message.value = `Registration successful for ${newUser.username}! You can now log in.`;
    messageType.value = 'success';
    // Optionally clear form or emit success immediately
    // formData.value = { username: '', email: '', full_name: '', password: '' }; // Reset form
    // confirmPassword.value = '';
    emit('registration-successful'); // Notify parent

  } catch (error: any) {
    console.error('Registration error:', error);
    message.value = error.message || 'An unexpected error occurred during registration.';
    messageType.value = 'error';
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
/* Add any specific styles if needed */
</style>