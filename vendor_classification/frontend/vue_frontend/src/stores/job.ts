import { defineStore } from 'pinia';
import { ref } from 'vue';

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
}

export const useJobStore = defineStore('job', () => {
    // --- State ---
    const currentJobId = ref<string | null>(null);
    const jobDetails = ref<JobDetails | null>(null);
    const isLoading = ref(false); // For tracking polling/loading state
    const error = ref<string | null>(null); // For storing errors related to fetching job status

    // --- Actions ---
    function setCurrentJobId(jobId: string | null): void {
        console.log(`JobStore: Setting currentJobId to ${jobId}`);
        if (currentJobId.value !== jobId) {
            currentJobId.value = jobId;
            jobDetails.value = null; // Clear details when job ID changes
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
    }

    return {
        currentJobId,
        jobDetails,
        isLoading,
        error,
        setCurrentJobId,
        updateJobDetails,
        setLoading,
        setError,
        clearJob,
    };
});