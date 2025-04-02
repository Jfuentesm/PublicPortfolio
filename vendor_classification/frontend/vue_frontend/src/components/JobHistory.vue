<template>
    <div class="mt-10 bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
      <div class="bg-gray-100 text-gray-800 p-4 sm:p-5 border-b border-gray-200">
        <h4 class="text-xl font-semibold mb-0">Job History</h4>
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
                  Company
                </th>
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
                <td class="px-4 py-3 whitespace-nowrap text-xs font-mono text-gray-700">
                  {{ job.id.substring(0, 8) }}...
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-800 font-medium">
                  {{ job.company_name }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap">
                  <span class="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide" :class="getStatusBadgeClass(job.status)">
                    {{ job.status }}
                  </span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDateTime(job.created_at) }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    v-if="job.status === 'completed'"
                    @click.stop="downloadResults(job.id, $event)"
                    :disabled="isDownloadLoading(job.id)"
                    class="text-primary hover:text-primary-hover disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center"
                    title="Download Results"
                  >
                     <svg v-if="isDownloadLoading(job.id)" class="animate-spin h-4 w-4 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                     </svg>
                     <ArrowDownTrayIcon v-else class="h-4 w-4" />
                    <!-- <span class="ml-1">Download</span> -->
                  </button>
                  <span v-else-if="job.status === 'failed'" class="text-red-500 text-xs italic" title="Job Failed">Failed</span>
                  <span v-else class="text-gray-400 text-xs italic" title="Processing or Pending">In Progress</span>
                  <!-- Add View Details button if needed -->
                  <!-- <button @click.stop="selectJob(job.id)" class="text-indigo-600 hover:text-indigo-900 ml-3">View</button> -->
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
  import { ExclamationTriangleIcon, ArrowDownTrayIcon } from '@heroicons/vue/20/solid';
  import apiService from '@/services/api';
  
  const jobStore = useJobStore();
  
  const jobHistory = computed(() => jobStore.jobHistory);
  const historyLoading = computed(() => jobStore.historyLoading);
  const historyError = computed(() => jobStore.historyError);
  
  // State for managing individual download button loading
  const downloadingJobs = ref<Set<string>>(new Set());
  const downloadErrors = ref<Record<string, string | null>>({});
  
  const isDownloadLoading = (jobId: string) => downloadingJobs.value.has(jobId);
  
  const fetchHistory = async () => {
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
    } catch (error: any) {
      console.error(`Download failed for job ${jobId}:`, error);
      downloadErrors.value[jobId] = `Download failed: ${error.message || 'Error'}`;
      // Optionally clear the error message after a delay
      setTimeout(() => { downloadErrors.value[jobId] = null; }, 5000);
    } finally {
      downloadingJobs.value.delete(jobId);
    }
  };
  
  
  onMounted(() => {
    fetchHistory();
  });
  </script>
  
  <style scoped>
  /* Add specific styles if needed */
  tbody tr:hover {
    background-color: #f9fafb; /* Tailwind gray-50 */
  }
  </style>