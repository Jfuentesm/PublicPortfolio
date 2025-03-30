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
           <span class="text-gray-900 font-mono text-xs bg-gray-100 px-2 py-1 rounded">{{ jobStore.currentJobId }}</span>
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
          {{ isDownloadLoading ? ' Preparing Download...' : 'Download Results' }}
        </button>
        <p v-if="downloadError" class="mt-2 text-xs text-red-600 text-center">{{ downloadError }}</p>
      </div>

      <!-- Stats Section (Rendered within JobStatus when complete) -->
       <JobStats v-if="jobDetails?.status === 'completed' && jobStore.currentJobId" :job-id="jobStore.currentJobId" />

    </div>
  </div>
</template>

<script setup lang="ts">
// Script content remains the same
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import apiService from '@/services/api';
import { useJobStore, type JobDetails } from '@/stores/job';
import JobStats from './JobStats.vue';
import { EnvelopeIcon, ArrowDownTrayIcon, ExclamationTriangleIcon } from '@heroicons/vue/20/solid';

const POLLING_INTERVAL = 5000;
const POLLING_RETRY_INTERVAL = 15000;
const jobStore = useJobStore();
const jobDetails = computed(() => jobStore.jobDetails);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const pollingIntervalId = ref<number | null>(null);
const notificationEmail = ref('');
const isNotifyLoading = ref(false);
const notifyMessage = ref<string | null>(null);
const notifyMessageIsError = ref(false);
const isDownloadLoading = ref(false);
const downloadError = ref<string | null>(null);

const formattedStage = computed(() => {
  const stage = jobDetails.value?.current_stage; const status = jobDetails.value?.status;
  if (status === 'completed') return 'Completed'; if (status === 'failed') return 'Failed'; if (status === 'pending') return 'Pending Start'; if (!stage) return 'Loading...';
  const stageNames: { [key: string]: string } = { 'ingestion': 'Ingesting File', 'normalization': 'Normalizing Data', 'classification_level_1': 'Classifying (L1)', 'classification_level_2': 'Classifying (L2)', 'classification_level_3': 'Classifying (L3)', 'classification_level_4': 'Classifying (L4)', 'search_unknown_vendors': 'Researching Vendors', 'result_generation': 'Generating Results', };
  return stageNames[stage] || stage;
 });
const progressPercent = computed(() => {
  const status = jobDetails.value?.status; const progress = jobDetails.value?.progress ?? 0;
  if (status === 'completed') return 100; if (status === 'pending') return 0;
  return Math.max(0, Math.min(100, Math.round(progress * 100)));
});
 const statusBadgeClass = computed(() => {
    switch (jobDetails.value?.status) {
        case 'completed': return 'bg-green-100 text-green-800'; case 'failed': return 'bg-red-100 text-red-800';
        case 'processing': return 'bg-blue-100 text-blue-800 animate-pulse'; default: return 'bg-gray-100 text-gray-800';
    }
});
const progressColorClass = computed(() => {
  const status = jobDetails.value?.status;
  if (status === 'completed') return 'bg-green-500'; if (status === 'failed') return 'bg-red-500';
  return 'bg-primary animate-pulse';
});
const formatDateTime = (isoString: string | null | undefined): string => {
    if (!isoString) return 'N/A'; try { return new Date(isoString).toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true }); } catch { return 'Invalid Date'; }
};
const formattedCreatedAt = computed(() => formatDateTime(jobDetails.value?.created_at));
const formattedUpdatedAt = computed(() => formatDateTime(jobDetails.value?.updated_at));
const formattedEstimatedCompletion = computed(() => {
     const status = jobDetails.value?.status;
    if (status === 'completed' && jobDetails.value?.completed_at) return formatDateTime(jobDetails.value.completed_at);
    if (status === 'processing' && jobDetails.value?.estimated_completion) return `${formatDateTime(jobDetails.value.estimated_completion)} (est.)`;
    if (status === 'processing') return 'Calculating...'; if (status === 'failed') return 'N/A';
    if (status === 'pending') return 'Pending Start'; return 'N/A';
});
const canRequestNotify = computed(() => { const status = jobDetails.value?.status; return status === 'pending' || status === 'processing'; });
const pollJobStatus = async (jobId: string) => {
   if (!jobId || jobStore.currentJobId !== jobId) { stopPolling(); return; } isLoading.value = true;
  try { const data = await apiService.getJobStatus(jobId); jobStore.updateJobDetails(data); errorMessage.value = null; }
  catch (error: any) { errorMessage.value = `Polling Error: ${error.message || 'Failed.'}`; stopPolling(); }
  finally { isLoading.value = false; }
};
const startPolling = (jobId: string) => {
  if (!jobId) return; stopPolling(); pollJobStatus(jobId);
  pollingIntervalId.value = window.setInterval(() => { if (jobStore.currentJobId === jobId) pollJobStatus(jobId); else stopPolling(); }, POLLING_INTERVAL);
};
const stopPolling = () => { if (pollingIntervalId.value !== null) { clearInterval(pollingIntervalId.value); pollingIntervalId.value = null; } };
const requestNotification = async () => {
   if (!jobStore.currentJobId || !notificationEmail.value) return; isNotifyLoading.value = true; notifyMessage.value = null; notifyMessageIsError.value = false;
  try { const response = await apiService.requestNotification(jobStore.currentJobId, notificationEmail.value); notifyMessage.value = response.message || 'Sent!'; notificationEmail.value = ''; }
  catch (error: any) { notifyMessage.value = `Error: ${error.message || 'Failed.'}`; notifyMessageIsError.value = true; }
  finally { isNotifyLoading.value = false; setTimeout(() => { notifyMessage.value = null; }, 5000); }
};
const downloadResults = async () => {
   if (!jobStore.currentJobId) return; isDownloadLoading.value = true; downloadError.value = null;
  try { const { blob, filename } = await apiService.downloadResults(jobStore.currentJobId); const url = window.URL.createObjectURL(blob); const a = document.createElement('a'); a.style.display = 'none'; a.href = url; a.download = filename; document.body.appendChild(a); a.click(); window.URL.revokeObjectURL(url); document.body.removeChild(a); }
  catch (error: any) { downloadError.value = `Download failed: ${error.message || 'Could not download.'}`; }
  finally { isDownloadLoading.value = false; }
};
onMounted(() => { if (jobStore.currentJobId) { errorMessage.value = null; if (jobDetails.value?.status !== 'completed' && jobDetails.value?.status !== 'failed') { startPolling(jobStore.currentJobId); } } });
onUnmounted(() => stopPolling());
watch(() => jobStore.currentJobId, (newJobId) => { if (newJobId) { errorMessage.value = null; downloadError.value = null; notifyMessage.value = null; notificationEmail.value = ''; isDownloadLoading.value = false; isNotifyLoading.value = false; if (jobStore.jobDetails?.status !== 'completed' && jobStore.jobDetails?.status !== 'failed') startPolling(newJobId); else stopPolling(); } else stopPolling(); });
watch(() => jobStore.jobDetails?.status, (newStatus) => { if (newStatus === 'completed' || newStatus === 'failed') stopPolling(); });
</script>

<style scoped>
/* Add subtle animation to progress bar */
.animate-pulse {
   /* Tailwind's pulse animation */
}
</style>