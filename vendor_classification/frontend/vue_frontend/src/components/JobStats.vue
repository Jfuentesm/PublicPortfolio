<template>
    <div class="card mt-4">
      <div class="card-header bg-secondary text-white">
          <h5 class="mb-0">Job Statistics</h5>
      </div>
      <div class="card-body">
        <div v-if="isLoading" class="text-center">Loading stats...</div>
        <div v-else-if="error" class="error-message">{{ error }}</div>
        <div v-else-if="stats">
          <p><strong>Vendors Processed:</strong> {{ stats.vendors_processed ?? 'N/A' }}</p>
          <p><strong>Unique Vendors:</strong> {{ stats.unique_vendors ?? 'N/A' }}</p>
          <p><strong>Successfully Classified (L4):</strong> {{ stats.successfully_classified_l4 ?? 'N/A' }}</p>
          <p><strong>Search Assisted Classifications (L4):</strong> {{ stats.search_successful_classifications ?? 'N/A' }}</p>
          <p><strong>Invalid Category Errors (LLM):</strong> {{ stats.invalid_category_errors ?? 'N/A' }}</p>
          <hr />
          <p><strong>LLM API Calls:</strong> {{ stats.api_calls ?? 'N/A' }}</p>
          <p><strong>LLM Tokens Used:</strong> {{ stats.tokens_used ?? 'N/A' }}</p>
          <p><strong>Search API Calls:</strong> {{ stats.tavily_searches ?? 'N/A' }}</p>
          <hr />
          <p><strong>Total Processing Time:</strong> {{ stats.processing_time != null ? `${stats.processing_time.toFixed(2)} seconds` : 'N/A' }}</p>
        </div>
         <div v-else>No statistics available.</div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, onMounted, watch } from 'vue';
  import apiService from '@/services/api'; // Adjust path as needed
  
  // Define the structure based on the API response expected from /api/v1/jobs/{job_id}/stats
  interface JobStatsData {
      vendors_processed: number | null;
      unique_vendors: number | null;
      api_calls: number | null;
      tokens_used: number | null;
      tavily_searches: number | null;
      processing_time: number | null;
      successfully_classified_l4: number | null;
      search_successful_classifications: number | null;
      invalid_category_errors: number | null;
  }
  
  interface Props {
    jobId: string;
  }
  
  const props = defineProps<Props>();
  const stats = ref<JobStatsData | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  
  const fetchStats = async (id: string) => {
    if (!id) return;
    isLoading.value = true;
    error.value = null;
    stats.value = null; // Clear previous stats
    console.log(`JobStats: Fetching stats for ${id}`);
    try {
      // Use your actual API service function
      stats.value = await apiService.getJobStats(id);
    } catch (err: any) {
      console.error(`JobStats: Error fetching stats for ${id}:`, err);
      error.value = err.message || 'Failed to load job statistics.';
    } finally {
      isLoading.value = false;
    }
  };
  
  // Fetch stats when the component mounts or the jobId prop changes
  onMounted(() => {
    fetchStats(props.jobId);
  });
  
  watch(() => props.jobId, (newJobId) => {
    fetchStats(newJobId);
  });
  
  </script>
  
  <style scoped>
  .error-message { color: #dc3545; }
  p { margin-bottom: 0.5rem; }
  hr { margin-top: 0.5rem; margin-bottom: 0.5rem; }
  </style>