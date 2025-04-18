import axios, {
    type AxiosInstance,
    type InternalAxiosRequestConfig,
    type AxiosError // Import AxiosError type
} from 'axios';
import { useAuthStore } from '@/stores/auth'; // Adjust path as needed
// --- UPDATED: Import JobResultItem and ReviewResultItem ---
// --- REMOVED JobStatsData from this import ---
import type { JobDetails, JobResultItem, ReviewResultItem } from '@/stores/job'; // Adjust path as needed
// --- END REMOVED ---
// --- END UPDATED ---

// --- Define API Response Interfaces ---

// Matches backend schemas/user.py -> UserResponse
export interface UserResponse {
    email: string;
    full_name: string | null;
    is_active: boolean | null;
    is_superuser: boolean | null;
    username: string;
    id: string; // UUID as string
    created_at: string; // ISO Date string
    updated_at: string; // ISO Date string
}

// Matches backend schemas/user.py -> UserCreate (for request body)
export interface UserCreateData {
    email: string;
    full_name?: string | null;
    is_active?: boolean | null;
    is_superuser?: boolean | null;
    username: string;
    password?: string; // Password required on create
}

// Matches backend schemas/user.py -> UserUpdate (for request body)
export interface UserUpdateData {
    email?: string | null;
    full_name?: string | null;
    password?: string | null; // Optional password update
    is_active?: boolean | null;
    is_superuser?: boolean | null;
}


// Matches backend response for /token (modified to include user object)
interface AuthResponse {
    access_token: string;
    token_type: string;
    user: UserResponse; // Include the user details
}

// --- ADDED: File Validation Response Interface ---
// Matches backend api/main.py -> FileValidationResponse
export interface FileValidationResponse {
    is_valid: boolean;
    message: string;
    detected_columns: string[];
    missing_mandatory_columns: string[];
}
// --- END ADDED ---

// Matches backend response for /api/v1/jobs/{job_id}/notify
interface NotifyResponse {
    success: boolean;
    message: string;
}

// Matches backend response for /api/v1/jobs/ (list endpoint)
// Should align with app/schemas/job.py -> JobResponse
export interface JobResponse {
    id: string;
    company_name: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    current_stage: string;
    created_at: string; // ISO Date string
    updated_at?: string | null;
    completed_at?: string | null;
    output_file_name?: string | null;
    input_file_name: string;
    created_by: string;
    error_message?: string | null;
    target_level: number; // Ensure target_level is included here
    // --- ADDED: Job Type and Parent Link ---
    job_type: 'CLASSIFICATION' | 'REVIEW';
    parent_job_id: string | null;
    // --- END ADDED ---
    stats?: Record<string, any>; // Include stats field optionally
}

// --- ADDED: Job Results Response Interface ---
// Matches backend schemas/job.py -> JobResultsResponse
export interface JobResultsResponse {
    job_id: string;
    job_type: 'CLASSIFICATION' | 'REVIEW';
    results: JobResultItem[] | ReviewResultItem[]; // Union type
}
// --- END ADDED ---

// --- ADDED: Job Stats Data Interface ---
// Matches backend models/classification.py -> ProcessingStats and console log
// --- UPDATED: Export the interface ---
export interface JobStatsData {
// --- END UPDATED ---
    job_id: string;
    company_name: string;
    start_time: string | null; // Assuming ISO string
    end_time: string | null; // Assuming ISO string
    processing_duration_seconds: number | null; // Renamed from processing_time
    total_vendors: number | null; // Added
    unique_vendors: number | null; // Added (was present in console)
    target_level: number | null; // Added target level to stats
    successfully_classified_l4?: number | null; // Keep for reference (optional)
    successfully_classified_l5?: number | null; // Keep L5 count (optional)
    classification_not_possible_initial?: number | null; // Added (optional)
    invalid_category_errors?: number | null; // Added (was present in console) (optional)
    search_attempts?: number | null; // Added (optional)
    search_successful_classifications_l1?: number | null; // Added (optional)
    search_successful_classifications_l5?: number | null; // Renamed from search_assisted_l5 (optional)
    api_usage?: { // Nested structure (optional)
        openrouter_calls: number | null;
        openrouter_prompt_tokens: number | null;
        openrouter_completion_tokens: number | null;
        openrouter_total_tokens: number | null;
        tavily_search_calls?: number | null; // Optional if not always present
        cost_estimate_usd: number | null;
    } | null; // Allow api_usage itself to be null if not populated
    // --- ADDED: Stats specific to REVIEW jobs ---
    reclassify_input?: Array<{ vendor_name: string; hint: string }>; // Input hints (optional)
    total_items_processed?: number; // Optional
    successful_reclassifications?: number; // Optional
    failed_reclassifications?: number; // Optional
    parent_job_id?: string; // Include parent ID in stats for review jobs (optional)
    merged_at?: string | null; // Added merge timestamp (optional)
    // --- END ADDED ---
}
// --- END ADDED ---


// Structure for download result helper
interface DownloadResult {
    blob: Blob;
    filename: string;
}

// Parameters for the job history list endpoint
interface GetJobsParams {
    status?: string;
    start_date?: string; // ISO string format
    end_date?: string; // ISO string format
    job_type?: 'CLASSIFICATION' | 'REVIEW'; // Filter by type
    skip?: number;
    limit?: number;
}

// --- ADDED: Password Reset Interfaces ---
// Matches backend schemas/password_reset.py -> MessageResponse
interface MessageResponse {
    message: string;
}
// --- END ADDED ---

// --- ADDED: Reclassification Interfaces ---
// Matches backend schemas/review.py -> ReclassifyRequestItem
interface ReclassifyRequestItemData {
    vendor_name: string;
    hint: string;
}
// Matches backend schemas/review.py -> ReclassifyResponse
interface ReclassifyResponseData {
    review_job_id: string;
    message: string;
}
// --- END ADDED ---

// --- ADDED: Merge Response Interface ---
// Matches backend api/jobs.py -> merge_review_results response
interface MergeResponseData {
    message: string;
    updated_parent_job_id: string;
}
// --- END ADDED ---


// --- Axios Instance Setup ---

const axiosInstance: AxiosInstance = axios.create({
    baseURL: '/api/v1', // Assumes Vite dev server proxies /api/v1 to your backend
    timeout: 60000, // 60 seconds timeout
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
});

// --- Request Interceptor (Add Auth Token) ---
axiosInstance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const authStore = useAuthStore();
        const token = authStore.getToken();
        // Define URLs that should NOT receive the auth token
        // --- UPDATED: Added /users/register ---
        const noAuthUrls = ['/auth/password-recovery', '/auth/reset-password', '/users/register'];
        // --- END UPDATED ---

        // Check if the request URL matches any of the no-auth URLs
        const requiresAuth = token && config.url && !noAuthUrls.some(url => config.url?.startsWith(url));

        if (requiresAuth) {
            // LOGGING: Log token presence and target URL
            // console.log(`[api.ts Request Interceptor] Adding token for URL: ${config.url}`);
            config.headers.Authorization = `Bearer ${token}`;
        } else {
            // console.log(`[api.ts Request Interceptor] No token added for URL: ${config.url} (Token: ${token ? 'present' : 'missing'}, No-Auth Match: ${!requiresAuth && !!token})`);
        }
        return config;
    },
    (error: AxiosError) => {
        console.error('[api.ts Request Interceptor] Error:', error);
        return Promise.reject(error);
    }
);

// --- Response Interceptor (Handle Errors) ---
axiosInstance.interceptors.response.use(
    (response) => {
        // LOGGING: Log successful response status and URL
        // console.log(`[api.ts Response Interceptor] Success for URL: ${response.config.url} | Status: ${response.status}`);
        return response;
    },
    (error: AxiosError) => {
        console.error('[api.ts Response Interceptor] Error:', error.config?.url, error.response?.status, error.message);
        const authStore = useAuthStore();

        if (error.response) {
            const { status, data } = error.response;

            // Handle 401 Unauthorized (except for login attempts and password reset)
            const isLoginAttempt = error.config?.url === '/token'; // Base URL for login
            // --- UPDATED: Check register url ---
            const isPublicAuthOperation = error.config?.url?.startsWith('/auth/') || error.config?.url?.startsWith('/users/register');
            // --- END UPDATED ---

            // --- UPDATED: Check isPublicAuthOperation ---
            if (status === 401 && !isLoginAttempt && !isPublicAuthOperation) {
            // --- END UPDATED ---
                console.warn('[api.ts Response Interceptor] Received 401 Unauthorized on protected route. Logging out.');
                authStore.logout(); // Trigger logout action
                // No reload here, let the component handle redirection or UI change
                return Promise.reject(new Error('Session expired. Please log in again.'));
            }

            // Extract detailed error message from response data
            let detailMessage = 'An error occurred.';
            const responseData = data as any;

            // Handle FastAPI validation errors (detail is an array)
            if (responseData?.detail && Array.isArray(responseData.detail)) {
                 detailMessage = `Validation Error: ${responseData.detail.map((err: any) => `${err.loc?.join('.') ?? 'field'}: ${err.msg}`).join('; ')}`;
            }
            // Handle other FastAPI errors (detail is a string) or custom errors
            else if (responseData?.detail && typeof responseData.detail === 'string') {
                detailMessage = responseData.detail;
            }
            // Handle cases where the error might be directly in the data object (less common)
            else if (typeof data === 'string' && data.length > 0 && data.length < 300) {
                detailMessage = data;
            }
            // Fallback to Axios error message
            else if (error.message) {
                detailMessage = error.message;
            }

            // Prepend status code for clarity, unless it's a 422 validation error where the message is usually sufficient
            const errorMessage = status === 422 ? detailMessage : `Error ${status}: ${detailMessage}`;
            console.error(`[api.ts Response Interceptor] Rejecting with error: ${errorMessage}`); // LOGGING
            return Promise.reject(new Error(errorMessage));

        } else if (error.request) {
            console.error('[api.ts Response Interceptor] Network error or no response received:', error.request);
            return Promise.reject(new Error('Network error or server did not respond. Please check connection.'));
        } else {
            console.error('[api.ts Response Interceptor] Axios setup error:', error.message);
            return Promise.reject(new Error(`Request setup error: ${error.message}`));
        }
    }
);


// --- API Service Object ---

const apiService = {
    /**
        * Logs in a user. Uses base axios for specific headers.
        */
    async login(usernameInput: string, passwordInput: string): Promise<AuthResponse> {
        const params = new URLSearchParams();
        params.append('username', usernameInput);
        params.append('password', passwordInput);
        console.log(`[api.ts login] Attempting login for user: ${usernameInput}`); // LOGGING
        // Use base axios to avoid default JSON headers and ensure correct Content-Type
        // Also avoids the interceptor adding an Authorization header if a previous token exists
        const response = await axios.post<AuthResponse>('/token', params, {
            baseURL: '/', // Use root base URL since '/token' is not under /api/v1
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
        console.log(`[api.ts login] Login successful for user: ${usernameInput}`); // LOGGING
        return response.data;
    },

    /**
        * Validates the header of an uploaded file.
        */
    async validateUpload(formData: FormData): Promise<FileValidationResponse> {
        console.log('[api.ts validateUpload] Attempting file header validation...'); // LOGGING
        // Uses axiosInstance, includes auth token if available and URL requires it
        const response = await axiosInstance.post<FileValidationResponse>('/validate-upload', formData, {
             headers: { 'Content-Type': undefined } // Let browser set Content-Type for FormData
        });
        console.log(`[api.ts validateUpload] Validation response received: isValid=${response.data.is_valid}`); // LOGGING
        return response.data;
    },


    /**
        * Uploads the vendor file (after validation).
        * Returns the full JobResponse object.
        */
    async uploadFile(formData: FormData): Promise<JobResponse> { // Return JobResponse
        console.log('[api.ts uploadFile] Attempting file upload...'); // LOGGING
        // This uses axiosInstance, so /api/v1 prefix is added automatically
        const response = await axiosInstance.post<JobResponse>('/upload', formData, { // Expect JobResponse
                headers: { 'Content-Type': undefined } // Let browser set Content-Type for FormData
        });
        console.log(`[api.ts uploadFile] Upload successful, job ID: ${response.data.id}, Target Level: ${response.data.target_level}`); // LOGGING
        return response.data;
    },

    /**
        * Fetches the status and details of a specific job.
        */
    async getJobStatus(jobId: string): Promise<JobDetails> {
        console.log(`[api.ts getJobStatus] Fetching status for job ID: ${jobId}`); // LOGGING
        const response = await axiosInstance.get<JobDetails>(`/jobs/${jobId}`);
        console.log(`[api.ts getJobStatus] Received status for job ${jobId}:`, response.data.status, `Target Level: ${response.data.target_level}`, `Job Type: ${response.data.job_type}`); // LOGGING
        return response.data;
    },

    /**
        * Fetches statistics for a specific job.
        */
    async getJobStats(jobId: string): Promise<JobStatsData> { // Use the updated interface here
        console.log(`[api.ts getJobStats] Fetching stats for job ID: ${jobId}`); // LOGGING
        // Use the exported JobStatsData interface
        const response = await axiosInstance.get<JobStatsData>(`/jobs/${jobId}/stats`);
        // LOGGING: Log the received stats structure
        console.log(`[api.ts getJobStats] Received stats for job ${jobId}:`, JSON.parse(JSON.stringify(response.data)));
        return response.data;
    },

    /**
     * Fetches the detailed classification results for a specific job.
     * Returns the JobResultsResponse structure containing job type and results list.
     */
    async getJobResults(jobId: string): Promise<JobResultsResponse> {
        console.log(`[api.ts getJobResults] Fetching detailed results for job ID: ${jobId}`); // LOGGING
        const response = await axiosInstance.get<JobResultsResponse>(`/jobs/${jobId}/results`);
        console.log(`[api.ts getJobResults] Received ${response.data.results.length} detailed result items for job ${jobId} (Type: ${response.data.job_type}).`); // LOGGING
        return response.data;
    },

    /**
        * Requests email notification for a job completion.
        */
    async requestNotification(jobId: string, email: string): Promise<NotifyResponse> {
        console.log(`[api.ts requestNotification] Requesting notification for job ${jobId} to email ${email}`); // LOGGING
        const response = await axiosInstance.post<NotifyResponse>(`/jobs/${jobId}/notify`, { email });
        console.log(`[api.ts requestNotification] Notification request response:`, response.data.success); // LOGGING
        return response.data;
    },

    /**
        * Downloads the results file for a completed job.
        */
    async downloadResults(jobId: string): Promise<DownloadResult> {
        console.log(`[api.ts downloadResults] Requesting download for job ID: ${jobId}`); // LOGGING
        const response = await axiosInstance.get(`/jobs/${jobId}/download`, {
            responseType: 'blob',
        });
        const disposition = response.headers['content-disposition'];
        let filename = `results_${jobId}.xlsx`;
        if (disposition?.includes('attachment')) {
            const filenameMatch = disposition.match(/filename\*?=(?:(?:"((?:[^"\\]|\\.)*)")|(?:([^;\n]*)))/i);
            if (filenameMatch?.[1]) { filename = filenameMatch[1].replace(/\\"/g, '"'); }
            else if (filenameMatch?.[2]) {
                    const utf8Match = filenameMatch[2].match(/^UTF-8''(.*)/i);
                    if (utf8Match?.[1]) { try { filename = decodeURIComponent(utf8Match[1]); } catch (e) { filename = utf8Match[1]; } }
                    else { filename = filenameMatch[2]; }
            }
        }
        console.log(`[api.ts downloadResults] Determined download filename: ${filename}`); // LOGGING
        return { blob: response.data as Blob, filename };
    },

    /**
        * Fetches a list of jobs for the current user, with optional filtering/pagination.
        */
    async getJobs(params: GetJobsParams = {}): Promise<JobResponse[]> {
        const cleanedParams = Object.fromEntries(
            Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== '')
        );
        console.log('[api.ts getJobs] Fetching job list with params:', cleanedParams); // LOGGING
        const response = await axiosInstance.get<JobResponse[]>('/jobs/', { params: cleanedParams });
        console.log(`[api.ts getJobs] Received ${response.data.length} jobs.`); // LOGGING
        return response.data;
    },

    // --- User Management API Methods ---

    /**
        * Fetches the current logged-in user's details.
        */
    async getCurrentUser(): Promise<UserResponse> {
        console.log('[api.ts getCurrentUser] Fetching current user details...'); // LOGGING
        const response = await axiosInstance.get<UserResponse>('/users/me');
        console.log(`[api.ts getCurrentUser] Received user: ${response.data.username}`); // LOGGING
        return response.data;
    },

    /**
        * Fetches a list of all users (admin only).
        */
    async getUsers(skip: number = 0, limit: number = 100): Promise<UserResponse[]> {
        console.log(`[api.ts getUsers] Fetching user list (skip: ${skip}, limit: ${limit})...`); // LOGGING
        const response = await axiosInstance.get<UserResponse[]>('/users/', { params: { skip, limit } });
         console.log(`[api.ts getUsers] Received ${response.data.length} users.`); // LOGGING
        return response.data;
    },

        /**
        * Fetches a specific user by ID (admin or self).
        */
        async getUserById(userId: string): Promise<UserResponse> {
        console.log(`[api.ts getUserById] Fetching user ID: ${userId}`); // LOGGING
        const response = await axiosInstance.get<UserResponse>(`/users/${userId}`);
        console.log(`[api.ts getUserById] Received user: ${response.data.username}`); // LOGGING
        return response.data;
    },

    /**
        * Creates a new user (admin only).
        */
    async createUser(userData: UserCreateData): Promise<UserResponse> {
        console.log(`[api.ts createUser] Attempting to create user (admin): ${userData.username}`); // LOGGING
        const response = await axiosInstance.post<UserResponse>('/users/', userData);
        console.log(`[api.ts createUser] User created successfully (admin): ${response.data.username}`); // LOGGING
        return response.data;
    },

    /**
        * Updates a user (admin or self).
        */
    async updateUser(userId: string, userData: UserUpdateData): Promise<UserResponse> {
        console.log(`[api.ts updateUser] Attempting to update user ID: ${userId}`); // LOGGING
        const response = await axiosInstance.put<UserResponse>(`/users/${userId}`, userData);
        console.log(`[api.ts updateUser] User updated successfully: ${response.data.username}`); // LOGGING
        return response.data;
    },

    /**
        * Deletes a user (admin only).
        */
    async deleteUser(userId: string): Promise<{ message: string }> {
        console.log(`[api.ts deleteUser] Attempting to delete user ID: ${userId}`); // LOGGING
        const response = await axiosInstance.delete<{ message: string }>(`/users/${userId}`);
        console.log(`[api.ts deleteUser] User delete response: ${response.data.message}`); // LOGGING
        return response.data;
    },
    // --- END User Management API Methods ---

    // --- ADDED: Public Registration API Method ---
    /**
     * Registers a new user publicly.
     */
    async registerUser(userData: UserCreateData): Promise<UserResponse> {
        console.log(`[api.ts registerUser] Attempting public registration for user: ${userData.username}`);
        // Uses axiosInstance, interceptor skips auth token for this URL
        const response = await axiosInstance.post<UserResponse>('/users/register', userData);
        console.log(`[api.ts registerUser] Public registration successful: ${response.data.username}`);
        return response.data;
    },
    // --- END Public Registration API Method ---


    // --- ADDED: Password Reset API Methods ---
    /**
     * Requests a password reset email to be sent.
     */
    async requestPasswordRecovery(email: string): Promise<MessageResponse> {
        console.log(`[api.ts requestPasswordRecovery] Requesting password reset for email: ${email}`);
        // This uses axiosInstance, but the interceptor should skip adding auth token for this URL
        const response = await axiosInstance.post<MessageResponse>('/auth/password-recovery', { email });
        console.log(`[api.ts requestPasswordRecovery] Request response: ${response.data.message}`);
        return response.data;
    },

    /**
     * Resets the password using the provided token and new password.
     */
    async resetPassword(token: string, newPassword: string): Promise<MessageResponse> {
        console.log(`[api.ts resetPassword] Attempting password reset with token: ${token.substring(0, 10)}...`);
        // This uses axiosInstance, but the interceptor should skip adding auth token for this URL
        const response = await axiosInstance.post<MessageResponse>('/auth/reset-password', {
            token: token,
            new_password: newPassword
        });
        console.log(`[api.ts resetPassword] Reset response: ${response.data.message}`);
        return response.data;
    },
    // --- END Password Reset API Methods ---

    // --- ADDED: Reclassification API Method ---
    /**
     * Submits flagged items for reclassification.
     */
    async reclassifyJob(originalJobId: string, items: ReclassifyRequestItemData[]): Promise<ReclassifyResponseData> {
        console.log(`[api.ts reclassifyJob] Submitting ${items.length} items for reclassification for job ${originalJobId}`);
        const payload = { items: items };
        const response = await axiosInstance.post<ReclassifyResponseData>(`/jobs/${originalJobId}/reclassify`, payload);
        console.log(`[api.ts reclassifyJob] Reclassification job started: ${response.data.review_job_id}`);
        return response.data;
    },
    // --- END ADDED ---

    // --- ADDED: Merge API Method ---
    /**
     * Merges results from a review job into its parent.
     */
    async mergeReviewResults(reviewJobId: string): Promise<MergeResponseData> {
        console.log(`[api.ts mergeReviewResults] Requesting merge for review job ${reviewJobId}`);
        const response = await axiosInstance.post<MergeResponseData>(`/jobs/${reviewJobId}/merge`);
        console.log(`[api.ts mergeReviewResults] Merge request successful: ${response.data.message}`);
        return response.data;
    }
    // --- END ADDED ---
};

export default apiService;