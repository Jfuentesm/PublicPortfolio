<template>
  <footer class="mt-auto py-3 bg-light"> <!-- Use mt-auto to push to bottom -->
    <div class="container text-center">
      <span class="text-muted">© {{ currentYear }} Vendor Classification Inc. All Rights Reserved.</span>
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
    font-size: 0.9em;
    padding: 1.5rem 0; /* Added padding */
}
</style>