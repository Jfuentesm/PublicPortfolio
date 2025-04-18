<template>
  <div class="flex flex-col min-h-screen">
    <Navbar
      :is-logged-in="authStore.isAuthenticated"
      :username="authStore.username"
      @logout="handleLogout"
    />

    <!-- Main content area -->
    <main role="main" class="flex-grow w-full mx-auto pt-16"> <!-- Added pt-16 for fixed navbar -->
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
        <!-- AppContent manages JobUpload, JobHistory, JobStatus -->
        <AppContent />
      </div>
      <!-- === UPDATED: Render AdminDashboard for 'admin' view === -->
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" v-else-if="viewStore.currentView === 'admin'">
        <AdminDashboard />
        <!-- Note: UserManagement might be moved *inside* AdminDashboard or accessed via a sub-route/tab there -->
      </div>
      <!-- === END UPDATED === -->
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
// import UserManagement from './components/UserManagement.vue'; // Keep if needed elsewhere, remove if only in AdminDashboard
import AdminDashboard from './components/AdminDashboard.vue'; // <<< Import AdminDashboard
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
const currentSearch = ref(window.location.search); // Track query params
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
const updateRouteInfo = () => {
  currentPath.value = window.location.pathname;
  currentSearch.value = window.location.search;
  console.log("App.vue: Route updated - Path:", currentPath.value, "Search:", currentSearch.value); // Debugging
};

// Simulate navigation (replace with router.push in a real app)
const navigateTo = (path: string, searchParams: URLSearchParams | null = null) => {
    let url = path;
    if (searchParams && searchParams.toString()) {
        url += `?${searchParams.toString()}`;
    }
    window.history.pushState({}, '', url);
    updateRouteInfo(); // Update internal state
    // Reset view store if navigating away from app/admin
    if (path === '/' || path === '/forgot-password') {
        if (!authStore.isAuthenticated) {
            viewStore.setView('landing');
        } else if (viewStore.currentView === 'admin') {
            // If navigating away from admin, switch back to app view
            viewStore.setView('app');
        }
    }
    // If navigating to the main app view, check for job_id
    if (path === '/') { // Assuming '/' is the main app view when logged in
        handleAppNavigation(searchParams);
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
window.addEventListener('popstate', updateRouteInfo);

onMounted(() => {
  updateRouteInfo(); // Initial route check
});
// --- End Password Reset Route Handling ---

// --- App Navigation Logic ---
const handleAppNavigation = (searchParams: URLSearchParams | null) => {
    const params = searchParams || new URLSearchParams(currentSearch.value);
    const jobIdFromUrl = params.get('job_id');
    console.log("App.vue: Handling app navigation. Job ID from URL:", jobIdFromUrl); // Debugging
    // If authenticated and a job ID is present, set it in the store
    // Let the store decide if it's a new ID or a refresh
    if (authStore.isAuthenticated && jobIdFromUrl) {
        console.log(`App.vue: Setting Job ID from URL: ${jobIdFromUrl}`);
        jobStore.setCurrentJobId(jobIdFromUrl);
    } else if (authStore.isAuthenticated && !jobIdFromUrl && jobStore.currentJobId) {
         // If authenticated and URL has no job_id, but store has one, clear it
         console.log(`App.vue: URL has no job_id, clearing store's currentJobId.`);
         jobStore.setCurrentJobId(null);
    }
};


const handleLogout = () => {
  authStore.logout();
  jobStore.clearJob();
  viewStore.setView('landing');
  navigateToLanding(); // Go to landing page URL
};

const handleLoginSuccess = () => {
  console.log('Login successful, App.vue notified.');
  viewStore.setView('app'); // Default to app view on login
  authStore.fetchCurrentUserDetails();
  // Check URL for job_id immediately after login
  const urlParams = new URLSearchParams(window.location.search);
  handleAppNavigation(urlParams);
};

// Watch auth state to set initial view (excluding reset password route)
watch(() => authStore.isAuthenticated, (isAuth, wasAuth) => {
  console.log("App.vue: Auth state changed:", isAuth); // Debugging
  if (!isResetPasswordRoute.value) { // Only change view if not on reset password page
    if (isAuth && viewStore.currentView === 'landing') {
      console.log("App.vue: Auth true, setting view to 'app'");
      viewStore.setView('app'); // Default to app view
      // Check URL for job_id when becoming authenticated
      const urlParams = new URLSearchParams(window.location.search);
      handleAppNavigation(urlParams);
    } else if (!isAuth && wasAuth) { // Only switch to landing if user was previously authenticated (i.e., logged out)
      console.log("App.vue: Auth false, setting view to 'landing'");
      viewStore.setView('landing');
    }
  }
}, { immediate: false }); // Change immediate to false to avoid race conditions on initial load

// Watch for route changes (path or search) to potentially update view or job ID
watch([currentPath, currentSearch], ([newPath, newSearch], [_oldPath, oldSearch]) => {
    console.log("App.vue: Route watcher triggered. New Path:", newPath, "New Search:", newSearch); // Debugging
    if (!isResetPasswordRoute.value && !authStore.isAuthenticated) {
        console.log("App.vue: Not reset route, not authenticated, setting view to landing.");
        viewStore.setView('landing');
    } else if (authStore.isAuthenticated && viewStore.currentView !== 'admin') { // Only adjust job ID if not in admin view
        // If already in the app view, check if the job_id param changed
        const oldParams = new URLSearchParams(oldSearch);
        const newParams = new URLSearchParams(newSearch);
        const oldJobId = oldParams.get('job_id');
        const newJobId = newParams.get('job_id');

        if (newJobId !== oldJobId) {
             console.log(`App.vue: job_id param changed from ${oldJobId} to ${newJobId}. Updating store.`);
             jobStore.setCurrentJobId(newJobId); // Let the store handle null/new value
        }
    }
    // Add other route-based view logic if needed
}, { deep: true }); // Use deep watch if needed, though path/search are primitive


onMounted(() => {
    authStore.checkAuthStatus();
    // Rely on the watcher for isAuthenticated to handle logic after status check

    // Initial setup based on current state after checkAuthStatus might have run
    console.log("App.vue: onMounted - Initial state check. Auth state:", authStore.isAuthenticated);
    updateRouteInfo(); // Ensure route info is current
    if (authStore.isAuthenticated) {
      authStore.fetchCurrentUserDetails();
      // Set initial view based on auth state *after* checking auth
      if (!isResetPasswordRoute.value) {
          // Don't force 'app' view here if 'admin' might be intended (e.g., from Navbar click)
          // The Navbar click handler should set the view correctly.
          // If landing page is shown initially, the auth watcher will switch to 'app'.
          if (viewStore.currentView === 'landing') {
              viewStore.setView('app');
          }
      }
      handleAppNavigation(null); // Check URL for job_id after auth check
    } else {
       if (!isResetPasswordRoute.value) {
         viewStore.setView('landing');
       }
    }
});

// Cleanup listener on unmount
import { onUnmounted } from 'vue';
onUnmounted(() => {
  window.removeEventListener('popstate', updateRouteInfo);
});
</script>

<style>
/* Ensure html, body, and #app take full height if needed */
html, body, #app {
  height: 100%;
  margin: 0;
}
/* Add padding to the top of the main content area to account for the fixed navbar */
main[role="main"] {
  padding-top: 4rem; /* Adjust this value based on your navbar's height (h-16 = 4rem) */
}
</style>