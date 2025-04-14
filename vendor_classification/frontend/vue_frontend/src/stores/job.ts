// <file path='frontend/vue_frontend/src/stores/job.ts'>
import { defineStore } from 'pinia';
import { ref, reactive, computed } from 'vue'; // <<< Added reactive, computed
import apiService, { type JobResponse, type JobResultsResponse } from '@/services/api'; // Import JobResponse type

// Define the structure of the job details object based on your API response
// Should align with app/schemas/job.py -> JobResponse
export interface JobDetails {
    id: string; // Changed from job_id to match JobResponse schema
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    current_stage: string; // Consider using specific stage literals if known
    created_at: string | null; // Use string for ISO date
    updated_at: string | null; // Use string for ISO date
    completed_at?: string | null; // Optional completion time
    estimated_completion?: string | null; // Added optional field (backend doesn't provide this explicitly yet)
    error_message: string | null;
    target_level: number; // ADDED: Ensure target_level is part of the details
    company_name?: string;
    input_file_name?: string;
    output_file_name?: string | null;
    created_by?: string;
    // --- ADDED: Job Type and Parent Link ---
    job_type: 'CLASSIFICATION' | 'REVIEW';
    parent_job_id: string | null;
    // --- END ADDED ---
}

// --- UPDATED: Interface for a single detailed result item (for CLASSIFICATION jobs) ---
// Should align with app/schemas/job.py -> JobResultItem
export interface JobResultItem {
    vendor_name: string;
    level1_id: string | null;
    level1_name: string | null;
    level2_id: string | null;
    level2_name: string | null;
    level3_id: string | null;
    level3_name: string | null;
    level4_id: string | null;
    level4_name: string | null;
    level5_id: string | null;
    level5_name: string | null;
    final_confidence: number | null;
    final_status: string; // 'Classified', 'Not Possible', 'Error'
    classification_source: string | null; // 'Initial', 'Search', 'Review'
    classification_notes_or_reason: string | null;
    achieved_level: number | null; // 0-5
}
// --- END UPDATED ---

// --- ADDED: Interface for a single detailed result item (for REVIEW jobs) ---
// Should align with app/schemas/review.py -> ReviewResultItem
export interface ReviewResultItem {
    vendor_name: string;
    hint: string;
    // Store the original result (as a dict matching JobResultItem)
    original_result: JobResultItem; // Use JobResultItem type for structure
    // Store the new result (as a dict matching JobResultItem)
    new_result: JobResultItem; // Use JobResultItem type for structure
}
// --- END ADDED ---


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

    // --- ADDED: Detailed Job Results State ---
    // Use Union type to hold either result type
    const jobResults = ref<JobResultItem[] | ReviewResultItem[] | null>(null);
    const resultsLoading = ref(false);
    const resultsError = ref<string | null>(null);
    // --- END ADDED ---

    // --- ADDED: Reclassification State ---
    // Map vendor name to its flagged state and hint
    const flaggedForReview = reactive<Map<string, { hint: string | null }>>(new Map());
    const reclassifyLoading = ref(false);
    const reclassifyError = ref<string | null>(null);
    const lastReviewJobId = ref<string | null>(null); // Store ID of the last created review job
    // --- END ADDED ---

    // --- Computed ---
    const hasFlaggedItems = computed(() => flaggedForReview.size > 0);

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
            // --- ADDED: Clear detailed results when job changes ---
            jobResults.value = null;
            resultsLoading.value = false;
            resultsError.value = null;
            console.log(`JobStore: Cleared detailed jobResults due to ID change.`); // LOGGING
            // --- END ADDED ---
            // --- ADDED: Clear flagging state when job changes ---
            flaggedForReview.clear();
            reclassifyLoading.value = false;
            reclassifyError.value = null;
            lastReviewJobId.value = null;
            console.log(`JobStore: Cleared flagging state due to ID change.`); // LOGGING
            // --- END ADDED ---

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
             console.log(`JobStore: Re-setting same job ID ${jobId}, clearing details and results to force refresh.`); // LOGGING
             jobDetails.value = null;
             error.value = null;
             isLoading.value = false;
             // --- ADDED: Clear detailed results on re-select too ---
             jobResults.value = null;
             resultsLoading.value = false;
             resultsError.value = null;
             // --- END ADDED ---
             // --- ADDED: Clear flagging state on re-select too ---
             flaggedForReview.clear();
             reclassifyLoading.value = false;
             reclassifyError.value = null;
             lastReviewJobId.value = null;
             // --- END ADDED ---
         }
    }

    function updateJobDetails(details: JobDetails): void {
        // Only update if the details are for the currently tracked job
        if (details && details.id === currentJobId.value) { // Match 'id' field from JobResponse/JobDetails
            // LOGGING: Include target_level in log
            console.log(`JobStore: Updating jobDetails for ${currentJobId.value} with status ${details.status}, progress ${details.progress}, target_level ${details.target_level}, job_type ${details.job_type}`);
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
        setCurrentJobId(null); // This also clears details, error, loading, results and URL param
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

    // --- ADDED: Detailed Job Results Actions ---
    async function fetchJobResults(jobId: string): Promise<void> {
        // Only fetch if the jobId matches the current job
        if (jobId !== currentJobId.value) {
            console.log(`JobStore: fetchJobResults called for ${jobId}, but current job is ${currentJobId.value}. Skipping.`);
            return;
        }
        // Avoid redundant fetches if already loading
        if (resultsLoading.value) {
             console.log(`JobStore: fetchJobResults called for ${jobId}, but already loading. Skipping.`);
             return;
        }

        console.log(`JobStore: Fetching detailed results for job ${jobId}...`);
        resultsLoading.value = true;
        resultsError.value = null;
        jobResults.value = null; // Clear previous results before fetching
        try {
            // API now returns { job_id, job_type, results: [...] }
            const response: JobResultsResponse = await apiService.getJobResults(jobId);
            // Double-check the job ID hasn't changed *during* the API call
            if (jobId === currentJobId.value) {
                // Store the results array. The type (JobResultItem[] or ReviewResultItem[])
                // is implicitly handled by the Union type and determined by job_type.
                jobResults.value = response.results;
                // Update jobDetails with the job_type from the response if needed
                if (jobDetails.value && jobDetails.value.job_type !== response.job_type) {
                    console.log(`JobStore: Updating job_type in details from results response for ${jobId}`);
                    jobDetails.value.job_type = response.job_type;
                }
                console.log(`JobStore: Successfully fetched ${response.results.length} detailed results for ${jobId} (Type: ${response.job_type}).`);
            } else {
                 console.log(`JobStore: Job ID changed while fetching results for ${jobId}. Discarding fetched results.`);
            }
        } catch (err: any) {
            console.error(`JobStore: Failed to fetch detailed results for ${jobId}:`, err);
            // Only set error if it's for the currently selected job
            if (jobId === currentJobId.value) {
                resultsError.value = err.message || 'Failed to load detailed results.';
                jobResults.value = null; // Clear results on error
            }
        } finally {
             // Only stop loading if it's for the currently selected job
            if (jobId === currentJobId.value) {
                resultsLoading.value = false;
            }
        }
    }
    // --- END ADDED ---

    // --- ADDED: Reclassification Actions ---
    function isFlagged(vendorName: string): boolean {
        return flaggedForReview.has(vendorName);
    }

    function getHint(vendorName: string): string | null {
        return flaggedForReview.get(vendorName)?.hint ?? null;
    }

    function flagVendor(vendorName: string): void {
        if (!flaggedForReview.has(vendorName)) {
            flaggedForReview.set(vendorName, { hint: null });
            console.log(`JobStore: Flagged vendor '${vendorName}' for review.`);
        }
    }

    function unflagVendor(vendorName: string): void {
        if (flaggedForReview.has(vendorName)) {
            flaggedForReview.delete(vendorName);
            console.log(`JobStore: Unflagged vendor '${vendorName}'.`);
        }
    }

    function setHint(vendorName: string, hint: string | null): void {
        if (flaggedForReview.has(vendorName)) {
            flaggedForReview.set(vendorName, { hint });
            console.log(`JobStore: Set hint for '${vendorName}': ${hint ? `'${hint}'` : 'cleared'}`);
        } else {
            console.warn(`JobStore: Tried to set hint for unflagged vendor '${vendorName}'.`);
        }
    }

    async function submitFlagsForReview(): Promise<string | null> {
        const originalJobId = currentJobId.value;
        if (!originalJobId || flaggedForReview.size === 0) {
            console.warn("JobStore: submitFlagsForReview called with no job ID or no flagged items.");
            reclassifyError.value = "No items flagged for review.";
            return null;
        }

        const itemsToReclassify = Array.from(flaggedForReview.entries())
            .filter(([_, data]) => data.hint && data.hint.trim() !== '') // Only submit items with a non-empty hint
            .map(([vendorName, data]) => ({
                vendor_name: vendorName,
                hint: data.hint!, // Assert non-null because we filtered
            }));

        if (itemsToReclassify.length === 0) {
            console.warn("JobStore: submitFlagsForReview called, but no flagged items have valid hints.");
            reclassifyError.value = "Please provide hints for the flagged items before submitting.";
            // Clear flags that have no hint? Maybe not, let user clear them.
            return null;
        }


        console.log(`JobStore: Submitting ${itemsToReclassify.length} flags for reclassification for job ${originalJobId}...`);
        reclassifyLoading.value = true;
        reclassifyError.value = null;
        lastReviewJobId.value = null;

        try {
            const response = await apiService.reclassifyJob(originalJobId, itemsToReclassify);
            console.log(`JobStore: Reclassification job started successfully. Review Job ID: ${response.review_job_id}`);
            lastReviewJobId.value = response.review_job_id;
            // Clear the flags after successful submission
            flaggedForReview.clear();
            // Optionally: Fetch job history again to show the new PENDING review job
            // await fetchJobHistory();
            // Optionally: Navigate to the new review job? Or just show a success message.
            // setCurrentJobId(response.review_job_id); // This would switch view immediately
            return response.review_job_id; // Return the new job ID for potential navigation
        } catch (err: any) {
            console.error('JobStore: Failed to submit flags for reclassification:', err);
            reclassifyError.value = err.message || 'Failed to start reclassification job.';
            return null;
        } finally {
            reclassifyLoading.value = false;
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
        // Detailed Results state & actions
        jobResults, // Can be JobResultItem[] or ReviewResultItem[]
        resultsLoading,
        resultsError,
        fetchJobResults,
        // Reclassification state & actions
        flaggedForReview,
        reclassifyLoading,
        reclassifyError,
        lastReviewJobId,
        hasFlaggedItems,
        isFlagged,
        getHint,
        flagVendor,
        unflagVendor,
        setHint,
        submitFlagsForReview,
        // Existing actions
        setCurrentJobId,
        updateJobDetails,
        setLoading,
        setError,
        clearJob,
    };
});