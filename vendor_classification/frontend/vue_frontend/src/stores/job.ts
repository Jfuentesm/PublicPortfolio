import { defineStore } from 'pinia';
import { ref } from 'vue';
import apiService, { type JobResponse } from '@/services/api'; // Import JobResponse type

// Define the structure of the job details object based on your API response
export interface JobDetails {
    job_id: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    current_stage: string; // Consider using specific stage literals if known
    created_at: string | null;
    updated_at: string | null;
    completed_at?: string | null; // Optional completion time
    estimated_completion: string | null;
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
        console.log(`JobStore: Setting currentJobId to ${jobId}`);
        if (currentJobId.value !== jobId) {
            currentJobId.value = jobId;
            // Only clear details if the ID actually changes to a non-null value
            // If setting to null, keep details until explicitly cleared
            if (jobId !== null) {
                jobDetails.value = null;
            }
            error.value = null; // Clear errors
            isLoading.value = false; // Reset loading state

            // Update URL to reflect the current job ID or clear it
            try {
                 const url = new URL(window.location.href);
                 if (jobId) {
                     url.searchParams.set('job_id', jobId);
                 } else {
                     url.searchParams.delete('job_id');
                 }
                 // Use replaceState to avoid polluting history
                 window.history.replaceState({}, '', url.toString());
            } catch (e) {
                 console.error("Failed to update URL:", e);
            }
        }
         // If the same job ID is set again, force a refresh of details
         else if (jobId !== null) {
             console.log(`JobStore: Re-setting same job ID ${jobId}, clearing details to force refresh.`);
             jobDetails.value = null;
             error.value = null;
             isLoading.value = false;
         }
    }

    function updateJobDetails(details: JobDetails): void {
        // Only update if the details are for the currently tracked job
        if (details && details.job_id === currentJobId.value) {
            // console.log(`JobStore: Updating jobDetails for ${currentJobId.value}`);
            jobDetails.value = { ...details }; // Create new object for reactivity
            error.value = null; // Clear error on successful update
        } else if (details) {
            // console.warn(`JobStore: Received details for job ${details.job_id}, but currently tracking ${currentJobId.value}. Ignoring update.`);
        }
    }

    function setLoading(loading: boolean): void {
        isLoading.value = loading;
    }

    function setError(errorMessage: string | null): void {
        error.value = errorMessage;
    }

    function clearJob(): void {
        console.log('JobStore: Clearing job state.');
        setCurrentJobId(null); // This also clears details, error, loading and URL param
        // --- ADDED: Clear history too on full clear? Optional. ---
        // jobHistory.value = [];
        // historyLoading.value = false;
        // historyError.value = null;
        // --- END ADDED ---
    }

    // --- ADDED: Job History Actions ---
    async function fetchJobHistory(params = {}): Promise<void> {
        console.log('JobStore: Fetching job history with params:', params);
        historyLoading.value = true;
        historyError.value = null;
        try {
            const jobs = await apiService.getJobs(params);
            jobHistory.value = jobs;
            console.log(`JobStore: Fetched ${jobs.length} jobs.`);
        } catch (err: any) {
            console.error('JobStore: Failed to fetch job history:', err);
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