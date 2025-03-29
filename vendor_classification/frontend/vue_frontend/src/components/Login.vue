<template>
  <!-- Added mb-5 for spacing -->
  <div class="card shadow-sm mb-5">
    <div class="card-header bg-primary text-white">
      <h4 class="mb-0 text-center">Login to Access Service</h4> <!-- Centered -->
    </div>
    <div class="card-body">
      <form @submit.prevent="handleLogin">
        <div class="mb-3">
          <label for="username" class="form-label">Username</label>
          <input
              type="text"
              class="form-control"
              id="username"
              v-model="username"
              required
              :disabled="isLoading"
              placeholder="admin"
          >
          <div class="form-text">Default: admin</div>
        </div>
        <div class="mb-4"> <!-- Increased margin -->
          <label for="password" class="form-label">Password</label>
          <input
              type="password"
              class="form-control"
              id="password"
              v-model="password"
              required
              :disabled="isLoading"
              placeholder="password"
          >
           <div class="form-text">Default: password</div>
        </div>
        <button type="submit" class="btn btn-primary w-100 btn-lg" :disabled="isLoading"> <!-- Added btn-lg -->
           <span v-if="isLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
           {{ isLoading ? ' Logging in...' : 'Login' }}
        </button>
        <!-- Use Bootstrap Alert for error -->
        <div v-if="errorMessage" class="alert alert-danger text-center mt-3 py-2">{{ errorMessage }}</div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
// Script content remains the same as the previous refined version
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
 /* No extra scoped styles needed if global styles are sufficient */
</style>