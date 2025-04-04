<template>
    <div class="mt-6 bg-gray-50 rounded-lg p-6 border border-gray-200 shadow-inner">
      <h5 class="text-lg font-semibold text-gray-700 mb-5 border-b border-gray-200 pb-3">
          Processing Statistics
      </h5>
      <div v-if="isLoading" class="text-center text-gray-500 py-4">
            <svg class="animate-spin inline-block h-5 w-5 text-primary mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
               <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
               <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Loading stats...</span>
      </div>
      <div v-else-if="error" class="p-3 bg-yellow-100 border border-yellow-300 text-yellow-800 rounded-md text-sm">
          {{ error }}
      </div>
      <div v-else-if="stats" class="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4 text-sm">
          <!-- Column 1: Vendor & Classification Stats -->
          <div class="space-y-2.5">
              <p class="flex justify-between">
                  <strong class="text-gray-600 font-medium">Vendors Processed:</strong>
                  <span class="text-gray-800 font-semibold">{{ stats.vendors_processed?.toLocaleString() ?? 'N/A' }}</span>
              </p>
              <p class="flex justify-between">
                  <strong class="text-gray-600 font-medium">Unique Vendors:</strong>
                  <span class="text-gray-800 font-semibold">{{ stats.unique_vendors?.toLocaleString() ?? 'N/A' }}</span>
              </p>
              <!-- UPDATED: Display L5 Success -->
              <p class="flex justify-between">
                  <strong class="text-gray-600 font-medium">Successfully Classified (L5):</strong>
                  <span class="text-green-700 font-semibold">{{ stats.successfully_classified_l5?.toLocaleString() ?? 'N/A' }}</span>
              </p>
              <!-- UPDATED: Display L5 Search Success -->
              <p class="flex justify-between">
                  <strong class="text-gray-600 font-medium">Search Assisted (L5):</strong>
                  <span class="text-gray-800 font-semibold">{{ stats.search_assisted_l5?.toLocaleString() ?? 'N/A' }}</span>
              </p>
              <!-- Keep L4 for reference if desired -->
               <p class="flex justify-between text-xs text-gray-500">
                  <strong class="font-normal">Ref: Classified (L4):</strong>
                  <span class="font-normal">{{ stats.successfully_classified_l4?.toLocaleString() ?? 'N/A' }}</span>
              </p>
              <p class="flex justify-between">
                  <strong class="text-gray-600 font-medium">Invalid Category Errors:</strong>
                  <span :class="(stats.invalid_category_errors ?? 0) > 0 ? 'text-red-600 font-semibold' : 'text-gray-800 font-semibold'">
                      {{ stats.invalid_category_errors?.toLocaleString() ?? 'N/A' }}
                  </span>
              </p>
          </div>
           <!-- Column 2: API & Time Stats -->
           <div class="space-y-2.5">
              <p class="flex justify-between">
                  <strong class="text-gray-600 font-medium">LLM API Calls:</strong>
                  <span class="text-gray-800 font-semibold">{{ stats.api_calls?.toLocaleString() ?? 'N/A' }}</span>
              </p>
              <p class="flex justify-between">
                  <strong class="text-gray-600 font-medium">LLM Tokens Used:</strong>
                  <span class="text-gray-800 font-semibold">{{ stats.tokens_used?.toLocaleString() ?? 'N/A' }}</span>
              </p>
              <p class="flex justify-between">
                  <strong class="text-gray-600 font-medium">Search API Calls:</strong>
                  <span class="text-gray-800 font-semibold">{{ stats.tavily_searches?.toLocaleString() ?? 'N/A' }}</span>
              </p>
              <p class="flex justify-between pt-2 mt-1 border-t border-gray-200">
                  <strong class="text-gray-600 font-medium">Processing Time:</strong>
                  <span class="text-gray-800 font-semibold">{{ formattedTime }}</span>
              </p>
           </div>
      </div>
       <div v-else class="text-gray-500 text-center py-4 text-sm">No statistics available for this job.</div>
    </div>
  </template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
// --- MODIFIED: Import JobStatsData from apiService ---
import apiService, { type JobStatsData } from '@/services/api';
// --- END MODIFIED ---

// --- REMOVED: Redundant local interface definition ---
// interface JobStatsData { ... }
// --- END REMOVED ---

// Define the component props
interface Props {
    jobId: string | null | undefined; // Allow jobId to be potentially null or undefined
}
const props = defineProps<Props>();

// Reactive state variables
const stats = ref<JobStatsData | null>(null); // Use the imported type
const isLoading = ref(false);
const error = ref<string | null>(null);

// Computed property to format processing time nicely
const formattedTime = computed(() => {
    if (stats.value?.processing_time == null) return 'N/A'; // Check for null or undefined
    const seconds = stats.value.processing_time;
    if (seconds < 0) return 'N/A'; // Handle potential negative values if they occur
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)} ms`;
    if (seconds < 60) return `${seconds.toFixed(1)} seconds`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = (seconds % 60).toFixed(0);
    return `${minutes} min ${remainingSeconds} sec`;
});

/**
 * Fetches job statistics from the API for the given job ID.
 * @param {string | null | undefined} id - The job ID to fetch stats for.
 */
const fetchStats = async (id: string | null | undefined) => {
  // Only proceed if id is a non-empty string
  if (!id) {
      console.log("JobStats: fetchStats called with no ID, skipping."); // Logging
      stats.value = null; // Clear previous stats if ID is null/undefined
      error.value = null;
      isLoading.value = false;
      return;
  }

  isLoading.value = true;
  error.value = null;
  // Don't clear stats immediately, only on successful fetch or error
  // stats.value = null;

  try {
      console.log(`JobStats: Fetching stats for job ID: ${id}`); // Logging
      // The API service now returns the updated structure
      stats.value = await apiService.getJobStats(id);
      console.log(`JobStats: Received stats:`, JSON.parse(JSON.stringify(stats.value))); // Log a deep copy
  } catch (err: any) {
      console.error(`JobStats: Error fetching stats for ${id}:`, err); // Logging
      error.value = err.message || 'Failed to load statistics.';
      stats.value = null; // Clear stats on error
  } finally {
      isLoading.value = false;
  }
};

// Fetch stats when the component mounts
onMounted(() => {
    console.log(`JobStats: Mounted with initial jobId: ${props.jobId}`); // Logging
    fetchStats(props.jobId);
});

// Watch for changes in the jobId prop and refetch stats
watch(() => props.jobId,
  (newJobId: string | null | undefined) => {
    console.log(`JobStats: Watched jobId changed to: ${newJobId}`); // Logging
    fetchStats(newJobId); // fetchStats handles null/undefined check internally
  },
  { immediate: false } // Don't run immediately, onMounted handles initial fetch
);
</script>

<style scoped>
  .shadow-inner {
      box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.05);
  }
  /* Add any other specific styles if needed */
</style>