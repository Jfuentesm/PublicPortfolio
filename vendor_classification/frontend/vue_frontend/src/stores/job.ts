// <file path='frontend/vue_frontend/src/stores/job.ts'>
import { defineStore } from 'pinia';
import { ref, reactive, computed } from 'vue';
// Removed JobResultsResponse from here
import apiService, { type JobResponse } from '@/services/api';

// Define the structure of the job details object based on your API response
// Should align with app/schemas/job.py -> JobResponse
export interface JobDetails {
    id: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    current_stage: string;
    created_at: string | null;
    updated_at: string | null;
    completed_at?: string | null;
    estimated_completion?: string | null;
    error_message: string | null;
    target_level: number;
    company_name?: string;
    input_file_name?: string;
    output_file_name?: string | null;
    created_by?: string;
    job_type: 'CLASSIFICATION' | 'REVIEW';
    parent_job_id: string | null;
}

// Interface for a single detailed result item (for CLASSIFICATION jobs)
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

// Interface for a single detailed result item (for REVIEW jobs)
// Should align with app/schemas/review.py -> ReviewResultItem
export interface ReviewResultItem {
    vendor_name: string;
    hint: string;
    original_result: JobResultItem; // Use JobResultItem type for structure
    new_result: JobResultItem; // Use JobResultItem type for structure
}


export const useJobStore = defineStore('job', () => {
    // --- State ---
    const currentJobId = ref<string | null>(null);
    const jobDetails = ref<JobDetails | null>(null);
    const isLoading = ref(false); // For tracking polling/loading state for CURRENT job details
    const error = ref<string | null>(null); // For storing errors related to fetching CURRENT job status

    const jobHistory = ref<JobResponse[]>([]);
    const historyLoading = ref(false);
    const historyError = ref<string | null>(null);

    // --- UPDATED: Results State ---
    // Holds the primary results for the currentJobId (JobResultItem[] or ReviewResultItem[])
    const jobResults = ref<JobResultItem[] | ReviewResultItem[] | null>(null);
    // Holds results from the latest review job *if* currentJobId is a CLASSIFICATION job
    const relatedReviewResults = ref<ReviewResultItem[] | null>(null); // NEW
    const resultsLoading = ref(false);
    const resultsError = ref<string | null>(null);
    // --- END UPDATED ---

    const flaggedForReview = reactive<Map<string, { hint: string | null }>>(new Map());
    const reclassifyLoading = ref(false);
    const reclassifyError = ref<string | null>(null);
    const lastReviewJobId = ref<string | null>(null);

    // --- Computed ---
    const hasFlaggedItems = computed(() => flaggedForReview.size > 0);

    // --- Actions ---
    function setCurrentJobId(jobId: string | null): void {
        console.log(`JobStore: Setting currentJobId from '${currentJobId.value}' to '${jobId}'`);
        if (currentJobId.value !== jobId) {
            currentJobId.value = jobId;
            // Clear details and results when ID changes
            jobDetails.value = null;
            jobResults.value = null;
            relatedReviewResults.value = null; // Clear related results too
            console.log(`JobStore: Cleared jobDetails and results due to ID change.`);
            error.value = null;
            isLoading.value = false;
            resultsLoading.value = false; // Reset results loading
            resultsError.value = null; // Reset results error
            // Clear flagging state
            flaggedForReview.clear();
            reclassifyLoading.value = false;
            reclassifyError.value = null;
            lastReviewJobId.value = null;
            console.log(`JobStore: Cleared flagging state due to ID change.`);

            // Update URL
            try {
                 const url = new URL(window.location.href);
                 if (jobId) {
                     url.searchParams.set('job_id', jobId);
                     console.log(`JobStore: Updated URL searchParam 'job_id' to ${jobId}`);
                 } else {
                     url.searchParams.delete('job_id');
                     console.log(`JobStore: Removed 'job_id' from URL searchParams.`);
                 }
                 window.history.replaceState({}, '', url.toString());
            } catch (e) {
                 console.error("JobStore: Failed to update URL:", e);
            }
        }
         // If the same job ID is set again, force a refresh
         else if (jobId !== null) {
             console.log(`JobStore: Re-setting same job ID ${jobId}, clearing details and results to force refresh.`);
             jobDetails.value = null;
             jobResults.value = null;
             relatedReviewResults.value = null; // Clear related results too
             error.value = null;
             isLoading.value = false;
             resultsLoading.value = false;
             resultsError.value = null;
             // Clear flagging state
             flaggedForReview.clear();
             reclassifyLoading.value = false;
             reclassifyError.value = null;
             lastReviewJobId.value = null;
         }
    }

    function updateJobDetails(details: JobDetails): void {
        if (details && details.id === currentJobId.value) {
            console.log(`JobStore: Updating jobDetails for ${currentJobId.value} with status ${details.status}, progress ${details.progress}, target_level ${details.target_level}, job_type ${details.job_type}`);
            // Check if job type changed (e.g., initial load vs poll update)
            const typeChanged = jobDetails.value?.job_type !== details.job_type;
            jobDetails.value = { ...details };
            error.value = null;
            // If type changed, results might need refetching/reinterpreting
            if (typeChanged) {
                console.log("JobStore: Job type changed, clearing existing results.");
                jobResults.value = null;
                relatedReviewResults.value = null;
                resultsLoading.value = false;
                resultsError.value = null;
                // Trigger results fetch again? Or let the calling component handle it.
                // Let's assume the component watching jobDetails will trigger fetchCurrentJobResults.
            }
        } else if (details) {
            console.warn(`JobStore: Received details for job ${details.id}, but currently tracking ${currentJobId.value}. Ignoring update.`);
        } else {
            console.warn(`JobStore: updateJobDetails called with invalid details object.`);
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
        setCurrentJobId(null);
    }

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
            jobHistory.value = [];
        } finally {
            historyLoading.value = false;
        }
    }

    // --- NEW HELPER: Find latest completed review job for a parent ---
    function findLatestReviewJobFor(parentId: string): JobResponse | null {
        const completedReviewJobs = jobHistory.value
            .filter(job =>
                job.parent_job_id === parentId &&
                job.job_type === 'REVIEW' &&
                job.status === 'completed' &&
                job.completed_at // Ensure completed_at is not null
            )
            .sort((a, b) => {
                // Sort descending by completed_at date
                const dateA = a.completed_at ? new Date(a.completed_at) : new Date(0);
                const dateB = b.completed_at ? new Date(b.completed_at) : new Date(0);
                return dateB.getTime() - dateA.getTime();
            });

        if (completedReviewJobs.length > 0) {
            console.log(`JobStore: Found latest review job ${completedReviewJobs[0].id} for parent ${parentId}`);
            return completedReviewJobs[0];
        }
        return null;
    }
    // --- END NEW HELPER ---

    // --- UPDATED: Action to fetch results based on current job type ---
    async function fetchCurrentJobResults(): Promise<void> {
        if (!currentJobId.value || !jobDetails.value) {
            console.warn("JobStore: fetchCurrentJobResults called without currentJobId or jobDetails.");
            resultsLoading.value = false; // Ensure loading is false if we exit early
            return;
        }
        // Avoid redundant fetches
        if (resultsLoading.value) {
            console.log("JobStore: fetchCurrentJobResults called while already loading. Skipping.");
            return;
        }

        const jobId = currentJobId.value;
        const jobType = jobDetails.value.job_type;

        console.log(`JobStore: Starting fetchCurrentJobResults for ${jobId} (Type: ${jobType})`);

        // Clear previous results
        jobResults.value = null;
        relatedReviewResults.value = null;
        resultsLoading.value = true;
        resultsError.value = null;

        try {
            // Fetch primary results for the current job ID
            console.log(`JobStore: Fetching primary results for ${jobId}...`);
            // The actual response type from apiService.getJobResults is inferred here
            const primaryResponse = await apiService.getJobResults(jobId);

            // Check if job ID changed *during* the API call
            if (jobId !== currentJobId.value) {
                 console.log(`JobStore: Job ID changed while fetching primary results for ${jobId}. Discarding.`);
                 resultsLoading.value = false; // Ensure loading is reset
                 return; // Exit early
            }

            // Store primary results (casting based on expected type)
            if (jobType === 'CLASSIFICATION') {
                jobResults.value = primaryResponse.results as JobResultItem[];
            } else if (jobType === 'REVIEW') {
                jobResults.value = primaryResponse.results as ReviewResultItem[];
            } else {
                console.error(`JobStore: Unknown job type '${jobType}' encountered.`);
                jobResults.value = primaryResponse.results; // Store as is, might cause issues downstream
            }
            console.log(`JobStore: Successfully fetched ${primaryResponse.results.length} primary results for ${jobId}.`);

            // If it's a CLASSIFICATION job, try to find and fetch the latest *completed* review results
            if (jobType === 'CLASSIFICATION') {
                // Ensure job history is available. Fetch if needed?
                // For simplicity, assume history is reasonably up-to-date when this is called.
                // If not, add: if (jobHistory.value.length === 0) await fetchJobHistory();
                const latestReviewJob = findLatestReviewJobFor(jobId);
                if (latestReviewJob) {
                    console.log(`JobStore: Found related completed review job: ${latestReviewJob.id}. Fetching its results...`);
                    try {
                        // The actual response type from apiService.getJobResults is inferred here
                        const reviewResponse = await apiService.getJobResults(latestReviewJob.id);
                         // Check if job ID changed *during* this second API call
                        if (jobId !== currentJobId.value) {
                             console.log(`JobStore: Job ID changed while fetching related review results for ${jobId}. Discarding.`);
                             // Don't reset loading here, let the finally block handle it
                             return; // Exit early
                        }
                        // Ensure the response is ReviewResultItem[]
                        if (latestReviewJob.job_type === 'REVIEW') { // Sanity check
                             relatedReviewResults.value = reviewResponse.results as ReviewResultItem[];
                             console.log(`JobStore: Successfully fetched ${reviewResponse.results.length} related review results for ${jobId} from review job ${latestReviewJob.id}`);
                        } else {
                             console.warn(`JobStore: Found related job ${latestReviewJob.id}, but it's not a REVIEW job type.`);
                        }
                    } catch (reviewErr: any) {
                        console.error(`JobStore: Failed to fetch results for related review job ${latestReviewJob.id}:`, reviewErr);
                        // Don't set the main resultsError, just log it.
                        // Clear related results if fetch failed
                        relatedReviewResults.value = null;
                    }
                } else {
                     console.log(`JobStore: No related completed review job found for classification job ${jobId}.`);
                     relatedReviewResults.value = null; // Ensure it's null if none found
                }
            }
        } catch (err: any) {
            console.error(`JobStore: Failed to fetch primary results for ${jobId}:`, err);
            // Only set error if it's for the currently selected job
            if (jobId === currentJobId.value) {
                resultsError.value = err.message || 'Failed to load results.';
                jobResults.value = null; // Clear results on primary fetch error
                relatedReviewResults.value = null; // Clear related results too
            }
        } finally {
             // Only stop loading if it's for the currently selected job
            if (jobId === currentJobId.value) {
                resultsLoading.value = false;
                console.log(`JobStore: Finished fetchCurrentJobResults for ${jobId}. Loading: ${resultsLoading.value}`);
            } else {
                 console.log(`JobStore: Finished fetchCurrentJobResults for ${jobId}, but current job is now ${currentJobId.value}. Loading state not updated for current job.`);
            }
        }
    }
    // --- END UPDATED ---

    // --- Reclassification Actions (Minor Adjustments) ---
    function isFlagged(vendorName: string): boolean {
        return flaggedForReview.has(vendorName);
    }

    function getHint(vendorName: string): string | null {
        return flaggedForReview.get(vendorName)?.hint ?? null;
    }

    function flagVendor(vendorName: string, initialHint: string | null = null): void { // Added optional initial hint
        if (!flaggedForReview.has(vendorName)) {
            flaggedForReview.set(vendorName, { hint: initialHint }); // Use initial hint if provided
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
        // --- Ensure submission always uses the original classification job ID ---
        let submissionJobId = currentJobId.value;
        // If the current job is a REVIEW job, find its parent (original CLASSIFICATION job)
        if (jobDetails.value?.job_type === 'REVIEW' && jobDetails.value?.parent_job_id) {
            submissionJobId = jobDetails.value.parent_job_id;
            console.log(`JobStore: Current job is REVIEW type, submitting flags against parent job ${submissionJobId}`);
        } else if (jobDetails.value?.job_type === 'CLASSIFICATION') {
             console.log(`JobStore: Current job is CLASSIFICATION type, submitting flags against job ${submissionJobId}`);
        } else {
             console.error("JobStore: Cannot determine original job ID for submitting flags.");
             reclassifyError.value = "Cannot determine the original job to reclassify from.";
             return null;
        }

        if (!submissionJobId || flaggedForReview.size === 0) {
            console.warn("JobStore: submitFlagsForReview called with no submission job ID or no flagged items.");
            reclassifyError.value = "No items flagged for review.";
            return null;
        }
        // --- End Ensure submission job ID ---

        const itemsToReclassify = Array.from(flaggedForReview.entries())
            .filter(([_, data]) => data.hint && data.hint.trim() !== '')
            .map(([vendorName, data]) => ({
                vendor_name: vendorName,
                hint: data.hint!,
            }));

        if (itemsToReclassify.length === 0) {
            console.warn("JobStore: submitFlagsForReview called, but no flagged items have valid hints.");
            reclassifyError.value = "Please provide hints for the flagged items before submitting.";
            return null;
        }

        console.log(`JobStore: Submitting ${itemsToReclassify.length} flags for reclassification against job ${submissionJobId}...`);
        reclassifyLoading.value = true;
        reclassifyError.value = null;
        lastReviewJobId.value = null;

        try {
            // Use the determined submissionJobId
            const response = await apiService.reclassifyJob(submissionJobId, itemsToReclassify);
            console.log(`JobStore: Reclassification job started successfully. Review Job ID: ${response.review_job_id}`);
            lastReviewJobId.value = response.review_job_id;
            flaggedForReview.clear(); // Clear flags after successful submission
            // Optionally: Fetch job history again AFTER a short delay to show the new PENDING review job
            setTimeout(() => fetchJobHistory(), 1000); // Refresh history after 1s
            return response.review_job_id;
        } catch (err: any) {
            console.error('JobStore: Failed to submit flags for reclassification:', err);
            reclassifyError.value = err.message || 'Failed to start reclassification job.';
            return null;
        } finally {
            reclassifyLoading.value = false;
        }
    }
    // --- END Reclassification Actions ---


    return {
        // State
        currentJobId,
        jobDetails,
        isLoading,
        error,
        jobHistory,
        historyLoading,
        historyError,
        jobResults, // Holds JobResultItem[] or ReviewResultItem[]
        relatedReviewResults, // Holds ReviewResultItem[] or null
        resultsLoading,
        resultsError,
        flaggedForReview,
        reclassifyLoading,
        reclassifyError,
        lastReviewJobId,
        hasFlaggedItems,

        // Actions
        setCurrentJobId,
        updateJobDetails,
        setLoading,
        setError,
        clearJob,
        fetchJobHistory,
        fetchCurrentJobResults, // Use this action to fetch results
        // fetchJobResults, // Keep original name if preferred, but fetchCurrentJobResults is clearer
        isFlagged,
        getHint,
        flagVendor,
        unflagVendor,
        setHint,
        submitFlagsForReview,
    };
});