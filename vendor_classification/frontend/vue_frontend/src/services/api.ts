// <file path='frontend/vue_frontend/src/services/api.ts'>
import axios, {
    type AxiosInstance,
    type InternalAxiosRequestConfig,
    type AxiosError // Import AxiosError type
} from 'axios';
import { useAuthStore } from '@/stores/auth'; // Adjust path as needed
import type { JobDetails } from '@/stores/job'; // Adjust path as needed

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

// --- REMOVED UploadResponse - Use JobResponse instead ---
// interface UploadResponse {
//     job_id: string;
//     status: string;
//     message: string;
//     created_at: string;
//     progress: number;
//     current_stage: string;
// }

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
}

// --- UPDATED JobStatsData Interface ---
// Matches backend models/classification.py -> ProcessingStats and console log
export interface JobStatsData {
    job_id: string;
    company_name: string;
    start_time: string | null; // Assuming ISO string
    end_time: string | null; // Assuming ISO string
    processing_duration_seconds: number | null; // Renamed from processing_time
    total_vendors: number | null; // Added
    unique_vendors: number | null; // Added (was present in console)
    target_level: number | null; // Added target level to stats
    successfully_classified_l4: number | null; // Keep for reference
    successfully_classified_l5: number | null; // Keep L5 count
    classification_not_possible_initial: number | null; // Added
    invalid_category_errors: number | null; // Added (was present in console)
    search_attempts: number | null; // Added
    search_successful_classifications_l1: number | null; // Added
    search_successful_classifications_l5: number | null; // Renamed from search_assisted_l5
    api_usage: { // Nested structure
        openrouter_calls: number | null;
        openrouter_prompt_tokens: number | null;
        openrouter_completion_tokens: number | null;
        openrouter_total_tokens: number | null;
        tavily_search_calls: number | null;
        cost_estimate_usd: number | null;
    } | null; // Allow api_usage itself to be null if not populated
}
// --- END UPDATED JobStatsData Interface ---


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
    skip?: number;
    limit?: number;
}

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
        // No need for noAuthUrls here as login uses base axios
        if (token && config.url) {
            // LOGGING: Log token presence and target URL
            // console.log(`[api.ts Request Interceptor] Adding token for URL: ${config.url}`);
            config.headers.Authorization = `Bearer ${token}`;
        } else {
            // console.log(`[api.ts Request Interceptor] No token found or no URL for config: ${config.url}`);
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

            // Handle 401 Unauthorized (except for login attempts)
            // Login uses base axios, so this interceptor won't catch its 401
            if (status === 401) {
                console.warn('[api.ts Response Interceptor] Received 401 Unauthorized. Logging out.');
                authStore.logout(); // Trigger logout action
                // No reload here, let the component handle redirection or UI change
                return Promise.reject(new Error('Session expired. Please log in again.'));
            }

            // Extract detailed error message from response data
            let detailMessage = 'An error occurred.';
            const responseData = data as any;

            if (responseData?.detail) {
                    if (Array.isArray(responseData.detail)) {
                        detailMessage = `Validation Error: ${responseData.detail.map((err: any) => `${err.loc?.join('.') ?? 'field'}: ${err.msg}`).join('; ')}`;
                    } else if (typeof responseData.detail === 'string') {
                        detailMessage = responseData.detail;
                    } else {
                        try { detailMessage = JSON.stringify(responseData.detail); } catch { /* ignore */ }
                    }
            } else if (typeof data === 'string' && data.length > 0 && data.length < 300) {
                detailMessage = data;
            } else if (error.message) {
                detailMessage = error.message;
            }

            const errorMessage = `Error ${status}: ${detailMessage}`;
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
        const response = await axios.post<AuthResponse>('/token', params, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
        console.log(`[api.ts login] Login successful for user: ${usernameInput}`); // LOGGING
        return response.data;
    },

    /**
        * Uploads the vendor file.
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
        console.log(`[api.ts getJobStatus] Received status for job ${jobId}:`, response.data.status, `Target Level: ${response.data.target_level}`); // LOGGING
        return response.data;
    },

    /**
        * Fetches statistics for a specific job.
        */
    async getJobStats(jobId: string): Promise<JobStatsData> { // Use the updated interface here
        console.log(`[api.ts getJobStats] Fetching stats for job ID: ${jobId}`); // LOGGING
        const response = await axiosInstance.get<JobStatsData>(`/jobs/${jobId}/stats`);
        // LOGGING: Log the received stats structure
        console.log(`[api.ts getJobStats] Received stats for job ${jobId}:`, JSON.parse(JSON.stringify(response.data)));
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
            Object.entries(params).filter(([, value]) => value !== undefined && value !== null)
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
        console.log(`[api.ts createUser] Attempting to create user: ${userData.username}`); // LOGGING
        const response = await axiosInstance.post<UserResponse>('/users/', userData);
        console.log(`[api.ts createUser] User created successfully: ${response.data.username}`); // LOGGING
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
};

export default apiService;