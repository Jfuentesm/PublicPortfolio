<template>
  <div class="mt-10 bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
    <div class="bg-gray-100 text-gray-800 p-4 sm:p-5 border-b border-gray-200 flex justify-between items-center">
      <h4 class="text-xl font-semibold mb-0">Job History</h4>
      <!-- Add a refresh button maybe? -->
    </div>
    <div class="p-6 sm:p-8">
      <!-- Loading State -->
      <div v-if="historyLoading" class="text-center text-gray-500 py-8">
        <svg class="animate-spin inline-block h-6 w-6 text-primary mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>Loading job history...</span>
      </div>

      <!-- Error State -->
      <div v-else-if="historyError" class="p-4 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm flex items-center">
        <ExclamationTriangleIcon class="h-5 w-5 mr-2 text-red-600 flex-shrink-0"/>
        <span>Error loading history: {{ historyError }}</span>
      </div>

      <!-- Empty State -->
      <div v-else-if="!jobHistory || jobHistory.length === 0" class="text-center text-gray-500 py-8">
        <p>No job history found.</p>
        <p class="text-sm">Upload a file to start your first job.</p>
      </div>

      <!-- History Table -->
      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Job ID
              </th>
              <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Company
              </th>
              <!-- ADDED: User Column (Admin Only) -->
              <th v-if="isSuperuser" scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                User
              </th>
              <!-- END ADDED -->
              <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th scope="col" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="job in jobHistory" :key="job.id" class="hover:bg-gray-50 cursor-pointer" @click="selectJob(job.id)">
              <td class="px-4 py-3 whitespace-nowrap text-xs font-mono text-gray-700" :title="job.id">
                {{ job.id.substring(0, 8) }}...
              </td>
              <td class="px-4 py-3 whitespace-nowrap">
                   <span v-if="job.job_type === 'REVIEW'" class="inline-block px-1.5 py-0.5 rounded text-xs font-semibold bg-purple-100 text-purple-800 align-middle">REVIEW</span>
                   <span v-else-if="job.job_type === 'CLASSIFICATION'" class="inline-block px-1.5 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800 align-middle">CLASSIFICATION</span>
                   <span v-else class="text-xs text-gray-500">{{ job.job_type }}</span>
               </td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-800 font-medium">
                {{ job.company_name }}
              </td>
              <!-- ADDED: User Column Data (Admin Only) -->
              <td v-if="isSuperuser" class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                {{ job.created_by }}
              </td>
              <!-- END ADDED -->
              <td class="px-4 py-3 whitespace-nowrap">
                <span class="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide" :class="getStatusBadgeClass(job.status)" :title="job.error_message || ''">
                  {{ job.status }}
                </span>
                <!-- Optionally show error icon -->
                <ExclamationCircleIcon v-if="job.status === 'failed' && job.error_message" class="h-4 w-4 inline-block ml-1 text-red-500" :title="job.error_message"/>
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                {{ formatDateTime(job.created_at) }}
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-sm font-medium space-x-2">
                <!-- Download only for completed CLASSIFICATION jobs -->
                <button
                  v-if="job.status === 'completed' && job.job_type === 'CLASSIFICATION'"
                  @click.stop="downloadResults(job.id, $event)"
                  :disabled="isDownloadLoading(job.id)"
                  class="text-primary hover:text-primary-hover disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center p-1 rounded hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-primary"
                  title="Download Results"
                >
                   <svg v-if="isDownloadLoading(job.id)" class="animate-spin h-4 w-4 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                   </svg>
                   <ArrowDownTrayIcon v-else class="h-4 w-4" />
                </button>

                <!-- ADDED: Cancel Button (Admin Only for Pending/Processing) -->
                 <button
                   v-if="isSuperuser && (job.status === 'pending' || job.status === 'processing')"
                   @click.stop="cancelJob(job.id, $event)"
                   :disabled="isCancelLoading(job.id)"
                   class="text-red-600 hover:text-red-800 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center p-1 rounded hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-red-500"
                   title="Cancel Job"
                 >
                   <svg v-if="isCancelLoading(job.id)" class="animate-spin h-4 w-4 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                   </svg>
                   <XCircleIcon v-else class="h-4 w-4" />
                 </button>
                <!-- END ADDED -->

                 <!-- Placeholder for other actions or status indicators -->
                 <span v-else-if="job.status === 'failed'" class="text-red-500 text-xs italic" title="Job Failed"></span>
                 <span v-else-if="job.job_type === 'REVIEW' && job.status === 'completed'" class="text-gray-400 text-xs italic" title="Review Job Completed (No Download)"></span>
                 <span v-else-if="job.status !== 'completed' && job.status !== 'pending' && job.status !== 'processing'" class="text-gray-400 text-xs italic" title="Processing or Pending"></span>

                 <!-- Error messages for actions -->
                  <span v-if="downloadErrors[job.id]" class="text-red-600 text-xs italic ml-2">{{ downloadErrors[job.id] }}</span>
                  <span v-if="cancelErrors[job.id]" class="text-red-600 text-xs italic ml-2">{{ cancelErrors[job.id] }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- TODO: Add Pagination Controls if needed -->

    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useJobStore } from '@/stores/job';
import { useAuthStore } from '@/stores/auth'; // <<< ADDED Auth Store import
import { ExclamationTriangleIcon, ArrowDownTrayIcon, XCircleIcon, ExclamationCircleIcon } from '@heroicons/vue/20/solid'; // <<< ADDED Icons
import apiService from '@/services/api';
import { useToast } from 'vue-toastification'; // Import toast

const jobStore = useJobStore();
const authStore = useAuthStore(); // <<< ADDED Auth Store instance
const toast = useToast(); // <<< Initialize toast

const jobHistory = computed(() => jobStore.jobHistory);
const historyLoading = computed(() => jobStore.historyLoading);
const historyError = computed(() => jobStore.historyError);
const isSuperuser = computed(() => authStore.isSuperuser); // <<< ADDED Superuser getter

// State for managing individual button loading and errors
const downloadingJobs = ref<Set<string>>(new Set());
const downloadErrors = ref<Record<string, string | null>>({});
const cancellingJobs = ref<Set<string>>(new Set()); // <<< ADDED Cancel loading state
const cancelErrors = ref<Record<string, string | null>>({}); // <<< ADDED Cancel error state

const isDownloadLoading = (jobId: string) => downloadingJobs.value.has(jobId);
const isCancelLoading = (jobId: string) => cancellingJobs.value.has(jobId); // <<< ADDED Cancel loading check

const fetchHistory = async () => {
  // Reset errors on fetch
  downloadErrors.value = {};
  cancelErrors.value = {};
  await jobStore.fetchJobHistory({ limit: 100 }); // Fetch latest 100 jobs on mount
};

const selectJob = (jobId: string) => {
  console.log(`JobHistory: Selecting job ${jobId}`);
  jobStore.setCurrentJobId(jobId);
  // Optional: Scroll to the top or to the JobStatus component
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

const formatDateTime = (isoString: string | null | undefined): string => {
  if (!isoString) return 'N/A';
  try {
    return new Date(isoString).toLocaleString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: 'numeric', minute: '2-digit', hour12: true
    });
  } catch {
    return 'Invalid Date';
  }
};

const getStatusBadgeClass = (status: string | undefined) => {
  switch (status) {
    case 'completed': return 'bg-green-100 text-green-800';
    case 'failed': return 'bg-red-100 text-red-800';
    case 'processing': return 'bg-blue-100 text-blue-800';
    case 'pending': return 'bg-yellow-100 text-yellow-800'; // Added pending style
    default: return 'bg-gray-100 text-gray-800';
  }
};

const downloadResults = async (jobId: string, event: Event) => {
   event.stopPropagation(); // Prevent row click when clicking button
   if (!jobId || downloadingJobs.value.has(jobId)) return;

   downloadingJobs.value.add(jobId);
   downloadErrors.value[jobId] = null;

  try {
    const { blob, filename } = await apiService.downloadResults(jobId);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    toast.success(`Results downloaded for job ${jobId.substring(0, 8)}...`);
  } catch (error: any) {
    console.error(`Download failed for job ${jobId}:`, error);
    const errorMsg = `Download failed: ${error.message || 'Unknown error'}`;
    downloadErrors.value[jobId] = errorMsg;
    toast.error(errorMsg);
    // Optionally clear the error message after a delay
    setTimeout(() => { downloadErrors.value[jobId] = null; }, 7000);
  } finally {
    downloadingJobs.value.delete(jobId);
  }
};

// --- ADDED: Cancel Job Method ---
const cancelJob = async (jobId: string, event: Event) => {
  event.stopPropagation(); // Prevent row click
  if (!jobId || cancellingJobs.value.has(jobId)) return;

  // Confirmation dialog
  if (!confirm(`Are you sure you want to cancel job ${jobId.substring(0, 8)}...? This cannot be undone.`)) {
      return;
  }

  cancellingJobs.value.add(jobId);
  cancelErrors.value[jobId] = null;

  try {
      const response = await apiService.cancelJob(jobId);
      toast.success(response.message || `Job ${jobId.substring(0, 8)}... cancelled.`);
      // Refresh the job list to show the updated status
      await fetchHistory();
      // --- REMOVED Problematic Line ---
      // If the cancelled job was the currently selected one, the JobStatus component
      // should reactively update when the history refreshes or when the ID is re-selected.
      // jobStore.fetchCurrentJobDetails(); // This method doesn't exist
      // --- END REMOVED ---
  } catch (error: any) {
      console.error(`Cancel failed for job ${jobId}:`, error);
      const errorMsg = `Cancel failed: ${error.message || 'Unknown error'}`;
      cancelErrors.value[jobId] = errorMsg;
      toast.error(errorMsg);
      // Optionally clear the error message after a delay
      setTimeout(() => { cancelErrors.value[jobId] = null; }, 7000);
  } finally {
      cancellingJobs.value.delete(jobId);
  }
};
// --- END ADDED ---

onMounted(() => {
  // Ensure user info is loaded before fetching history if needed for superuser check
  // (though the backend handles the logic, the UI elements depend on isSuperuser)
  if (!authStore.user) {
      authStore.checkAuthStatus(); // Make sure user state is potentially loaded from localStorage
  }
  fetchHistory();
});
</script>

<style scoped>
/* Add specific styles if needed */
tbody tr:hover {
  background-color: #f9fafb; /* Tailwind gray-50 */
}
/* Add spacing for action buttons if needed */
 td:last-child {
      text-align: right; /* Align actions to the right */
 }
</style>