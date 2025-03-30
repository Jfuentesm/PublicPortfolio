<template>
  <div class="bg-white rounded-lg shadow-md mb-5 overflow-hidden border border-gray-200">
    <div class="bg-primary text-white p-4">
      <h4 class="text-xl font-semibold mb-0 text-center">Login to Access Service</h4>
    </div>
    <div class="p-6">
      <form @submit.prevent="handleLogin">
        <div class="mb-4">
          <label for="username" class="block text-sm font-medium text-gray-700 mb-1">Username</label>
          <input
              type="text"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm disabled:opacity-50"
              id="username"
              v-model="username"
              required
              :disabled="isLoading"
              placeholder="admin"
          >
          <p class="mt-1 text-xs text-gray-500">Default: admin</p>
        </div>
        <div class="mb-6">
          <label for="password" class="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input
              type="password"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm disabled:opacity-50"
              id="password"
              v-model="password"
              required
              :disabled="isLoading"
              placeholder="password"
          >
           <p class="mt-1 text-xs text-gray-500">Default: password</p>
        </div>
        <button type="submit" class="w-full flex justify-center items-center px-4 py-2.5 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-primary hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed" :disabled="isLoading">
           <svg v-if="isLoading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
           </svg>
           {{ isLoading ? ' Logging in...' : 'Login' }}
        </button>
         <!-- Tailwind Alert -->
        <div v-if="errorMessage" class="mt-4 p-3 bg-red-100 border border-red-300 text-red-700 rounded-md text-center text-sm">{{ errorMessage }}</div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
   // ... script remains the same ...
   import { ref } from 'vue';
   import { useAuthStore } from '@/stores/auth';

   const username = ref('admin');
   const password = ref('password');
   const isLoading = ref(false);
   const errorMessage = ref<string | null>(null);

   const authStore = useAuthStore();
   const emit = defineEmits(['login-successful']);

   const handleLogin = async () => {
     isLoading.value = true;
     errorMessage.value = null;
     try {
       await authStore.login(username.value, password.value);
       console.log('Login component: Login successful.');
       emit('login-successful');
     } catch (error: any) {
       console.error('Login component error:', error);
       errorMessage.value = error.message || 'An unexpected error occurred during login.';
     } finally {
       isLoading.value = false;
     }
   };
</script>

<style scoped>
 /* No scoped styles needed */
</style>