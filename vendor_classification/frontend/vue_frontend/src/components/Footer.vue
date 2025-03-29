<template>
    <footer class="mt-5 py-3 bg-light">
      <div class="container text-center">
        <p class="text-muted mb-0">© {{ currentYear }} NAICS Vendor Classification</p>
      </div>
    </footer>
  </template>
  
  <script setup lang="ts">
  import { computed } from 'vue';
  
  const currentYear = computed(() => new Date().getFullYear());
  </script>
  
  <style scoped>
  footer {
      color: #6c757d;
      border-top: 1px solid #dee2e6;
  }
  </style>