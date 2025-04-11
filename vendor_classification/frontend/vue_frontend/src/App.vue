
<template>
  <div class="flex flex-col min-h-screen">
    <Navbar
      :is-logged-in="authStore.isAuthenticated"
      :username="authStore.username"
      @logout="handleLogout"
    />

    <!-- Main content area -->
    <main role="main" class="flex-grow w-full mx-auto">
      <!-- Render based on viewStore and potentially route -->
      <LandingPage
        v-if="viewStore.currentView === 'landing' && !isResetPasswordRoute"
        @login-successful="handleLoginSuccess"
      />
      <div v-else-if="isResetPasswordRoute" class="max-w-xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <!-- ResetPassword component rendered directly based on route -->
        <ResetPassword
          :token="resetToken"
          @close="navigateToLanding"
          @show-login="navigateToLanding"
          @show-forgot-password="navigateToForgotPassword"
        />
      </div>
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" v-else-if="viewStore.currentView === 'app'">
        <AppContent />
      </div>
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" v-else-if="viewStore.currentView === 'admin'">
        <UserManagement />
      </div>
    </main>

    <Footer />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import Navbar from './components/Navbar.vue';
import LandingPage from './components/LandingPage.vue';
import AppContent from './components/AppContent.vue';
import Footer from './components/Footer.vue';
import UserManagement from './components/UserManagement.vue';
import ResetPassword from './components/ResetPassword.vue'; // Import ResetPassword
import { useAuthStore } from './stores/auth';
import { useJobStore } from './stores/job';
import { useViewStore } from './stores/view';

const authStore = useAuthStore();
const jobStore = useJobStore();
const viewStore = useViewStore();

// --- Password Reset Route Handling ---
// This simulates basic routing without Vue Router.
// For a real app, use Vue Router for proper route handling.
const currentPath = ref(window.location.pathname);
const resetToken = ref('');

const isResetPasswordRoute = computed(() => {
  const match = currentPath.value.match(/^\/reset-password\/(.+)/);
  if (match && match[1]) {
    resetToken.value = match[1]; // Extract token from path
    return true;
  }
  resetToken.value = '';
  return false;
});

// Function to update path on navigation (e.g., history API changes)
const updatePath = () => {
  currentPath.value = window.location.pathname;
};

// Simulate navigation (replace with router.push in a real app)
const navigateTo = (path: string) => {
  window.history.pushState({}, '', path);
  updatePath(); // Update internal state
  // Reset view store if navigating away from app/admin
  if (path === '/' || path === '/forgot-password') {
      if (!authStore.isAuthenticated) {
        viewStore.setView('landing');
      }
  }
};

const navigateToLanding = () => navigateTo('/');
const navigateToForgotPassword = () => {
    // In LandingPage, this would typically show the ForgotPassword modal/component
    // Since we don't have full routing, we might just navigate to '/' and rely on LandingPage state
    navigateTo('/');
    // You might need a way to signal LandingPage to show the forgot password form immediately
    // e.g., using a query parameter or a temporary state variable (less ideal)
    // For simplicity, just navigate to landing. The user clicks "Forgot Password" again there.
};


// Update path when browser back/forward buttons are used
window.addEventListener('popstate', updatePath);

onMounted(() => {
  updatePath(); // Initial path check
});
// --- End Password Reset Route Handling ---


const handleLogout = () => {
  authStore.logout();
  jobStore.clearJob();
  viewStore.setView('landing');
  navigateToLanding(); // Go to landing page URL
};

const handleLoginSuccess = () => {
  console.log('Login successful, App.vue notified.');
  viewStore.setView('app');
  const urlParams = new URLSearchParams(window.location.search);
  const jobIdFromUrl = urlParams.get('job_id');
  if (jobIdFromUrl) {
    console.log(`App.vue: Found Job ID in URL after login: ${jobIdFromUrl}. Setting in store.`);
    jobStore.setCurrentJobId(jobIdFromUrl);
  }
  authStore.fetchCurrentUserDetails();
};

// Watch auth state to set initial view (excluding reset password route)
watch(() => authStore.isAuthenticated, (isAuth) => {
  if (!isResetPasswordRoute.value) { // Only change view if not on reset password page
    if (isAuth && viewStore.currentView === 'landing') {
      viewStore.setView('app');
    } else if (!isAuth) {
      viewStore.setView('landing');
    }
  }
}, { immediate: true });

// Watch for route changes to potentially update view
// --- MODIFIED: Use _newPath to indicate unused parameter ---
watch(currentPath, (_newPath) => {
// --- END MODIFIED ---
    if (!isResetPasswordRoute.value && !authStore.isAuthenticated) {
        viewStore.setView('landing');
    }
    // Add other route-based view logic if needed
});


onMounted(() => {
  authStore.checkAuthStatus(); // This will trigger the watcher above
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

// Cleanup listener on unmount
import { onUnmounted } from 'vue';
onUnmounted(() => {
  window.removeEventListener('popstate', updatePath);
});
</script>

<style>
/* Ensure html, body, and #app take full height if needed */
html, body, #app {
  height: 100%;
  margin: 0;
}
</style>
