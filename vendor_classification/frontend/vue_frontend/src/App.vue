<template>
  <!-- Basic wrapper, background set in styles.css/body -->
  <div class="flex flex-col min-h-screen">
    <Navbar :is-logged-in="authStore.isAuthenticated" :username="authStore.username" @logout="handleLogout" />

    <!-- main content area that grows -->
    <main role="main" class="flex-grow w-full mx-auto">
      <!-- LandingPage takes full width for its sections -->
      <LandingPage v-if="!authStore.isAuthenticated" @login-successful="handleLoginSuccess" />

      <!-- AppContent is wrapped in a standard container for logged-in state -->
       <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" v-else>
          <AppContent />
       </div>
    </main>

    <Footer />
  </div>
</template>

<script setup lang="ts">
// ... script content remains the same ...
import { onMounted } from 'vue';
import Navbar from './components/Navbar.vue';
import LandingPage from './components/LandingPage.vue';
import AppContent from './components/AppContent.vue';
import Footer from './components/Footer.vue';
import { useAuthStore } from './stores/auth';
import { useJobStore } from './stores/job';

const authStore = useAuthStore();
const jobStore = useJobStore();

const handleLogout = () => {
  authStore.logout();
  jobStore.clearJob();
  if (window.history.pushState) {
      const newUrl = window.location.protocol + "//" + window.location.host + window.location.pathname;
      window.history.pushState({path:newUrl},'',newUrl);
  }
};

const handleLoginSuccess = () => {
  console.log('Login successful, App.vue notified.');
  const urlParams = new URLSearchParams(window.location.search);
  const jobIdFromUrl = urlParams.get('job_id');
   if (jobIdFromUrl) {
      console.log(`App.vue: Found Job ID in URL after login: ${jobIdFromUrl}. Setting in store.`);
      jobStore.setCurrentJobId(jobIdFromUrl);
   }
};

onMounted(() => {
  authStore.checkAuthStatus();
  if (authStore.isAuthenticated) {
    const urlParams = new URLSearchParams(window.location.search);
    const jobIdFromUrl = urlParams.get('job_id');
    if (jobIdFromUrl && !jobStore.currentJobId) {
      console.log(`App.vue: Found Job ID in URL on mount: ${jobIdFromUrl}. Setting in store.`);
      jobStore.setCurrentJobId(jobIdFromUrl);
    }
  }
});
</script>
