<template>
    <div class="card mb-4">
      <div class="card-header bg-primary text-white">
        <h4 class="mb-0">Login to Access</h4>
      </div>
      <div class="card-body">
        <form @submit.prevent="handleLogin">
          <div class="mb-3">
            <label for="username" class="form-label">Username</label>
            <input type="text" class="form-control" id="username" v-model="username" required :disabled="isLoading">
            <div class="form-text">Default credentials: admin / password</div>
          </div>
          <div class="mb-3">
            <label for="password" class="form-label">Password</label>
            <input type="password" class="form-control" id="password" v-model="password" required :disabled="isLoading">
          </div>
          <button type="submit" class="btn btn-primary" :disabled="isLoading">
            {{ isLoading ? 'Logging in...' : 'Login' }}
          </button>
          <div v-if="errorMessage" class="error-message mt-2">{{ errorMessage }}</div>
        </form>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref } from 'vue';
  import { useAuthStore } from '@/stores/auth'; // Adjust path as needed
  
  const username = ref('');
  const password = ref('');
  const isLoading = ref(false);
  const errorMessage = ref<string | null>(null);
  
  const authStore = useAuthStore();
  const emit = defineEmits(['login-successful']);
  
  const handleLogin = async () => {
    isLoading.value = true;
    errorMessage.value = null;
    try {
      await authStore.login(username.value, password.value);
      // No need to manually set token/user here, store handles it
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
  .error-message {
      color: #dc3545;
      font-size: 0.875em;
  }
  </style>