import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/auth'; // Adjust path as needed
import type { JobDetails } from '@/stores/job'; // Adjust path as needed

// Define expected API response types (adjust based on your actual backend)
interface AuthResponse {
    access_token: string;
    token_type: string;
    username: string;
}

interface UploadResponse {
    job_id: string;
    status: string;
    message: string;
    created_at: string;
    progress: number;
    current_stage: string;
}

interface NotifyResponse {
    success: boolean;
    message: string;
}

interface JobStatsData {
    vendors_processed: number | null;
    unique_vendors: number | null;
    api_calls: number | null;
    tokens_used: number | null;
    tavily_searches: number | null;
    processing_time: number | null;
    successfully_classified_l4: number | null;
    search_successful_classifications: number | null;
    invalid_category_errors: number | null;
}

interface DownloadResult {
    blob: Blob;
    filename: string;
}

// Create an Axios instance
const axiosInstance: AxiosInstance = axios.create({
    baseURL: '/api/v1', // Base URL for your API endpoints
    timeout: 30000, // 30 seconds timeout
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
});

// --- Request Interceptor ---
// Adds the auth token to requests if available
axiosInstance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        // IMPORTANT: Get store instance inside the interceptor
        const authStore = useAuthStore();
        const token = authStore.getToken(); // Use the action to get token

        // Don't add token to the login request itself
        if (token && config.url !== '/token') {
            console.log(`Interceptor: Adding token to ${config.method?.toUpperCase()} ${config.url}`);
            config.headers.Authorization = `Bearer ${token}`;
        } else {
            // console.log(`Interceptor: No token or login request for ${config.method?.toUpperCase()} ${config.url}`);
        }
        return config;
    },
    (error) => {
        console.error('Axios request interceptor error:', error);
        return Promise.reject(error);
    }
);

// --- Response Interceptor ---
// Handles common errors like 401 Unauthorized
axiosInstance.interceptors.response.use(
    (response) => {
        // Any status code within 2xx range triggers this
        return response;
    },
    (error) => {
        // Any status codes outside 2xx range triggers this
        console.error('Axios response interceptor error:', error.config?.url, error.response?.status, error.message);
        const authStore = useAuthStore(); // Get store instance inside interceptor

        if (error.response) {
            // --- Handle 401 Unauthorized ---
            if (error.response.status === 401 && error.config.url !== '/token') {
                console.warn('Interceptor: Received 401 Unauthorized. Logging out.');
                authStore.logout(); // Trigger logout action
                // Optionally redirect to login page or show a global message
                // window.location.href = '/login';
                // Return a specific rejected promise to prevent further component processing
                return Promise.reject(new Error('Session expired. Please log in again.'));
            }

            // --- Extract FastAPI Error Details ---
            // Try to get detail from response.data.detail (FastAPI standard)
            let detailMessage = 'An error occurred.';
            if (error.response.data?.detail) {
                 if (Array.isArray(error.response.data.detail)) {
                     // Handle Pydantic validation errors
                     detailMessage = `Validation Error: ${error.response.data.detail.map((err: any) => `${err.loc?.join('.') ?? 'field'}: ${err.msg}`).join('; ')}`;
                 } else if (typeof error.response.data.detail === 'string') {
                     detailMessage = error.response.data.detail;
                 } else {
                     try { detailMessage = JSON.stringify(error.response.data.detail); } catch { /* ignore */ }
                 }
            } else if (typeof error.response.data === 'string') {
                detailMessage = error.response.data.substring(0, 200); // Use raw response text if detail is missing
            }

            // Add status code for context
            const errorMessage = `Error ${error.response.status}: ${detailMessage}`;
            // Reject with a new error containing the extracted message
            return Promise.reject(new Error(errorMessage));

        } else if (error.request) {
            // Request was made but no response received (network error, timeout)
            console.error('Network error or no response:', error.request);
            return Promise.reject(new Error('Network error or server did not respond. Please try again.'));
        } else {
            // Something happened setting up the request
            console.error('Axios setup error:', error.message);
            return Promise.reject(new Error(`Request setup error: ${error.message}`));
        }
    }
);


// --- API Service Functions ---

const apiService = {
    /**
     * Logs in a user.
     */
    async login(usernameInput: string, passwordInput: string): Promise<AuthResponse> {
        // Login requires 'application/x-www-form-urlencoded'
        const params = new URLSearchParams();
        params.append('username', usernameInput);
        params.append('password', passwordInput);

        // Make request *without* default JSON content type and *without* auth interceptor adding token
        // Use base axios or configure instance specifically for this call if needed
        try {
             const response = await axios.post<AuthResponse>('/token', params, { // Use base path defined in main.py
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                baseURL: '/', // Override baseURL if /token is not under /api/v1
            });
            return response.data;
        } catch (error: any) {
            // Handle specific login errors (e.g., 401 manually if not using interceptor fully)
             let detailMessage = 'Login failed.';
             if (error.response?.data?.detail) {
                detailMessage = error.response.data.detail;
             } else if (error.response?.status === 401) {
                 detailMessage = 'Incorrect username or password.';
             } else if (error.message) {
                 detailMessage = error.message;
             }
             throw new Error(detailMessage);
        }
    },

    /**
     * Uploads the vendor file.
     */
    async uploadFile(formData: FormData): Promise<UploadResponse> {
        // Axios automatically sets Content-Type to multipart/form-data for FormData
        const response = await axiosInstance.post<UploadResponse>('/upload', formData, {
             headers: {
                // Let Axios handle the Content-Type for FormData
                'Content-Type': undefined,
             }
        });
        return response.data;
    },

    /**
     * Fetches the status of a specific job.
     */
    async getJobStatus(jobId: string): Promise<JobDetails> {
        const response = await axiosInstance.get<JobDetails>(`/jobs/${jobId}`);
        return response.data;
    },

    /**
     * Fetches statistics for a specific job.
     */
    async getJobStats(jobId: string): Promise<JobStatsData> {
        const response = await axiosInstance.get<JobStatsData>(`/jobs/${jobId}/stats`);
        return response.data;
    },

    /**
     * Requests email notification for a job.
     */
    async requestNotification(jobId: string, email: string): Promise<NotifyResponse> {
        const response = await axiosInstance.post<NotifyResponse>(`/jobs/${jobId}/notify`, { email });
        return response.data;
    },

    /**
     * Downloads the results file for a job.
     */
    async downloadResults(jobId: string): Promise<DownloadResult> {
        const response = await axiosInstance.get(`/jobs/${jobId}/download`, {
            responseType: 'blob', // Important for file downloads
        });

        // Extract filename from Content-Disposition header
        const disposition = response.headers['content-disposition'];
        let filename = `job_${jobId}_results.xlsx`; // Default filename
        if (disposition && disposition.includes('attachment')) {
            const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
            const matches = filenameRegex.exec(disposition);
            if (matches?.[1]) {
                filename = matches[1].replace(/['"]/g, '');
            }
        }

        return { blob: response.data as Blob, filename };
    },
};

export default apiService;