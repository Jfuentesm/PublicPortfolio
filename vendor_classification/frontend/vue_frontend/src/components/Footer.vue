<template>
  <footer class="mt-auto py-4 bg-gray-100 border-t border-gray-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
      <span class="text-sm text-gray-500">© {{ currentYear }} Vendor Classification Inc. All Rights Reserved.</span>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { computed } from 'vue';
const currentYear = computed(() => new Date().getFullYear());
</script>

<style scoped>
/* Footer is simple, scoped styles likely not needed */
</style>