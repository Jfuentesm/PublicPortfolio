<template>
  <div v-if="jobStore.currentJobId" class="card shadow-sm">
    <div class="card-header bg-secondary text-white"> <!-- Changed bg color -->
      <h4 class="mb-0">Job Status</h4>
    </div>
    <div class="card-body">
      <div v-if="errorMessage" class="alert alert-warning">{{ errorMessage }}</div>

      <div class="row mb-3">
        <div class="col-md-6">
           <strong>Job ID:</strong> <span>{{ jobStore.currentJobId }}</span>
        </div>
         <div class="col-md-6">
           <strong>Status:</strong> <span :class="statusClass">{{ jobDetails?.status || 'Loading...' }}</span>
         </div>
      </div>

      <div class="mb-3">
        <strong>Current Stage:</strong> <span>{{ formattedStage }}</span>
          <span v-if="jobDetails?.status === 'failed' && jobDetails?.error_message" class="error-message d-block mt-1">
            <strong>Error:</strong> {{ jobDetails.error_message }}
          </span>
      </div>

      <div class="mb-3">
        <label class="form-label">Progress:</label>
        <div class="progress">
          <div
            class="progress-bar"
            role="progressbar"
            :style="{ width: progressPercent + '%' }"
            :class="progressClass"
            :aria-valuenow="progressPercent"
            aria-valuemin="0"
            aria-valuemax="100"
            >{{ progressPercent }}%</div>
        </div>
      </div>

      <div class="row mb-3">
          <div class="col-md-6">
               <strong>Created:</strong> <span>{{ formattedCreatedAt }}</span>
          </div>
          <div class="col-md-6">
               <strong>Updated:</strong> <span>{{ formattedUpdatedAt }}</span>
          </div>
           <div class="col-md-6">
              <strong>Estimated Completion:</strong> <span>{{ formattedEstimatedCompletion }}</span>
          </div>
      </div>

      <!-- Notification Section -->
      <div v-if="canRequestNotify" class="mb-4 p-3 border rounded bg-light">
          <label for="notificationEmail" class="form-label">Get Notified Upon Completion</label>
          <div class="input-group">
              <input type="email" class="form-control" id="notificationEmail" placeholder="Enter your email" v-model="notificationEmail" :disabled="isNotifyLoading">
              <button class="btn btn-outline-primary" type="button" @click="requestNotification" :disabled="isNotifyLoading || !notificationEmail">
                  <span v-if="isNotifyLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                  {{ isNotifyLoading ? ' Sending...' : 'Notify Me' }}
              </button>
          </div>
          <div v-if="notifyMessage" :class="notifyMessageIsError ? 'error-message' : 'success-message'" class="form-text mt-2">{{ notifyMessage }}</div>
      </div>

      <!-- Download Section -->
      <div v-if="jobDetails?.status === 'completed'" class="mb-3 d-grid">
        <button @click="downloadResults" class="btn btn-success" :disabled="isDownloadLoading">
           <span v-if="isDownloadLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
          {{ isDownloadLoading ? ' Preparing Download...' : 'Download Results' }}
        </button>
        <div v-if="downloadError" class="error-message text-center mt-2">{{ downloadError }}</div>
      </div>

      <!-- Stats Section (Rendered here when job is complete) -->
       <JobStats v-if="jobDetails?.status === 'completed' && jobStore.currentJobId" :job-id="jobStore.currentJobId" />

    </div>
  </div>
  <div v-else class="text-center text-muted mt-4">
      Upload a file to see job status.
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

// Use computed properties to react to store changes
const jobDetails = computed(() => jobStore.jobDetails);

const isLoading = ref(false); // Local loading state for polling maybe? Or rely on store?
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
  if (!stage) return jobDetails.value?.status === 'pending' ? 'Pending Start' : 'N/A'; // Show pending if status is pending
  const stageNames: { [key: string]: string } = {
    'ingestion': 'Ingesting File',
    'normalization': 'Normalizing Data',
    'classification_level_1': 'Classifying (Level 1)',
    'classification_level_2': 'Classifying (Level 2)',
    'classification_level_3': 'Classifying (Level 3)',
    'classification_level_4': 'Classifying (Level 4)',
    'search_unknown_vendors': 'Researching Vendors',
    'result_generation': 'Generating Results',
    // Completed/Failed handled by status primarily
  };
  // If completed or failed, use the status text instead of last stage
  if (jobDetails.value?.status === 'completed') return 'Completed';
  if (jobDetails.value?.status === 'failed') return 'Failed';
  return stageNames[stage] || stage;
});

const progressPercent = computed(() => {
    // Ensure progress is 100% if completed, 0% if pending/failed without progress
    const status = jobDetails.value?.status;
    const progress = jobDetails.value?.progress ?? 0;
    if (status === 'completed') return 100;
    // Keep progress as is if failed but had some progress
    // if (status === 'failed') return progress > 0 ? Math.round(progress * 100) : 0; // Or always 0 on fail?
    if (status === 'pending') return 0;
    return Math.round(progress * 100);
});

 const statusClass = computed(() => {
    switch (jobDetails.value?.status) {
        case 'completed': return 'status-completed';
        case 'failed': return 'status-failed';
        case 'processing': return 'status-processing';
        default: return 'status-pending';
    }
});

const progressClass = computed(() => {
  const status = jobDetails.value?.status;
  if (status === 'completed') return 'progress-bar bg-success';
  if (status === 'failed') return 'progress-bar bg-danger';
  // Keep animating if processing or pending with some progress
  if (status === 'processing' || (status === 'pending' && (jobDetails.value?.progress ?? 0) > 0)) {
      return 'progress-bar progress-bar-striped progress-bar-animated';
  }
  return 'progress-bar bg-secondary'; // Pending or unknown
});

const formatDateTime = (isoString: string | null | undefined): string => {
    if (!isoString) return 'N/A';
    try {
        // More readable format
        return new Date(isoString).toLocaleString(undefined, {
              year: 'numeric', month: 'short', day: 'numeric',
              hour: 'numeric', minute: '2-digit', hour12: true
          });
    } catch {
        return 'Invalid Date';
    }
};

const formattedCreatedAt = computed(() => formatDateTime(jobDetails.value?.created_at));
const formattedUpdatedAt = computed(() => formatDateTime(jobDetails.value?.updated_at));
const formattedEstimatedCompletion = computed(() => {
     const status = jobDetails.value?.status;
    if (status === 'completed' && jobDetails.value?.completed_at) {
        return formatDateTime(jobDetails.value.completed_at);
    }
    if (status === 'processing' && jobDetails.value?.estimated_completion) {
         return `${formatDateTime(jobDetails.value.estimated_completion)} (est.)`;
    }
    if (status === 'processing') return 'Calculating...';
    if (status === 'failed') return 'N/A';
    if (status === 'pending') return 'Pending Start';
    return 'N/A';
});

const canRequestNotify = computed(() => {
    const status = jobDetails.value?.status;
    return status === 'pending' || status === 'processing';
});

// --- Methods ---
const pollJobStatus = async (jobId: string) => {
  if (!jobId || jobStore.currentJobId !== jobId) {
      console.log(`Polling stopped or skipped for ${jobId} (current: ${jobStore.currentJobId})`);
      stopPolling(); // Ensure stopped if job ID mismatch
      return;
  }

  isLoading.value = true; // Track loading state

  try {
    console.log(`JobStatus: Polling status for ${jobId}`);
    const data = await apiService.getJobStatus(jobId);
    jobStore.updateJobDetails(data); // Update store -> updates computed props
    errorMessage.value = null; // Clear component-specific error on success

    // Handle final states - relies on watcher now
    // if (data.status === 'completed' || data.status === 'failed') {
    //   console.log(`Job ${jobId} finished polling with status: ${data.status}`);
    //   stopPolling();
    // }
  } catch (error: any) {
    console.error(`Error polling job status for ${jobId}:`, error);
    // Use error message from interceptor if available
    errorMessage.value = `Polling Error: ${error.message || 'Failed to fetch job status.'}`;
    // Stop polling on error to avoid spamming failing requests
    console.warn(`Stopping polling for ${jobId} due to error.`);
    stopPolling();

  } finally {
    isLoading.value = false;
  }
};

const startPolling = (jobId: string) => {
  if (!jobId) return;
  stopPolling(); // Clear existing interval
  console.log(`JobStatus: Starting polling for ${jobId}`);
  pollJobStatus(jobId); // Initial poll
  pollingIntervalId.value = window.setInterval(() => {
      // Extra check inside interval callback
      if (jobStore.currentJobId === jobId) {
           pollJobStatus(jobId)
      } else {
          console.log(`JobStatus: Interval skipped, job ID changed from ${jobId} to ${jobStore.currentJobId}`);
          stopPolling();
      }
  }, POLLING_INTERVAL);
};

const stopPolling = () => {
  if (pollingIntervalId.value !== null) {
    console.log(`JobStatus: Stopping polling interval ID: ${pollingIntervalId.value}`);
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
    notifyMessage.value = response.message || 'Notification request sent!';
    notificationEmail.value = ''; // Clear email on success
  } catch (error: any) {
    // Use error message from interceptor
    notifyMessage.value = `Error: ${error.message || 'Failed to send notification request.'}`;
    notifyMessageIsError.value = true;
  } finally {
    isNotifyLoading.value = false;
    // Optional: Hide message after a few seconds
    setTimeout(() => { notifyMessage.value = null; }, 5000);
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
    // Use error message from interceptor
    downloadError.value = `Download failed: ${error.message || 'Could not download results.'}`;
  } finally {
    isDownloadLoading.value = false;
  }
};

// --- Lifecycle Hooks ---
onMounted(() => {
  if (jobStore.currentJobId) {
     errorMessage.value = null; // Clear errors on mount/remount
    // Start polling only if the job isn't already in a final state
    if (jobDetails.value?.status !== 'completed' && jobDetails.value?.status !== 'failed') {
      startPolling(jobStore.currentJobId);
    }
  }
});

onUnmounted(() => {
  stopPolling();
});

// Watch for changes in the job ID from the store
watch(() => jobStore.currentJobId, (newJobId, oldJobId) => {
  console.log(`JobStatus: Watcher detected Job ID change from ${oldJobId} to ${newJobId}`);
  if (newJobId) {
     // Reset local component state when job ID changes
     errorMessage.value = null;
     downloadError.value = null;
     notifyMessage.value = null;
     notificationEmail.value = '';
     isDownloadLoading.value = false;
     isNotifyLoading.value = false;
     // Fetch initial state or start polling if not final
     if (jobStore.jobDetails?.status !== 'completed' && jobStore.jobDetails?.status !== 'failed') {
         startPolling(newJobId);
     } else {
         stopPolling(); // Ensure polling stopped if new job is already final
     }
  } else {
     stopPolling(); // Stop polling if job ID is cleared
  }
});

// Watch for status changes reported by polling to stop the interval
watch(() => jobStore.jobDetails?.status, (newStatus, oldStatus) => {
     if (newStatus && oldStatus !== newStatus) {
         console.log(`JobStatus: Watcher detected status change from ${oldStatus} to ${newStatus}`);
         if (newStatus === 'completed' || newStatus === 'failed') {
             console.log(`JobStatus: Status is final (${newStatus}). Stopping polling.`);
             stopPolling();
         }
         // Reset notification form if job completes/fails while user is looking?
         // if (!canRequestNotify.value) {
         //     notifyMessage.value = null; // Clear old notify messages if status changes
         // }
     }
});


</script>

<style scoped>
.card-header h4 {
    font-weight: 500;
}
.error-message { color: #dc3545; font-size: 0.875em; }
.success-message { color: #198754; font-size: 0.875em; }
/* Add more specific styles if needed */
</style>