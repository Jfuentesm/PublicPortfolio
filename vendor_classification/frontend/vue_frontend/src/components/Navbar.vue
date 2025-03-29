<template>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary fixed-top">
      <div class="container">
        <a class="navbar-brand" href="/">NAICS Vendor Classification</a>
        <!-- User Info / Logout Button Area -->
        <div v-if="isLoggedIn" class="ms-auto text-white">
          Welcome, <span>{{ username || 'User' }}</span>
          <button @click="emitLogout" class="btn btn-sm btn-outline-light ms-2">Logout</button>
        </div>
      </div>
    </nav>
  </template>
  
  <script setup lang="ts">
  interface Props {
    isLoggedIn: boolean;
    username: string | null;
  }
  
  // Define props with default values or make them optional if appropriate
  const props = defineProps<Props>();
  
  const emit = defineEmits(['logout']);
  
  const emitLogout = () => {
    emit('logout');
  };
  </script>
  
  <style scoped>
  /* Add specific Navbar styles if needed */
  .navbar {
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  </style>