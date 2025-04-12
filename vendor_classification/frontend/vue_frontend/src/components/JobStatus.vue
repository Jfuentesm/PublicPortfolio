<template>
    <div v-if="jobStore.currentJobId" class="bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
      <div class="bg-gray-100 text-gray-800 p-4 sm:p-5 border-b border-gray-200">
        <h4 class="text-xl font-semibold mb-0">Job Status</h4>
      </div>
      <div class="p-6 sm:p-8 space-y-6"> <!-- Increased spacing -->

        <!-- Error Message -->
        <div v-if="errorMessage" class="p-3 bg-yellow-100 border border-yellow-300 text-yellow-800 rounded-md text-sm flex items-center">
            <ExclamationTriangleIcon class="h-5 w-5 mr-2 text-yellow-600 flex-shrink-0"/>
            <span>{{ errorMessage }}</span>
        </div>

        <!-- Job ID & Status Row -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm border-b border-gray-100 pb-4">
          <div>
             <strong class="text-gray-600 block mb-1">Job ID:</strong>
             <!-- Display the full ID for clarity during debugging -->
             <span class="text-gray-900 font-mono text-xs bg-gray-100 px-2 py-1 rounded break-all">{{ jobStore.currentJobId }}</span>
          </div>
           <div class="flex items-center space-x-2">
             <strong class="text-gray-600">Status:</strong>
             <span class="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide" :class="statusBadgeClass">
                 <!-- Use jobDetails.status directly -->
                 {{ jobDetails?.status || 'Loading...' }}
             </span>
           </div>
        </div>

        <!-- Stage & Error (if failed) -->
        <div class="text-sm">
            <strong class="text-gray-600 block mb-1">Current Stage:</strong>
            <span class="text-gray-800 font-medium">{{ formattedStage }}</span>
            <!-- Use jobDetails.error_message -->
            <div v-if="jobDetails?.status === 'failed' && jobDetails?.error_message" class="mt-3 p-4 bg-red-50 border border-red-200 text-red-800 rounded-md text-xs shadow-sm">
              <strong class="block mb-1 font-semibold">Error Details:</strong>
              <p class="whitespace-pre-wrap">{{ jobDetails.error_message }}</p> <!-- Preserve whitespace -->
            </div>
        </div>

        <!-- Progress Bar -->
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-1.5">Progress:</label>
          <div class="w-full bg-gray-200 rounded-full h-3 overflow-hidden"> <!-- Slimmer progress bar -->
            <div
              class="h-3 rounded-full transition-all duration-500 ease-out"
              :class="progressColorClass"
              :style="{ width: progressPercent + '%' }"
              ></div>
          </div>
          <div class="text-right text-xs text-gray-500 mt-1">{{ progressPercent }}% Complete</div>
        </div>

        <!-- Timestamps Row -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-gray-500 border-t border-gray-100 pt-5">
            <div>
                 <strong class="block text-gray-600 mb-0.5">Created:</strong>
                 <span>{{ formattedCreatedAt }}</span>
            </div>
            <div>
                 <strong class="block text-gray-600 mb-0.5">Updated:</strong>
                 <span>{{ formattedUpdatedAt }}</span>
            </div>
             <div>
                <strong class="block text-gray-600 mb-0.5">Est. Completion:</strong>
                <span>{{ formattedEstimatedCompletion }}</span>
            </div>
        </div>

        <!-- Notification Section -->
        <div v-if="canRequestNotify" class="pt-5 border-t border-gray-100">
            <label for="notificationEmail" class="block text-sm font-medium text-gray-700 mb-1.5">Get Notified Upon Completion</label>
            <div class="flex flex-col sm:flex-row sm:space-x-2">
                <input type="email"
                       class="mb-2 sm:mb-0 flex-grow block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm disabled:opacity-60 disabled:bg-gray-100"
                       id="notificationEmail"
                       placeholder="Enter your email"
                       v-model="notificationEmail"
                       :disabled="isNotifyLoading" />
                <button
                    type="button"
                    @click="requestNotification"
                    :disabled="isNotifyLoading || !notificationEmail"
                    class="w-full sm:w-auto inline-flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <svg v-if="isNotifyLoading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                       <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                       <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                     <EnvelopeIcon v-else class="h-4 w-4 mr-2 -ml-1 text-gray-500"/>
                    {{ isNotifyLoading ? 'Sending...' : 'Notify Me' }}
                </button>
            </div>
            <!-- Notification Feedback -->
            <p v-if="notifyMessage" :class="notifyMessageIsError ? 'text-red-600' : 'text-green-600'" class="mt-2 text-xs">{{ notifyMessage }}</p>
        </div>

        <!-- Download Section -->
        <div v-if="jobDetails?.status === 'completed'" class="pt-5 border-t border-gray-100">
          <button @click="downloadResults"
                  class="w-full flex justify-center items-center px-4 py-2.5 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  :disabled="isDownloadLoading">
             <!-- Spinner SVG -->
             <svg v-if="isDownloadLoading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
             </svg>
             <!-- Download Icon -->
             <ArrowDownTrayIcon v-else class="h-5 w-5 mr-2 -ml-1" />
            {{ isDownloadLoading ? ' Preparing Download...' : 'Download Excel Results' }} <!-- Updated Text -->
          </button>
          <p v-if="downloadError" class="mt-2 text-xs text-red-600 text-center">{{ downloadError }}</p>
        </div>

        <!-- Stats Section (Rendered within JobStatus when complete) -->
         <!-- Use jobDetails.id -->
         <JobStats v-if="jobDetails?.status === 'completed' && jobDetails?.id" :job-id="jobDetails.id" />

        <!-- ***** NEW: Detailed Results Table Section ***** -->
        <JobResultsTable
            v-if="jobDetails?.status === 'completed' && jobDetails?.id"
            :results="jobStore.jobResults"
            :loading="jobStore.resultsLoading"
            :error="jobStore.resultsError"
        />
        <!-- ***** END NEW Section ***** -->

      </div>
    </div>
      <div v-else class="text-center py-10 text-gray-500">
        <!-- Message shown when no job is selected -->
        <!-- Select a job from the history or upload a new file. -->
      </div>
  </template>

  <script setup lang="ts">
  import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
  import apiService from '@/services/api';
  import { useJobStore, type JobDetails } from '@/stores/job';
  import JobStats from './JobStats.vue';
  import JobResultsTable from './JobResultsTable.vue'; // Import the new component
  import { EnvelopeIcon, ArrowDownTrayIcon, ExclamationTriangleIcon } from '@heroicons/vue/20/solid';

  const POLLING_INTERVAL = 5000; // Poll every 5 seconds
  const jobStore = useJobStore();
  // Use jobDetails directly from the store
  const jobDetails = computed(() => jobStore.jobDetails);
  const isLoading = ref(false); // Tracks if a poll request is currently in flight
  const errorMessage = ref<string | null>(null); // Stores polling or general errors
  const pollingIntervalId = ref<number | null>(null); // Stores the ID from setInterval

  // --- Notification State ---
  const notificationEmail = ref('');
  const isNotifyLoading = ref(false);
  const notifyMessage = ref<string | null>(null);
  const notifyMessageIsError = ref(false);

  // --- Download State ---
  const isDownloadLoading = ref(false);
  const downloadError = ref<string | null>(null);

  // --- Computed Properties ---
  const formattedStage = computed(() => {
    const stage = jobDetails.value?.current_stage;
    const status = jobDetails.value?.status;
    if (status === 'completed') return 'Completed';
    if (status === 'failed') return 'Failed';
    if (status === 'pending') return 'Pending Start';
    if (!stage) return 'Loading...';

    // Map internal stage names to user-friendly display names
    const stageNames: { [key: string]: string } = {
      'ingestion': 'Ingesting File',
      'normalization': 'Normalizing Data',
      'classification_level_1': 'Classifying (L1)',
      'classification_level_2': 'Classifying (L2)',
      'classification_level_3': 'Classifying (L3)',
      'classification_level_4': 'Classifying (L4)',
      'classification_level_5': 'Classifying (L5)', // Added L5
      'search_unknown_vendors': 'Researching Vendors',
      'result_generation': 'Generating Results',
    };
    return stageNames[stage] || stage; // Fallback to raw stage name if not mapped
  });

  const progressPercent = computed(() => {
    const status = jobDetails.value?.status;
    const progress = jobDetails.value?.progress ?? 0;
    if (status === 'completed') return 100;
    if (status === 'pending') return 0; // Show 0% for pending
    // Ensure progress is between 0 and 100
    return Math.max(0, Math.min(100, Math.round(progress * 100)));
  });

  const statusBadgeClass = computed(() => {
      switch (jobDetails.value?.status) {
          case 'completed': return 'bg-green-100 text-green-800';
          case 'failed': return 'bg-red-100 text-red-800';
          case 'processing': return 'bg-blue-100 text-blue-800 animate-pulse'; // Add pulse for processing
          default: return 'bg-gray-100 text-gray-800'; // Pending or loading
      }
  });

  const progressColorClass = computed(() => {
    const status = jobDetails.value?.status;
    if (status === 'completed') return 'bg-green-500';
    if (status === 'failed') return 'bg-red-500';
    // Use primary color and pulse animation for processing/pending
    return 'bg-primary animate-pulse';
  });

  const formatDateTime = (isoString: string | null | undefined): string => {
      if (!isoString) return 'N/A';
      try {
          // Use user's locale and common options
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
      // Assuming backend provides 'estimated_completion' during processing
      // --- CHECK FIELD NAME ---
      // Check if the field is 'estimated_completion' or something else in JobDetails
      const estCompletion = jobDetails.value?.estimated_completion; // Use the actual field name
      if (status === 'processing' && estCompletion) {
          return `${formatDateTime(estCompletion)} (est.)`;
      }
      // --- END CHECK ---
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
  const pollJobStatus = async (jobId: string | null | undefined) => {
     // Check if we should still be polling this job
     if (!jobId || jobStore.currentJobId !== jobId) {
         console.log(`JobStatus: [pollJobStatus] Stopping polling because jobId (${jobId}) doesn't match store (${jobStore.currentJobId}) or is null.`); // LOGGING
         stopPolling();
         return;
     }

     // Avoid concurrent polls
     if (isLoading.value) {
         console.log(`JobStatus: [pollJobStatus] Skipping poll for ${jobId} as another poll is already in progress.`); // LOGGING
         return;
     }

     isLoading.value = true;
     console.log(`JobStatus: [pollJobStatus] Polling status for job ${jobId}...`); // LOGGING
    try {
        const data = await apiService.getJobStatus(jobId);
        // IMPORTANT: Check if the job ID is still the current one *after* the API call returns
        if (jobStore.currentJobId === jobId) {
            console.log(`JobStatus: [pollJobStatus] Received status data for ${jobId}: Status=${data.status}, Progress=${data.progress}, Stage=${data.current_stage}`); // LOGGING
            jobStore.updateJobDetails(data); // Update the store
            errorMessage.value = null; // Clear previous errors on successful poll

            // Stop polling if job is completed or failed
            if (data.status === 'completed' || data.status === 'failed') {
                console.log(`JobStatus: [pollJobStatus] Job ${jobId} reached terminal state (${data.status}). Stopping polling.`); // LOGGING
                stopPolling();
                // --- NEW: Trigger results fetch if completed ---
                if (data.status === 'completed') {
                    console.log(`JobStatus: [pollJobStatus] Job ${jobId} completed. Triggering fetchJobResults.`); // LOGGING
                    jobStore.fetchJobResults(jobId); // Fetch detailed results
                }
                // --- END NEW ---
            }
        } else {
             console.log(`JobStatus: [pollJobStatus] Job ID changed from ${jobId} to ${jobStore.currentJobId} during API call. Ignoring stale data.`); // LOGGING
             // Don't update the store with stale data
        }
    } catch (error: any) {
        console.error(`JobStatus: [pollJobStatus] Error polling status for ${jobId}:`, error); // LOGGING
        // Only set error if the failed poll was for the *current* job ID
        if (jobStore.currentJobId === jobId) {
            errorMessage.value = `Polling Error: ${error.message || 'Failed to fetch status.'}`;
        }
        // Consider retrying after a longer interval before stopping completely
        stopPolling(); // Stop polling on error for now
    } finally {
        // Only set isLoading to false if the poll was for the current job
        if (jobStore.currentJobId === jobId) {
            isLoading.value = false;
        }
    }
  };

  const startPolling = (jobId: string | null | undefined) => {
    if (!jobId) {
        console.log("JobStatus: [startPolling] Cannot start polling, no jobId provided."); // LOGGING
        return;
    }
    stopPolling(); // Ensure any existing polling is stopped first
    console.log(`JobStatus: [startPolling] Starting polling for job ${jobId}.`); // LOGGING
    pollJobStatus(jobId); // Poll immediately

    pollingIntervalId.value = window.setInterval(() => {
        console.log(`JobStatus: [setInterval] Checking poll condition for ${jobId}. Current store ID: ${jobStore.currentJobId}, Status: ${jobStore.jobDetails?.status}`); // LOGGING
        // Check condition inside interval as well
        if (jobStore.currentJobId === jobId && jobStore.jobDetails?.status !== 'completed' && jobStore.jobDetails?.status !== 'failed') {
            pollJobStatus(jobId);
        } else {
            console.log(`JobStatus: [setInterval] Condition not met, stopping polling.`); // LOGGING
            // Stop if job ID changed or job finished between polls
            stopPolling();
        }
    }, POLLING_INTERVAL);
  };

  const stopPolling = () => {
    if (pollingIntervalId.value !== null) {
        console.log(`JobStatus: [stopPolling] Stopping polling interval ID ${pollingIntervalId.value}.`); // LOGGING
        clearInterval(pollingIntervalId.value);
        pollingIntervalId.value = null;
    } else {
        // console.log(`JobStatus: [stopPolling] No active polling interval to stop.`); // LOGGING (Optional)
    }
  };

  const requestNotification = async () => {
     // Use jobDetails.id
     const currentId = jobDetails.value?.id;
     if (!currentId || !notificationEmail.value) return;
     isNotifyLoading.value = true;
     notifyMessage.value = null;
     notifyMessageIsError.value = false;
     console.log(`JobStatus: Requesting notification for ${currentId} to ${notificationEmail.value}`); // LOGGING
    try {
        const response = await apiService.requestNotification(currentId, notificationEmail.value);
        console.log(`JobStatus: Notification request successful:`, response); // LOGGING
        notifyMessage.value = response.message || 'Notification request sent!';
        notificationEmail.value = ''; // Clear input on success
    } catch (error: any) {
        console.error(`JobStatus: Notification request failed:`, error); // LOGGING
        notifyMessage.value = `Error: ${error.message || 'Failed to send request.'}`;
        notifyMessageIsError.value = true;
    } finally {
        isNotifyLoading.value = false;
        // Clear message after a delay
        setTimeout(() => { notifyMessage.value = null; }, 5000);
    }
  };

  const downloadResults = async () => {
     // Use jobDetails.id
     const currentId = jobDetails.value?.id;
     if (!currentId) return;
     isDownloadLoading.value = true;
     downloadError.value = null;
     console.log(`JobStatus: Attempting download for ${currentId}`); // LOGGING
    try {
        const { blob, filename } = await apiService.downloadResults(currentId);
        console.log(`JobStatus: Download blob received, filename: ${filename}`); // LOGGING
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        console.log(`JobStatus: Download triggered for ${filename}`); // LOGGING
    } catch (error: any) {
        console.error(`JobStatus: Download failed:`, error); // LOGGING
        downloadError.value = `Download failed: ${error.message || 'Could not download results.'}`;
    } finally {
        isDownloadLoading.value = false;
    }
  };

  // --- Lifecycle Hooks ---
  onMounted(() => {
      console.log(`JobStatus: Mounted. Current job ID from store: ${jobStore.currentJobId}`); // LOGGING
      if (jobStore.currentJobId) {
          errorMessage.value = null;
          // Fetch initial details if not already present or if status is unknown/stale
          // Use jobDetails.id for comparison
          const currentDetails = jobStore.jobDetails;
          if (!currentDetails || currentDetails.id !== jobStore.currentJobId) {
              console.log(`JobStatus: Fetching initial details and starting polling for ${jobStore.currentJobId}`); // LOGGING
              startPolling(jobStore.currentJobId);
          } else if (currentDetails.status === 'completed') {
              console.log(`JobStatus: Job ${jobStore.currentJobId} already completed. Fetching results.`); // LOGGING
              stopPolling(); // Ensure polling is stopped
              jobStore.fetchJobResults(jobStore.currentJobId); // Fetch results if already completed on mount
          } else if (currentDetails.status === 'failed') {
              console.log(`JobStatus: Job ${jobStore.currentJobId} already failed. Not polling or fetching results.`); // LOGGING
              stopPolling(); // Ensure polling is stopped
          } else {
              // Status is pending or processing, start polling
              console.log(`JobStatus: Job ${jobStore.currentJobId} is ${currentDetails.status}. Starting polling.`); // LOGGING
              startPolling(jobStore.currentJobId);
          }
      }
  });


  onUnmounted(() => {
      console.log("JobStatus: Unmounted, stopping polling."); // LOGGING
      stopPolling();
  });

  // --- Watchers ---
  // Watch for changes in the store's currentJobId
  watch(() => jobStore.currentJobId, (newJobId: string | null | undefined) => {
      console.log(`JobStatus: Watched currentJobId changed to: ${newJobId}`); // LOGGING
      if (newJobId) {
          // Reset component state when job ID changes
          errorMessage.value = null;
          downloadError.value = null;
          notifyMessage.value = null;
          notificationEmail.value = '';
          isDownloadLoading.value = false;
          isNotifyLoading.value = false;

          // Fetch details or start polling if needed for the new job
          const currentDetails = jobStore.jobDetails;
          if (!currentDetails || currentDetails.id !== newJobId) {
               console.log(`JobStatus: Fetching initial details and starting polling due to job ID change to ${newJobId}`); // LOGGING
               startPolling(newJobId);
          } else if (currentDetails.status === 'completed') {
               console.log(`JobStatus: Job ${newJobId} already completed. Fetching results.`); // LOGGING
               stopPolling(); // Ensure polling is stopped
               jobStore.fetchJobResults(newJobId); // Fetch results if already completed
          } else if (currentDetails.status === 'failed') {
               console.log(`JobStatus: Job ${newJobId} already failed. Not polling or fetching results.`); // LOGGING
               stopPolling(); // Ensure polling is stopped
          } else {
               // Status is pending or processing, start polling
               console.log(`JobStatus: Job ${newJobId} is ${currentDetails.status}. Starting polling.`); // LOGGING
               startPolling(newJobId);
          }
      } else {
          // Job ID was cleared
          console.log("JobStatus: Job ID cleared, stopping polling."); // LOGGING
          stopPolling();
      }
  });

  // Watch for the job status changing to a terminal state (this handles updates from polling)
  watch(() => jobStore.jobDetails?.status, (newStatus: JobDetails['status'] | undefined, oldStatus) => {
      const currentId = jobStore.currentJobId;
      if (!currentId) return; // Don't do anything if no job is selected

      console.log(`JobStatus: Watched job status changed from ${oldStatus} to: ${newStatus} for job ${currentId}`); // LOGGING

      if (newStatus === 'completed' && oldStatus !== 'completed') {
          console.log(`JobStatus: Job ${currentId} just completed. Stopping polling and fetching results.`); // LOGGING
          stopPolling();
          jobStore.fetchJobResults(currentId); // Fetch detailed results when status changes to completed
      } else if (newStatus === 'failed' && oldStatus !== 'failed') {
          console.log(`JobStatus: Job ${currentId} just failed. Stopping polling.`); // LOGGING
          stopPolling();
      }
  });

  </script>