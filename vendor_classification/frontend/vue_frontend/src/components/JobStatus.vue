<template>
    <div v-if="jobStore.currentJobId" class="card mt-4">
      <div class="card-header bg-info text-white">
        <h4 class="mb-0">Job Status</h4>
      </div>
      <div class="card-body">
        <div v-if="errorMessage" class="error-message mb-3">{{ errorMessage }}</div>
  
        <div class="mb-3">
          <strong>Job ID:</strong> <span>{{ jobStore.currentJobId }}</span>
        </div>
        <div class="mb-3">
          <strong>Status:</strong> <span :class="statusClass">{{ jobDetails?.status || 'Loading...' }}</span>
          <span v-if="jobDetails?.status === 'failed' && jobDetails?.error_message" class="error-message ms-2">
              : {{ jobDetails.error_message.substring(0, 150) }}{{ jobDetails.error_message.length > 150 ? '...' : '' }}
          </span>
        </div>
        <div class="mb-3">
          <strong>Current Stage:</strong> <span>{{ formattedStage }}</span>
        </div>
        <div class="mb-3">
          <div class="progress">
            <div
              class="progress-bar"
              role="progressbar"
              :style="{ width: progressPercent + '%' }"
              :class="progressClass"
              >{{ progressPercent }}%</div
            >
          </div>
        </div>
        <div class="mb-3">
          <strong>Created:</strong> <span>{{ formattedCreatedAt }}</span>
        </div>
        <div class="mb-3">
          <strong>Updated:</strong> <span>{{ formattedUpdatedAt }}</span>
        </div>
        <div class="mb-3">
          <strong>Estimated Completion:</strong> <span>{{ formattedEstimatedCompletion }}</span>
        </div>
  
        <!-- Notification Section -->
        <div v-if="jobDetails?.status !== 'completed' && jobDetails?.status !== 'failed'" class="mb-3">
          <label for="notificationEmail" class="form-label">Email Notification</label>
          <div class="input-group">
            <input type="email" class="form-control" id="notificationEmail" placeholder="Enter your email" v-model="notificationEmail" :disabled="isNotifyLoading">
            <button class="btn btn-outline-primary" type="button" @click="requestNotification" :disabled="isNotifyLoading || !notificationEmail">
              {{ isNotifyLoading ? 'Sending...' : 'Notify Me' }}
            </button>
          </div>
          <div v-if="notifyMessage" :class="notifyMessageIsError ? 'error-message' : 'success-message'" class="form-text mt-1">{{ notifyMessage }}</div>
           <div v-else class="form-text">We'll notify you when processing is complete.</div>
        </div>
  
        <!-- Download Section -->
        <div v-if="jobDetails?.status === 'completed'" class="mb-3">
          <button @click="downloadResults" class="btn btn-success w-100" :disabled="isDownloadLoading">
            {{ isDownloadLoading ? 'Preparing Download...' : 'Download Results' }}
          </button>
          <div v-if="downloadError" class="error-message mt-1">{{ downloadError }}</div>
        </div>
  
        <!-- Stats Section (Conditionally Rendered) -->
         <JobStats v-if="jobDetails?.status === 'completed' && jobStore.currentJobId" :job-id="jobStore.currentJobId" />
  
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
  import apiService from '@/services/api'; // Adjust path
  import { useJobStore, type JobDetails } from '@/stores/job'; // Adjust path
  import JobStats from './JobStats.vue'; // Import JobStats
  
  const POLLING_INTERVAL = 5000; // 5 seconds
  const POLLING_RETRY_INTERVAL = 15000; // 15 seconds
  
  const jobStore = useJobStore();
  
  const jobDetails = ref<JobDetails | null>(null);
  const isLoading = ref(false);
  const errorMessage = ref<string | null>(null);
  const pollingIntervalId = ref<number | null>(null);
  
  const notificationEmail = ref('');
  const isNotifyLoading = ref(false);
  const notifyMessage = ref<string | null>(null);
  const notifyMessageIsError = ref(false);
  
  const isDownloadLoading = ref(false);
  const downloadError = ref<string | null>(null);
  
  // --- Computed Properties for Display ---
  const formattedStage = computed(() => {
    const stage = jobDetails.value?.current_stage;
    if (!stage) return 'N/A';
    const stageNames: { [key: string]: string } = {
      'ingestion': 'File Ingestion',
      'normalization': 'Vendor Name Normalization',
      'classification_level_1': 'Level 1 Classification',
      'classification_level_2': 'Level 2 Classification',
      'classification_level_3': 'Level 3 Classification',
      'classification_level_4': 'Level 4 Classification',
      'search_unknown_vendors': 'Vendor Research',
      'result_generation': 'Result Generation',
      'completed': 'Completed',
      'failed': 'Failed'
    };
    return stageNames[stage] || stage;
  });
  
  const progressPercent = computed(() => {
    return Math.round((jobDetails.value?.progress || 0) * 100);
  });
  
  const statusClass = computed(() => {
      switch (jobDetails.value?.status) {
          case 'completed': return 'text-success fw-bold';
          case 'failed': return 'text-danger fw-bold';
          case 'processing': return 'text-primary';
          default: return 'text-muted';
      }
  });
  
  const progressClass = computed(() => {
    const status = jobDetails.value?.status;
    if (status === 'completed') return 'progress-bar bg-success';
    if (status === 'failed') return 'progress-bar bg-danger';
    return 'progress-bar progress-bar-striped progress-bar-animated'; // Default/Processing
  });
  
  const formatDateTime = (isoString: string | null | undefined): string => {
      if (!isoString) return 'N/A';
      try {
          return new Date(isoString).toLocaleString();
      } catch {
          return 'Invalid Date';
      }
  };
  
  const formattedCreatedAt = computed(() => formatDateTime(jobDetails.value?.created_at));
  const formattedUpdatedAt = computed(() => formatDateTime(jobDetails.value?.updated_at));
  const formattedEstimatedCompletion = computed(() => {
      if (jobDetails.value?.status === 'completed' && jobDetails.value?.completed_at) {
          return formatDateTime(jobDetails.value.completed_at);
      }
      if (jobDetails.value?.status === 'processing' && jobDetails.value?.estimated_completion) {
           return `${formatDateTime(jobDetails.value.estimated_completion)} (est.)`;
      }
      if (jobDetails.value?.status === 'processing') return 'Calculating...';
      return 'N/A';
  });
  
  
  // --- Methods ---
  const pollJobStatus = async (jobId: string) => {
    if (!jobId) return;
    isLoading.value = true; // Indicate loading during poll
    // Don't clear main error message on poll, only on success or specific poll error
    // errorMessage.value = null;
  
    try {
      const data = await apiService.getJobStatus(jobId);
      jobDetails.value = data; // Update local state
      jobStore.updateJobDetails(data); // Update store state
      errorMessage.value = null; // Clear error on successful poll
  
      // Handle final states
      if (data.status === 'completed' || data.status === 'failed') {
        console.log(`Job ${jobId} finished polling with status: ${data.status}`);
        stopPolling();
        // Reset upload form state if needed (might be better handled in UploadForm itself)
      }
    } catch (error: any) {
      console.error(`Error polling job status for ${jobId}:`, error);
      errorMessage.value = `Polling Error: ${error.message || 'Failed to fetch job status.'}`;
      // Implement retry logic or stop polling on persistent errors
      console.warn(`Retrying polling for ${jobId} in ${POLLING_RETRY_INTERVAL / 1000} seconds after error.`);
      stopPolling(); // Stop current interval
      // Schedule a single retry attempt
       pollingIntervalId.value = window.setTimeout(() => {
          if (jobStore.currentJobId === jobId) { // Check if job is still the current one
               startPolling(jobId);
          } else {
               console.log("Polling retry aborted, job ID changed.");
          }
       }, POLLING_RETRY_INTERVAL);
  
    } finally {
      isLoading.value = false;
    }
  };
  
  const startPolling = (jobId: string) => {
    if (!jobId) return;
    stopPolling(); // Clear existing interval
    console.log(`Starting polling for Job ID: ${jobId}`);
    pollJobStatus(jobId); // Initial poll
    pollingIntervalId.value = window.setInterval(() => pollJobStatus(jobId), POLLING_INTERVAL);
  };
  
  const stopPolling = () => {
    if (pollingIntervalId.value !== null) {
      console.log(`Stopping polling interval ID: ${pollingIntervalId.value}`);
      clearInterval(pollingIntervalId.value);
      pollingIntervalId.value = null;
    }
  };
  
  const requestNotification = async () => {
    if (!jobStore.currentJobId || !notificationEmail.value) return;
  
    isNotifyLoading.value = true;
    notifyMessage.value = null;
    notifyMessageIsError.value = false;
  
    try {
      const response = await apiService.requestNotification(jobStore.currentJobId, notificationEmail.value);
      notifyMessage.value = response.message || 'Notification request sent successfully!';
      notificationEmail.value = ''; // Clear email on success
    } catch (error: any) {
      notifyMessage.value = `Error: ${error.message || 'Failed to send notification request.'}`;
      notifyMessageIsError.value = true;
    } finally {
      isNotifyLoading.value = false;
    }
  };
  
  const downloadResults = async () => {
    if (!jobStore.currentJobId) return;
  
    isDownloadLoading.value = true;
    downloadError.value = null;
  
    try {
      const { blob, filename } = await apiService.downloadResults(jobStore.currentJobId);
  
      // Create a temporary link to trigger the download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      console.log('File download triggered.');
  
    } catch (error: any) {
      console.error('Download error:', error);
      downloadError.value = `Download failed: ${error.message || 'Could not download results.'}`;
    } finally {
      isDownloadLoading.value = false;
    }
  };
  
  // --- Lifecycle Hooks ---
  onMounted(() => {
    if (jobStore.currentJobId) {
      jobDetails.value = jobStore.jobDetails; // Initialize with store data if available
      if (jobDetails.value?.status !== 'completed' && jobDetails.value?.status !== 'failed') {
          startPolling(jobStore.currentJobId);
      } else if (jobDetails.value?.status === 'completed') {
          // If already completed from store, maybe fetch stats? Handled by JobStats component now.
      }
    }
  });
  
  onUnmounted(() => {
    stopPolling();
  });
  
  // Watch for changes in the job ID from the store (e.g., after upload or URL change)
  watch(() => jobStore.currentJobId, (newJobId, oldJobId) => {
    console.log(`JobStatus: Job ID changed from ${oldJobId} to ${newJobId}`);
    if (newJobId) {
      jobDetails.value = jobStore.jobDetails; // Reset details from store
      errorMessage.value = null;
      downloadError.value = null;
      notifyMessage.value = null;
      notificationEmail.value = '';
      // Start polling only if not already completed/failed
      if (jobStore.jobDetails?.status !== 'completed' && jobStore.jobDetails?.status !== 'failed') {
          startPolling(newJobId);
      } else {
          stopPolling(); // Ensure polling is stopped for completed/failed jobs
      }
    } else {
      stopPolling();
      jobDetails.value = null; // Clear details if job ID is cleared
    }
  });
  
  // Watch for status changes within the store's details to stop polling
  watch(() => jobStore.jobDetails?.status, (newStatus, oldStatus) => {
      if (newStatus && oldStatus !== newStatus && (newStatus === 'completed' || newStatus === 'failed')) {
          console.log(`JobStatus: Detected final status "${newStatus}" via store watch. Stopping polling.`);
          stopPolling();
      }
      // Update local ref if store changes (though polling should also update it)
      if (jobStore.jobDetails) {
          jobDetails.value = { ...jobStore.jobDetails };
      }
  });
  
  </script>
  
  <style scoped>
  .progress {
      height: 25px;
      border-radius: 10px;
      font-size: 0.9rem;
      background-color: #e9ecef;
  }
  .progress-bar {
      font-weight: 500;
      color: #fff;
      text-align: center;
      white-space: nowrap;
      transition: width .6s ease;
  }
  .error-message { color: #dc3545; font-size: 0.875em; }
  .success-message { color: #198754; font-size: 0.875em; }
  </style>