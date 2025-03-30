<template>
  <nav class="bg-primary shadow-md fixed top-0 left-0 right-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16"> 
        <!-- Branding -->
        <div class="flex-shrink-0">
          <a class="text-white text-xl font-bold flex items-center" href="#">
             <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="h-6 w-6 mr-2" viewBox="0 0 16 16">
               <path fill-rule="evenodd" d="M6 3.5A1.5 1.5 0 0 1 7.5 2h1A1.5 1.5 0 0 1 10 3.5v1A1.5 1.5 0 0 1 8.5 6v1H14a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0v-1A.5.5 0 0 1 2 7h5.5V6A1.5 1.5 0 0 1 6 4.5zM8.5 7H14v1h-5.5zM2 8h5.5v1H2zm9.5 4.5a1.5 1.5 0 0 0-1.5-1.5h-1a1.5 1.5 0 0 0-1.5 1.5v1a1.5 1.5 0 0 0 1.5 1.5h1a1.5 1.5 0 0 0 1.5-1.5zm-1.5 2.5a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5zM2 12.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5zM11 12.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5z"/>
             </svg>
            NAICS Classify
          </a>
        </div>

        <!-- User Info / Logout Section -->
        <div v-if="isLoggedIn" class="flex items-center">
          <span class="text-gray-200 text-sm mr-4">
            Welcome, <span class="font-semibold text-white">{{ username || 'User' }}</span>
          </span>
          <button
            @click="emitLogout"
            class="px-3 py-1 border border-transparent text-sm font-medium rounded-md text-primary bg-white hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-primary focus:ring-white"
          >
            Logout
          </button>
        </div>
         <!-- Optional Login button -->
         <!-- <div v-else>
             <button class="..." @click="scrollToLogin">Login</button>
         </div> -->
      </div>
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
</script>

<style scoped>
 /* Scoped styles generally not needed with Tailwind */
</style>