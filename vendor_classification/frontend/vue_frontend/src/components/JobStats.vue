<template>
    <div class="card mt-4 bg-light"> <!-- Subtle background -->
      <div class="card-header">
          <h5 class="mb-0">Processing Statistics</h5>
      </div>
      <div class="card-body">
        <div v-if="isLoading" class="text-center text-muted py-3">
            <div class="spinner-border spinner-border-sm" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <span class="ms-2">Loading stats...</span>
        </div>
        <div v-else-if="error" class="alert alert-warning">{{ error }}</div>
        <div v-else-if="stats" class="row g-3">
            <div class="col-md-6">
                <p><strong>Vendors Processed:</strong> {{ stats.vendors_processed ?? 'N/A' }}</p>
                <p><strong>Unique Vendors:</strong> {{ stats.unique_vendors ?? 'N/A' }}</p>
                <p><strong>Successfully Classified (L4):</strong> {{ stats.successfully_classified_l4 ?? 'N/A' }}</p>
                <p><strong>Search Assisted (L4):</strong> {{ stats.search_successful_classifications ?? 'N/A' }}</p>
                <p><strong>Invalid Category Errors:</strong> {{ stats.invalid_category_errors ?? 'N/A' }}</p>
            </div>
             <div class="col-md-6">
                <p><strong>LLM API Calls:</strong> {{ stats.api_calls ?? 'N/A' }}</p>
                <p><strong>LLM Tokens Used:</strong> {{ stats.tokens_used ?? 'N/A' }}</p>
                <p><strong>Search API Calls:</strong> {{ stats.tavily_searches ?? 'N/A' }}</p>
                <hr class="d-md-none"> <!-- Separator on smaller screens -->
                <p><strong>Processing Time:</strong> {{ formattedTime }}</p>
             </div>
        </div>
         <div v-else class="text-muted text-center py-3">No statistics available for this job.</div>
      </div>
    </div>
  </template>

  <script setup lang="ts">
  import { ref, onMounted, watch, computed } from 'vue';
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

  const formattedTime = computed(() => {
      if (stats.value?.processing_time == null) return 'N/A';
      const seconds = stats.value.processing_time;
      if (seconds < 60) return `${seconds.toFixed(2)} seconds`;
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = (seconds % 60).toFixed(0);
      return `${minutes} min ${remainingSeconds} sec`;
  });

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
      // Use error message from interceptor
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
      // Refetch only if the new ID is valid
      if (newJobId) {
          fetchStats(newJobId);
      } else {
          // Clear stats if job ID becomes invalid/null
          stats.value = null;
          error.value = null;
          isLoading.value = false;
      }
  });

  </script>

  <style scoped>
  .card-header h5 {
      font-weight: 500;
  }
  p { margin-bottom: 0.6rem; } /* Slightly more spacing */
  p strong { color: #495057; }
  </style>