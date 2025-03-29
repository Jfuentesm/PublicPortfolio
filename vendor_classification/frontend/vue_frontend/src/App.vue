<template>
  <div>
    <Navbar :is-logged-in="authStore.isAuthenticated" :username="authStore.username" @logout="handleLogout" />

    <div class="container mt-nav-fix">
      <LandingPage v-if="!authStore.isAuthenticated" @login-successful="handleLoginSuccess" />
      <AppContent v-else />
    </div>

    <Footer />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import Navbar from './components/Navbar.vue';
import LandingPage from './components/LandingPage.vue';
import AppContent from './components/AppContent.vue';
import Footer from './components/Footer.vue';
import { useAuthStore } from './stores/auth';
import { useJobStore } from './stores/job'; // Import job store

const authStore = useAuthStore();
const jobStore = useJobStore(); // Use job store

const handleLogout = () => {
  authStore.logout();
  jobStore.clearJob(); // Clear job state on logout
  // Optionally clear URL query params
  if (window.history.pushState) {
      const newUrl = window.location.protocol + "//" + window.location.host + window.location.pathname;
      window.history.pushState({path:newUrl},'',newUrl);
  }
};

const handleLoginSuccess = () => {
  // Auth store should update isAuthenticated itself after successful login
  console.log('Login successful, App.vue notified.');
};

// Check auth status on component mount (e.g., if token exists in localStorage)
// Also check for job_id in URL on initial load if authenticated
onMounted(() => {
  authStore.checkAuthStatus(); // Action in store to check localStorage
  if (authStore.isAuthenticated) {
    const urlParams = new URLSearchParams(window.location.search);
    const jobIdFromUrl = urlParams.get('job_id');
    if (jobIdFromUrl && !jobStore.currentJobId) {
      console.log(`App.vue: Found Job ID in URL: ${jobIdFromUrl}. Setting in store.`);
      jobStore.setCurrentJobId(jobIdFromUrl); // Set job ID in store
    }
  }
});
</script>

<style>
/* Import global styles if not done in main.ts */
/* @import './assets/css/styles.css'; */

body {
    padding-top: 56px; /* Adjust for fixed navbar height */
}

.mt-nav-fix {
    margin-top: 2rem; /* Additional margin below navbar */
}
</style>