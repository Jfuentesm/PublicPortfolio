<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary fixed-top">
    <div class="container">
      <!-- Branding -->
      <a class="navbar-brand fw-bold" href="#">
         <!-- Optional: Add an SVG logo here -->
         <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-diagram-3-fill me-2" viewBox="0 0 16 16">
           <path fill-rule="evenodd" d="M6 3.5A1.5 1.5 0 0 1 7.5 2h1A1.5 1.5 0 0 1 10 3.5v1A1.5 1.5 0 0 1 8.5 6v1H14a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0v-1A.5.5 0 0 1 2 7h5.5V6A1.5 1.5 0 0 1 6 4.5zM8.5 7H14v1h- опасностиv-1zM2 8h5.5v1H2z"/>
           <path d="M7.5 11h1a1.5 1.5 0 0 1 1.5 1.5v1A1.5 1.5 0 0 1 8.5 15h-1A1.5 1.5 0 0 1 6 13.5v-1A1.5 1.5 0 0 1 7.5 11"/>
           <path d="M2 11h1.5a.5.5 0 0 1 0 1H2zm10.5 1a.5.5 0 0 1 0-1H14v1z"/>
         </svg>
        NAICS Classify
      </a>

      <!-- User Info / Logout Section -->
      <div class="d-flex align-items-center" v-if="isLoggedIn">
        <span class="navbar-text me-3">
          Welcome, <span class="fw-semibold">{{ username || 'User' }}</span>
        </span>
        <button @click="emitLogout" class="btn btn-outline-light btn-sm">Logout</button>
      </div>
       <!-- Login Button (optional, shown when logged out) -->
       <!-- <div v-else>
           <button class="btn btn-outline-light btn-sm" @click="scrollToLogin">Login</button>
       </div> -->
    </div>
  </nav>
</template>

<script setup lang="ts">
interface Props {
  isLoggedIn: boolean;
  username: string | null;
}
defineProps<Props>();
const emit = defineEmits(['logout']);
const emitLogout = () => emit('logout');

// const scrollToLogin = () => { ... } // If using scroll button
</script>

<style scoped>
/* Styles are mostly handled globally now */
.navbar-brand {
    letter-spacing: 0.5px;
}
.navbar-text .fw-semibold {
    color: var(--white-color); /* Ensure username is white */
}
</style>