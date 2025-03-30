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
              <p class="flex justify-between">
                  <strong class="text-gray-600 font-medium">Successfully Classified (L4):</strong>
                  <span class="text-green-700 font-semibold">{{ stats.successfully_classified_l4?.toLocaleString() ?? 'N/A' }}</span>
              </p>
              <p class="flex justify-between">
                  <strong class="text-gray-600 font-medium">Search Assisted (L4):</strong>
                  <span class="text-gray-800 font-semibold">{{ stats.search_successful_classifications?.toLocaleString() ?? 'N/A' }}</span>
              </p>
              <p class="flex justify-between">
                  <strong class="text-gray-600 font-medium">Invalid Category Errors:</strong>
                  <span :class="stats.invalid_category_errors > 0 ? 'text-red-600 font-semibold' : 'text-gray-800 font-semibold'">
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
  // Script remains the same
  import { ref, onMounted, watch, computed } from 'vue';
  import apiService from '@/services/api';

  interface JobStatsData {
      vendors_processed: number | null; unique_vendors: number | null; api_calls: number | null;
      tokens_used: number | null; tavily_searches: number | null; processing_time: number | null;
      successfully_classified_l4: number | null; search_successful_classifications: number | null;
      invalid_category_errors: number | null;
  }
  interface Props { jobId: string; }
  const props = defineProps<Props>();
  const stats = ref<JobStatsData | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  const formattedTime = computed(() => {
      if (stats.value?.processing_time == null) return 'N/A';
      const seconds = stats.value.processing_time;
      if (seconds < 1) return `${(seconds * 1000).toFixed(0)} ms`;
      if (seconds < 60) return `${seconds.toFixed(1)} seconds`;
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = (seconds % 60).toFixed(0);
      return `${minutes} min ${remainingSeconds} sec`;
  });

  const fetchStats = async (id: string) => {
    if (!id) return;
    isLoading.value = true; error.value = null; stats.value = null;
    try { stats.value = await apiService.getJobStats(id); }
    catch (err: any) { error.value = err.message || 'Failed.'; }
    finally { isLoading.value = false; }
  };

  onMounted(() => fetchStats(props.jobId));
  watch(() => props.jobId, (newJobId) => {
      if (newJobId) fetchStats(newJobId);
      else { stats.value = null; error.value = null; isLoading.value = false; }
  });
  </script>

  <style scoped>
  .shadow-inner {
      box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.05);
  }
  </style>