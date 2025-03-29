<template>
  <div id="vue-app-wrapper">
    <Navbar :is-logged-in="authStore.isAuthenticated" :username="authStore.username" @logout="handleLogout" />

    <!-- Use container-fluid for full width sections like Hero, standard container for content -->
    <main role="main" class="flex-shrink-0">
      <!-- Show Landing/Login page if not authenticated -->
      <LandingPage v-if="!authStore.isAuthenticated" @login-successful="handleLoginSuccess" />

      <!-- Show main application content (Upload, Status) if authenticated -->
      <!-- Wrap AppContent in a standard container for centered content -->
      <div class="container" v-else>
          <AppContent />
      </div>
    </main>

    <Footer />
  </div>
</template>

<script setup lang="ts">
// ... (script content remains the same as previous version) ...
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

<style>
#vue-app-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
/* main role="main" is used for semantic structure */
main.flex-shrink-0 {
  flex: 1 0 auto; /* Allows main content to grow and push footer */
  padding-bottom: 3rem; /* Add some padding at the bottom */
}
</style>