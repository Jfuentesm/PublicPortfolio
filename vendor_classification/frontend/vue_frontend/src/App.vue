<template>
  <div class="flex flex-col min-h-screen">
  <Navbar
      :is-logged-in="authStore.isAuthenticated"
      :username="authStore.username"
      @logout="handleLogout"
  />

  <!-- main content area that grows -->
  <main role="main" class="flex-grow w-full mx-auto">
      <!-- Render based on viewStore -->
      <LandingPage v-if="viewStore.currentView === 'landing'" @login-successful="handleLoginSuccess" />
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" v-else-if="viewStore.currentView === 'app'">
      <AppContent />
      </div>
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" v-else-if="viewStore.currentView === 'admin'">
      <!-- Placeholder for Admin Content -->
      <UserManagement />
      </div>
  </main>

  <Footer />
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue';
import Navbar from './components/Navbar.vue';
import LandingPage from './components/LandingPage.vue';
import AppContent from './components/AppContent.vue';
import Footer from './components/Footer.vue';
import UserManagement from './components/UserManagement.vue'; // Import the new component
import { useAuthStore } from './stores/auth';
import { useJobStore } from './stores/job';
import { useViewStore } from './stores/view'; // Import the view store

const authStore = useAuthStore();
const jobStore = useJobStore();
const viewStore = useViewStore(); // Use the view store

const handleLogout = () => {
  authStore.logout();
  jobStore.clearJob();
  viewStore.setView('landing'); // Go to landing page on logout
  // No need to manually clear URL, logout reloads page
};

const handleLoginSuccess = () => {
  console.log('Login successful, App.vue notified.');
  viewStore.setView('app'); // Go to app content on login
  const urlParams = new URLSearchParams(window.location.search);
  const jobIdFromUrl = urlParams.get('job_id');
  if (jobIdFromUrl) {
      console.log(`App.vue: Found Job ID in URL after login: ${jobIdFromUrl}. Setting in store.`);
      jobStore.setCurrentJobId(jobIdFromUrl);
  }
  // Fetch user details after login to ensure superuser status is up-to-date
  authStore.fetchCurrentUserDetails();
};

// Watch auth state to set initial view
watch(() => authStore.isAuthenticated, (isAuth) => {
  if (isAuth && viewStore.currentView === 'landing') {
      viewStore.setView('app');
  } else if (!isAuth) {
      viewStore.setView('landing');
  }
}, { immediate: true }); // Run immediately on mount

onMounted(() => {
  authStore.checkAuthStatus(); // This will trigger the watcher above
  // If authenticated, potentially fetch user details again
  if (authStore.isAuthenticated) {
      authStore.fetchCurrentUserDetails();
      const urlParams = new URLSearchParams(window.location.search);
      const jobIdFromUrl = urlParams.get('job_id');
      if (jobIdFromUrl && !jobStore.currentJobId) {
      console.log(`App.vue: Found Job ID in URL on mount: ${jobIdFromUrl}. Setting in store.`);
      jobStore.setCurrentJobId(jobIdFromUrl);
      }
  }
});
</script>