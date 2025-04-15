<template>
    <div v-if="jobStore.currentJobId" class="bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
      <div class="bg-gray-100 text-gray-800 p-4 sm:p-5 border-b border-gray-200 flex justify-between items-center">
        <h4 class="text-xl font-semibold mb-0">Job Status</h4>
         <!-- Link to Parent Job (if this is a Review Job) -->
         <button v-if="jobDetails?.job_type === 'REVIEW' && jobDetails.parent_job_id"
                @click="viewParentJob"
                title="View Original Classification Job"
                class="text-xs inline-flex items-center px-2.5 py-1.5 border border-gray-300 shadow-sm font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-primary">
            <ArrowUturnLeftIcon class="h-4 w-4 mr-1.5 text-gray-500"/>
            View Original Job
        </button>
      </div>
      <div class="p-6 sm:p-8 space-y-6"> <!-- Increased spacing -->

        <!-- Error Message (Polling/General) -->
        <div v-if="errorMessage" class="p-3 bg-yellow-100 border border-yellow-300 text-yellow-800 rounded-md text-sm flex items-center">
            <ExclamationTriangleIcon class="h-5 w-5 mr-2 text-yellow-600 flex-shrink-0"/>
            <span>{{ errorMessage }}</span>
        </div>

        <!-- Reclassification Started Message -->
        <div v-if="showReclassifySuccessMessage && jobStore.lastReviewJobId" class="p-3 bg-green-100 border border-green-300 text-green-800 rounded-md text-sm flex items-center justify-between">
             <div class="flex items-center">
                 <CheckCircleIcon class="h-5 w-5 mr-2 text-green-600 flex-shrink-0"/>
                 <span>Re-classification job started successfully (ID: {{ jobStore.lastReviewJobId }}).</span>
             </div>
             <button @click="viewReviewJob(jobStore.lastReviewJobId!)" class="ml-4 text-xs font-semibold text-green-700 hover:text-green-900 underline">View Review Job</button>
        </div>


        <!-- Job ID & Status Row -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm border-b border-gray-100 pb-4">
          <div>
             <strong class="text-gray-600 block mb-1">Job ID:</strong>
             <span class="text-gray-900 font-mono text-xs bg-gray-100 px-2 py-1 rounded break-all">{{ jobStore.currentJobId }}</span>
             <span v-if="jobDetails?.job_type === 'REVIEW'" class="ml-2 inline-block px-1.5 py-0.5 rounded text-xs font-semibold bg-purple-100 text-purple-800 align-middle">REVIEW</span>
             <span v-else-if="jobDetails?.job_type === 'CLASSIFICATION'" class="ml-2 inline-block px-1.5 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800 align-middle">CLASSIFICATION</span>
          </div>
           <div class="flex items-center space-x-2">
             <strong class="text-gray-600">Status:</strong>
             <span class="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide" :class="statusBadgeClass">
                 {{ jobDetails?.status || 'Loading...' }}
             </span>
           </div>
        </div>

        <!-- Stage & Error (if failed) -->
        <div class="text-sm">
            <strong class="text-gray-600 block mb-1">Current Stage:</strong>
            <span class="text-gray-800 font-medium">{{ formattedStage }}</span>
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

        <!-- Download Section (Only for completed CLASSIFICATION jobs) -->
        <div v-if="jobDetails?.status === 'completed' && jobDetails?.job_type === 'CLASSIFICATION'" class="pt-5 border-t border-gray-100">
          <button @click="downloadResults"
                  class="w-full flex justify-center items-center px-4 py-2.5 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  :disabled="isDownloadLoading">
             <svg v-if="isDownloadLoading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
             </svg>
             <ArrowDownTrayIcon v-else class="h-5 w-5 mr-2 -ml-1" />
            {{ isDownloadLoading ? ' Preparing Download...' : 'Download Excel Results' }}
          </button>
          <p v-if="downloadError" class="mt-2 text-xs text-red-600 text-center">{{ downloadError }}</p>
        </div>

        <!-- Stats Section (Rendered within JobStatus when complete) -->
         <JobStats v-if="jobDetails?.status === 'completed' && jobDetails?.id" :job-id="jobDetails.id" />

        <!-- ***** UPDATED: Conditional Detailed Results Table Section ***** -->
        <!-- Show CLASSIFICATION results table (potentially integrated view) -->
        <JobResultsTable
            v-if="jobDetails?.status === 'completed' && jobDetails?.id && jobDetails?.job_type === 'CLASSIFICATION'"
            :original-results="jobStore.jobResults as JobResultItem[] | null"
            :review-results="jobStore.relatedReviewResults"
            :loading="jobStore.resultsLoading"
            :error="jobStore.resultsError"
            :target-level="jobDetails.target_level || 5"
            @submit-flags="handleSubmitFlags" /> <!-- Listen for submit event -->

        <!-- Show REVIEW results table -->
        <ReviewResultsTable
            v-if="jobDetails?.status === 'completed' && jobDetails?.id && jobDetails?.job_type === 'REVIEW'"
            :results="jobStore.jobResults as ReviewResultItem[] | null"
            :loading="jobStore.resultsLoading"
            :error="jobStore.resultsError"
            :target-level="jobDetails.target_level || 5"
            @submit-flags="handleSubmitFlags" /> <!-- Listen for submit event -->
        <!-- ***** END UPDATED Section ***** -->

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
  // Import store and types (Removed JobDetails from here)
  import { useJobStore, type JobResultItem, type ReviewResultItem } from '@/stores/job';
  import JobStats from './JobStats.vue';
  // Import both results tables
  import JobResultsTable from './JobResultsTable.vue';
  import ReviewResultsTable from './ReviewResultsTable.vue';
  import { EnvelopeIcon, ArrowDownTrayIcon, ExclamationTriangleIcon, ArrowUturnLeftIcon, CheckCircleIcon } from '@heroicons/vue/20/solid';

  const POLLING_INTERVAL = 5000; // Poll every 5 seconds
  const jobStore = useJobStore();
  const jobDetails = computed(() => jobStore.jobDetails); // Use jobDetails directly from the store
  const isLoading = ref(false); // Tracks if a poll request is currently in flight
  const errorMessage = ref<string | null>(null); // Stores polling or general errors
  const pollingIntervalId = ref<number | null>(null); // Stores the ID from setInterval
  const showReclassifySuccessMessage = ref(false); // Control visibility of success message

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
    const stageNames: { [key: string]: string } = {
      'ingestion': 'Ingesting File', 'normalization': 'Normalizing Data',
      'classification_level_1': 'Classifying (L1)', 'classification_level_2': 'Classifying (L2)',
      'classification_level_3': 'Classifying (L3)', 'classification_level_4': 'Classifying (L4)',
      'classification_level_5': 'Classifying (L5)', 'search_unknown_vendors': 'Researching Vendors',
      'reclassification': 'Re-classifying', 'result_generation': 'Generating Results',
      'pending': 'Pending Start',
    };
    return stageNames[stage] || stage;
  });

  const progressPercent = computed(() => {
    const status = jobDetails.value?.status;
    const progress = jobDetails.value?.progress ?? 0;
    if (status === 'completed') return 100;
    if (status === 'pending') return 0;
    return Math.max(0, Math.min(100, Math.round(progress * 100)));
  });

  const statusBadgeClass = computed(() => {
      switch (jobDetails.value?.status) {
          case 'completed': return 'bg-green-100 text-green-800';
          case 'failed': return 'bg-red-100 text-red-800';
          case 'processing': return 'bg-blue-100 text-blue-800 animate-pulse';
          default: return 'bg-gray-100 text-gray-800';
      }
  });

  const progressColorClass = computed(() => {
    const status = jobDetails.value?.status;
    if (status === 'completed') return 'bg-green-500';
    if (status === 'failed') return 'bg-red-500';
    return 'bg-primary animate-pulse';
  });

  const formatDateTime = (isoString: string | null | undefined): string => {
      if (!isoString) return 'N/A';
      try {
          return new Date(isoString).toLocaleString(undefined, {
              year: 'numeric', month: 'short', day: 'numeric',
              hour: 'numeric', minute: '2-digit', hour12: true
          });
      } catch { return 'Invalid Date'; }
  };

  const formattedCreatedAt = computed(() => formatDateTime(jobDetails.value?.created_at));
  const formattedUpdatedAt = computed(() => formatDateTime(jobDetails.value?.updated_at));

  const formattedEstimatedCompletion = computed(() => {
      const status = jobDetails.value?.status;
      if (status === 'completed' && jobDetails.value?.completed_at) {
          return formatDateTime(jobDetails.value.completed_at);
      }
      const estCompletion = jobDetails.value?.estimated_completion;
      if (status === 'processing' && estCompletion) {
          return `${formatDateTime(estCompletion)} (est.)`;
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
  const pollJobStatus = async (jobId: string | null | undefined) => {
     if (!jobId || jobStore.currentJobId !== jobId) {
         console.log(`JobStatus: [pollJobStatus] Stopping polling. Reason: Job ID mismatch or null. (Poll ID: ${jobId}, Store ID: ${jobStore.currentJobId})`);
         stopPolling();
         return;
     }
     if (isLoading.value) {
         console.log(`JobStatus: [pollJobStatus] Skipping poll for ${jobId} - already in progress.`);
         return;
     }

     isLoading.value = true;
     console.log(`JobStatus: [pollJobStatus] Polling status for job ${jobId}...`);
    try {
        const data = await apiService.getJobStatus(jobId);
        if (jobStore.currentJobId === jobId) {
            console.log(`JobStatus: [pollJobStatus] Received status for ${jobId}: Status=${data.status}, Progress=${data.progress}, Type=${data.job_type}`);
            const previousStatus = jobStore.jobDetails?.status; // Store previous status before update
            jobStore.updateJobDetails(data);
            errorMessage.value = null;

            // Check if job just completed or failed
            const justCompleted = data.status === 'completed' && previousStatus !== 'completed';
            const justFailed = data.status === 'failed' && previousStatus !== 'failed';

            if (justCompleted || justFailed) {
                console.log(`JobStatus: [pollJobStatus] Job ${jobId} reached terminal state (${data.status}). Stopping polling.`);
                stopPolling();
                if (justCompleted) {
                    console.log(`JobStatus: [pollJobStatus] Job ${jobId} completed. Triggering fetchCurrentJobResults.`);
                    // Use the new action to fetch results (handles both types)
                    if (!jobStore.resultsLoading && !jobStore.jobResults && !jobStore.relatedReviewResults) { // Check both result states
                         jobStore.fetchCurrentJobResults();
                    } else {
                         console.log(`JobStatus: [pollJobStatus] Job ${jobId} completed, but results already loading or present. Skipping fetch.`);
                    }
                }
            }
        } else {
             console.log(`JobStatus: [pollJobStatus] Job ID changed during API call for ${jobId}. Ignoring stale data.`);
        }
    } catch (error: any) {
        console.error(`JobStatus: [pollJobStatus] Error polling status for ${jobId}:`, error);
        if (jobStore.currentJobId === jobId) {
            errorMessage.value = `Polling Error: ${error.message || 'Failed to fetch status.'}`;
        }
        stopPolling();
    } finally {
        if (jobStore.currentJobId === jobId) {
            isLoading.value = false;
        }
    }
  };

  const startPolling = (jobId: string | null | undefined) => {
    if (!jobId) {
        console.log("JobStatus: [startPolling] Cannot start polling, no jobId provided.");
        return;
    }
    stopPolling();
    console.log(`JobStatus: [startPolling] Starting polling for job ${jobId}.`);
    pollJobStatus(jobId); // Poll immediately

    pollingIntervalId.value = window.setInterval(() => {
        console.log(`JobStatus: [setInterval] Checking poll condition for ${jobId}. Current store ID: ${jobStore.currentJobId}, Status: ${jobStore.jobDetails?.status}`);
        if (jobStore.currentJobId === jobId && jobStore.jobDetails?.status !== 'completed' && jobStore.jobDetails?.status !== 'failed') {
            pollJobStatus(jobId);
        } else {
            console.log(`JobStatus: [setInterval] Condition not met for job ${jobId}, stopping polling.`);
            stopPolling();
        }
    }, POLLING_INTERVAL);
  };

  const stopPolling = () => {
    if (pollingIntervalId.value !== null) {
        console.log(`JobStatus: [stopPolling] Stopping polling interval ID ${pollingIntervalId.value}.`);
        clearInterval(pollingIntervalId.value);
        pollingIntervalId.value = null;
    }
  };

  const requestNotification = async () => {
     const currentId = jobDetails.value?.id;
     if (!currentId || !notificationEmail.value) return;
     isNotifyLoading.value = true;
     notifyMessage.value = null;
     notifyMessageIsError.value = false;
     console.log(`JobStatus: Requesting notification for ${currentId} to ${notificationEmail.value}`);
    try {
        const response = await apiService.requestNotification(currentId, notificationEmail.value);
        console.log(`JobStatus: Notification request successful:`, response);
        notifyMessage.value = response.message || 'Notification request sent!';
        notificationEmail.value = '';
    } catch (error: any) {
        console.error(`JobStatus: Notification request failed:`, error);
        notifyMessage.value = `Error: ${error.message || 'Failed to send request.'}`;
        notifyMessageIsError.value = true;
    } finally {
        isNotifyLoading.value = false;
        setTimeout(() => { notifyMessage.value = null; }, 5000);
    }
  };

  const downloadResults = async () => {
     const currentId = jobDetails.value?.id;
     if (!currentId) return;
     isDownloadLoading.value = true;
     downloadError.value = null;
     console.log(`JobStatus: Attempting download for ${currentId}`);
    try {
        const { blob, filename } = await apiService.downloadResults(currentId);
        console.log(`JobStatus: Download blob received, filename: ${filename}`);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none'; a.href = url; a.download = filename;
        document.body.appendChild(a); a.click();
        window.URL.revokeObjectURL(url); document.body.removeChild(a);
        console.log(`JobStatus: Download triggered for ${filename}`);
    } catch (error: any) {
        console.error(`JobStatus: Download failed:`, error);
        downloadError.value = `Download failed: ${error.message || 'Could not download results.'}`;
    } finally {
        isDownloadLoading.value = false;
    }
  };

  // --- Reclassification Submission Handler ---
  const handleSubmitFlags = async () => {
    console.log("JobStatus: Handling submit flags event...");
    const reviewJobId = await jobStore.submitFlagsForReview();
    if (reviewJobId) {
        showReclassifySuccessMessage.value = true;
        setTimeout(() => { showReclassifySuccessMessage.value = false; }, 7000);
        jobStore.fetchJobHistory(); // Refresh history list
    } else {
        console.log("JobStatus: Flag submission failed (error handled in store/table).");
        // Optionally show a generic error message here if needed, though specific errors are better shown near the button
    }
  };

  // --- Navigation ---
  const viewParentJob = () => {
      if (jobDetails.value?.parent_job_id) {
          jobStore.setCurrentJobId(jobDetails.value.parent_job_id);
      }
  };

  const viewReviewJob = (reviewJobId: string) => {
       jobStore.setCurrentJobId(reviewJobId);
       showReclassifySuccessMessage.value = false; // Hide message on navigation
  };

  // --- Fetch Initial Data Function ---
  const fetchInitialData = (jobId: string) => {
      errorMessage.value = null; // Clear previous errors
      const currentDetails = jobStore.jobDetails;

      // Fetch details if they are missing OR if the ID matches but type/status might be stale
      if (!currentDetails || currentDetails.id !== jobId) {
           console.log(`JobStatus: Fetching initial details and starting polling for ${jobId}`);
           startPolling(jobId); // Poll will fetch details
      } else if (currentDetails.status === 'completed') {
           console.log(`JobStatus: Job ${jobId} already completed. Fetching results if needed.`);
           stopPolling();
           // Use the new action to fetch results
           if (!jobStore.resultsLoading && !jobStore.jobResults && !jobStore.relatedReviewResults) {
                jobStore.fetchCurrentJobResults();
           }
      } else if (currentDetails.status === 'failed') {
           console.log(`JobStatus: Job ${jobId} already failed. Not polling or fetching results.`);
           stopPolling();
      } else {
           // Status is pending or processing, start polling
           console.log(`JobStatus: Job ${jobId} is ${currentDetails.status}. Starting polling.`);
           startPolling(jobId);
      }
  };

  // --- Lifecycle Hooks ---
  onMounted(() => {
      console.log(`JobStatus: Mounted. Current job ID from store: ${jobStore.currentJobId}`);
      if (jobStore.currentJobId) {
          fetchInitialData(jobStore.currentJobId);
      }
  });

  onUnmounted(() => {
      console.log("JobStatus: Unmounted, stopping polling.");
      stopPolling();
  });

  // --- Watchers ---
  watch(() => jobStore.currentJobId, (newJobId, oldJobId) => {
      console.log(`JobStatus: Watched currentJobId changed from ${oldJobId} to: ${newJobId}`);
      showReclassifySuccessMessage.value = false; // Hide success message on job change
      if (newJobId) {
          // Reset component state related to the specific job
          errorMessage.value = null;
          downloadError.value = null;
          notifyMessage.value = null;
          notificationEmail.value = '';
          isDownloadLoading.value = false;
          isNotifyLoading.value = false;
          // Fetch data for the new job
          fetchInitialData(newJobId);
      } else {
          // Job ID was cleared
          console.log("JobStatus: Job ID cleared, stopping polling.");
          stopPolling();
      }
  }, { immediate: false }); // Don't run immediately on mount, let onMounted handle initial load

  // Watch for the job status changing to completed (handles updates from polling)
  // This watcher seems redundant now as the polling logic handles stopping and fetching results.
  // Keep it for now as a potential backup, but consider removing if polling logic proves robust.
  watch(() => jobStore.jobDetails?.status, (newStatus, oldStatus) => {
      const currentId = jobStore.currentJobId;
      if (!currentId || newStatus === oldStatus) return; // Only act on change for the current job

      console.log(`JobStatus: Watched job status changed from ${oldStatus} to: ${newStatus} for job ${currentId}`);

      if (newStatus === 'completed') {
          console.log(`JobStatus: Job ${currentId} completed (detected by status watcher). Ensuring results are fetched.`);
          stopPolling(); // Ensure polling is stopped
          // Use the new action to fetch results if not already loading/present
          if (!jobStore.resultsLoading && !jobStore.jobResults && !jobStore.relatedReviewResults) {
            jobStore.fetchCurrentJobResults();
          }
      } else if (newStatus === 'failed') {
          console.log(`JobStatus: Job ${currentId} failed (detected by status watcher). Ensuring polling is stopped.`);
          stopPolling();
      }
  });

  </script>