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
    status: string; // e.g., 'pending', 'processing'
    message: string;
    created_at: string; // ISO Date string
    progress: number; // 0.0 to 1.0
    current_stage: string; // e.g., 'ingestion'
}

interface NotifyResponse {
    success: boolean;
    message: string;
}

// Reuse JobDetails from the store definition
// interface JobDetails { ... }

interface JobStatsData {
    vendors_processed: number | null;
    unique_vendors: number | null;
    api_calls: number | null; // Renamed from openrouter_calls if backend changed
    tokens_used: number | null; // Renamed from openrouter_total_tokens if backend changed
    tavily_searches: number | null; // Renamed from tavily_search_calls if backend changed
    processing_time: number | null;
    successfully_classified_l4: number | null; // Added
    search_successful_classifications: number | null; // Added
    invalid_category_errors: number | null; // Added
}

interface DownloadResult {
    blob: Blob;
    filename: string;
}

// Create an Axios instance
const axiosInstance: AxiosInstance = axios.create({
    // IMPORTANT: Use a relative path for baseURL when running behind the same server/proxy
    // Or use full URL like 'http://localhost:8000/api/v1' during development if frontend runs on different port
    baseURL: '/api/v1', // Assumes Vite dev server proxies /api/v1 to your backend
    timeout: 60000, // 60 seconds timeout (increased for potential long operations)
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
});

// --- Request Interceptor ---
// Adds the auth token to requests if available
axiosInstance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        // Get store instance *inside* the interceptor function scope
        const authStore = useAuthStore();
        const token = authStore.getToken();

        // Exclude token endpoint from adding Authorization header
        // Also might exclude public endpoints if any exist later
        const noAuthUrls = ['/token']; // Add other paths if needed

        if (token && config.url && !noAuthUrls.includes(config.url)) {
            // console.log(`Interceptor: Adding token to ${config.method?.toUpperCase()} ${config.url}`);
            config.headers.Authorization = `Bearer ${token}`;
        } else {
            // console.log(`Interceptor: No token or excluded URL for ${config.method?.toUpperCase()} ${config.url}`);
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
    (response) => response, // Pass through successful responses
    (error) => {
        console.error('Axios response error:', error.config?.url, error.response?.status, error.message);
        const authStore = useAuthStore(); // Get store instance inside interceptor

        if (error.response) {
            const { status, data, config } = error.response;

            // --- Handle 401 Unauthorized ---
             // Exclude failures on the /token endpoint itself from triggering logout
            if (status === 401 && !config.url?.includes('/token')) {
                console.warn('Interceptor: Received 401 Unauthorized. Logging out.');
                authStore.logout(); // Trigger logout action in the store
                // Reload or redirect to force UI update and clear state
                 window.location.reload(); // Simple way to reset app state
                // Return a specific rejected promise to prevent further component processing
                return Promise.reject(new Error('Session expired. Please log in again.'));
            }

            // --- Extract FastAPI/General Error Details ---
            let detailMessage = 'An error occurred.';
            if (data?.detail) {
                 if (Array.isArray(data.detail)) { // Handle Pydantic validation errors
                     detailMessage = `Validation Error: ${data.detail.map((err: any) => `${err.loc?.join('.') ?? 'field'}: ${err.msg}`).join('; ')}`;
                 } else if (typeof data.detail === 'string') { // Standard FastAPI HTTPException detail
                     detailMessage = data.detail;
                 } else { // Other cases (e.g., detail is an object)
                     try { detailMessage = JSON.stringify(data.detail); } catch { /* ignore */}
                 }
            } else if (typeof data === 'string' && data.length > 0 && data.length < 300) { // Use raw response if it's a short string
                detailMessage = data;
            } else if (error.message) { // Fallback to Axios error message
                detailMessage = error.message;
            }

            const errorMessage = `Error ${status}: ${detailMessage}`;
            // Reject with a new error containing the extracted message
            return Promise.reject(new Error(errorMessage));

        } else if (error.request) {
            // Request was made but no response received
            console.error('Network error or no response received:', error.request);
            return Promise.reject(new Error('Network error or server did not respond. Please check connection.'));
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
     * Logs in a user. Note: Uses base axios for specific headers.
     */
    async login(usernameInput: string, passwordInput: string): Promise<AuthResponse> {
        const params = new URLSearchParams();
        params.append('username', usernameInput);
        params.append('password', passwordInput);

        // Use base axios to avoid default JSON headers and auth interceptor
        // Base URL for token is '/' assuming FastAPI serves it at the root
        const response = await axios.post<AuthResponse>('/token', params, {
            baseURL: '/', // Explicitly set base URL for login if needed
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
        return response.data; // Interceptor handles non-200 errors here too if using base axios
    },

    /**
     * Uploads the vendor file.
     */
    async uploadFile(formData: FormData): Promise<UploadResponse> {
        // Use the configured axiosInstance (handles auth token, base URL /api/v1)
        const response = await axiosInstance.post<UploadResponse>('/upload', formData, {
             headers: {
                // Let Axios set Content-Type for FormData
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
            responseType: 'blob', // Crucial for file downloads
        });

        // Extract filename from Content-Disposition header
        const disposition = response.headers['content-disposition'];
        let filename = `results_${jobId}.xlsx`; // Sensible default
        if (disposition?.includes('attachment')) {
            const filenameMatch = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (filenameMatch?.[1]) {
                filename = filenameMatch[1].replace(/['"]/g, '');
            }
        }

        return { blob: response.data as Blob, filename };
    },
};

export default apiService;