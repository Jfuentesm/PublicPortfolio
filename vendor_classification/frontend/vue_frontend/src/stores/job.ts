// frontend/vue_frontend/src/stores/job.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import apiService, { type JobResponse } from '@/services/api'; // Import JobResponse type

// Define the structure of the job details object based on your API response
export interface JobDetails {
    id: string; // Changed from job_id to match JobResponse schema
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    current_stage: string; // Consider using specific stage literals if known
    created_at: string | null;
    updated_at: string | null;
    completed_at?: string | null; // Optional completion time
    estimated_completion?: string | null; // Added optional field (backend doesn't provide this explicitly yet)
    error_message: string | null;
    // Add other fields returned by /api/v1/jobs/{job_id} if needed
    // Match JobResponse fields where applicable
    company_name?: string;
    input_file_name?: string;
    output_file_name?: string | null;
    created_by?: string;
}

export const useJobStore = defineStore('job', () => {
    // --- State ---
    const currentJobId = ref<string | null>(null);
    const jobDetails = ref<JobDetails | null>(null);
    const isLoading = ref(false); // For tracking polling/loading state for CURRENT job
    const error = ref<string | null>(null); // For storing errors related to fetching CURRENT job status

    // --- ADDED: Job History State ---
    const jobHistory = ref<JobResponse[]>([]);
    const historyLoading = ref(false);
    const historyError = ref<string | null>(null);
    // --- END ADDED ---

    // --- Actions ---
    function setCurrentJobId(jobId: string | null): void {
        console.log(`JobStore: Setting currentJobId from '${currentJobId.value}' to '${jobId}'`); // LOGGING
        if (currentJobId.value !== jobId) {
            currentJobId.value = jobId;
            // Clear details when ID changes (to null or a new ID) to force refresh
            jobDetails.value = null;
            console.log(`JobStore: Cleared jobDetails due to ID change.`); // LOGGING
            error.value = null; // Clear errors
            isLoading.value = false; // Reset loading state

            // Update URL to reflect the current job ID or clear it
            try {
                 const url = new URL(window.location.href);
                 if (jobId) {
                     url.searchParams.set('job_id', jobId);
                     console.log(`JobStore: Updated URL searchParam 'job_id' to ${jobId}`); // LOGGING
                 } else {
                     url.searchParams.delete('job_id');
                     console.log(`JobStore: Removed 'job_id' from URL searchParams.`); // LOGGING
                 }
                 // Use replaceState to avoid polluting history
                 window.history.replaceState({}, '', url.toString());
            } catch (e) {
                 console.error("JobStore: Failed to update URL:", e);
            }
        }
         // If the same job ID is set again, force a refresh of details
         else if (jobId !== null) {
             console.log(`JobStore: Re-setting same job ID ${jobId}, clearing details to force refresh.`); // LOGGING
             jobDetails.value = null;
             error.value = null;
             isLoading.value = false;
         }
    }

    function updateJobDetails(details: JobDetails): void {
        // Only update if the details are for the currently tracked job
        if (details && details.id === currentJobId.value) { // Match 'id' field from JobResponse/JobDetails
            console.log(`JobStore: Updating jobDetails for ${currentJobId.value} with status ${details.status}, progress ${details.progress}`); // LOGGING
            jobDetails.value = { ...details }; // Create new object for reactivity
            error.value = null; // Clear error on successful update
        } else if (details) {
            console.warn(`JobStore: Received details for job ${details.id}, but currently tracking ${currentJobId.value}. Ignoring update.`); // LOGGING
        } else {
            console.warn(`JobStore: updateJobDetails called with invalid details object.`); // LOGGING
        }
    }

    function setLoading(loading: boolean): void {
        isLoading.value = loading;
    }

    function setError(errorMessage: string | null): void {
        error.value = errorMessage;
    }

    function clearJob(): void {
        console.log('JobStore: Clearing job state.'); // LOGGING
        setCurrentJobId(null); // This also clears details, error, loading and URL param
        // --- ADDED: Clear history too on full clear? Optional. ---
        // jobHistory.value = [];
        // historyLoading.value = false;
        // historyError.value = null;
        // --- END ADDED ---
    }

    // --- ADDED: Job History Actions ---
    async function fetchJobHistory(params = {}): Promise<void> {
        console.log('JobStore: Fetching job history with params:', params); // LOGGING
        historyLoading.value = true;
        historyError.value = null;
        try {
            const jobs = await apiService.getJobs(params);
            jobHistory.value = jobs;
            console.log(`JobStore: Fetched ${jobs.length} jobs.`); // LOGGING
        } catch (err: any) {
            console.error('JobStore: Failed to fetch job history:', err); // LOGGING
            historyError.value = err.message || 'Failed to load job history.';
            jobHistory.value = []; // Clear history on error
        } finally {
            historyLoading.value = false;
        }
    }
    // --- END ADDED ---


    return {
        currentJobId,
        jobDetails,
        isLoading,
        error,
        // History state & actions
        jobHistory,
        historyLoading,
        historyError,
        fetchJobHistory,
        // Existing actions
        setCurrentJobId,
        updateJobDetails,
        setLoading,
        setError,
        clearJob,
    };
});
