// frontend/vue_frontend/src/services/api.ts
import axios, {
    type AxiosInstance,
    type InternalAxiosRequestConfig,
    type AxiosError // Import AxiosError type
} from 'axios';
import { useAuthStore } from '@/stores/auth'; // Adjust path as needed
import type { JobDetails } from '@/stores/job'; // Adjust path as needed

// --- Define API Response Interfaces ---

// Matches backend response for /token
interface AuthResponse {
    access_token: string;
    token_type: string;
    username: string;
}

// Matches backend response for /api/v1/upload
interface UploadResponse {
    job_id: string;
    status: string; // e.g., 'pending', 'processing'
    message: string;
    created_at: string; // ISO Date string
    progress: number; // 0.0 to 1.0
    current_stage: string; // e.g., 'ingestion'
}

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
}

// Matches backend response for /api/v1/jobs/{job_id}/stats
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
        const authStore = useAuthStore(); // Get store instance inside interceptor
        const token = authStore.getToken();
        const noAuthUrls = ['/token']; // URLs that don't need auth

        // Add token if available and URL is not excluded
        if (token && config.url && !noAuthUrls.some(url => config.url?.startsWith(url))) {
            // console.log(`Interceptor: Adding token to ${config.method?.toUpperCase()} ${config.url}`);
            config.headers.Authorization = `Bearer ${token}`;
        } else {
            // console.log(`Interceptor: No token or excluded URL for ${config.method?.toUpperCase()} ${config.url}`);
        }
        return config;
    },
    (error: AxiosError) => { // Add type annotation
        console.error('Axios request interceptor error:', error);
        return Promise.reject(error);
    }
);

// --- Response Interceptor (Handle Errors) ---
axiosInstance.interceptors.response.use(
    (response) => response, // Pass through successful responses
    (error: AxiosError) => { // Add type annotation for error
        console.error('Axios response error:', error.config?.url, error.response?.status, error.message);
        const authStore = useAuthStore(); // Get store instance inside interceptor

        if (error.response) {
            const { status, data, config } = error.response;

            // Handle 401 Unauthorized (except for login attempts)
            if (status === 401 && !config?.url?.includes('/token')) {
                console.warn('Interceptor: Received 401 Unauthorized. Logging out.');
                authStore.logout(); // Trigger logout action
                window.location.reload(); // Force reload to clear state
                return Promise.reject(new Error('Session expired. Please log in again.'));
            }

            // Extract detailed error message from response data
            let detailMessage = 'An error occurred.';
            const responseData = data as any; // Use 'any' for flexible access to 'detail'

            if (responseData?.detail) {
                 if (Array.isArray(responseData.detail)) { // Handle Pydantic validation errors
                     detailMessage = `Validation Error: ${responseData.detail.map((err: any) => `${err.loc?.join('.') ?? 'field'}: ${err.msg}`).join('; ')}`;
                 } else if (typeof responseData.detail === 'string') { // Standard FastAPI HTTPException detail
                     detailMessage = responseData.detail;
                 } else { // Other cases (e.g., detail is an object)
                     try { detailMessage = JSON.stringify(responseData.detail); } catch { /* ignore */ }
                 }
            } else if (typeof data === 'string' && data.length > 0 && data.length < 300) { // Use raw response if short string
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


// --- API Service Object ---

const apiService = {
    /**
     * Logs in a user. Uses base axios for specific headers.
     */
    async login(usernameInput: string, passwordInput: string): Promise<AuthResponse> {
        const params = new URLSearchParams();
        params.append('username', usernameInput);
        params.append('password', passwordInput);

        // Use base axios to avoid default JSON headers and ensure correct Content-Type
        // Assume /token is at the root relative to the domain
        const response = await axios.post<AuthResponse>('/token', params, {
            baseURL: '/', // Use root base URL for the token endpoint
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
        return response.data;
    },

    /**
     * Uploads the vendor file.
     */
    async uploadFile(formData: FormData): Promise<UploadResponse> {
        // Use the configured axiosInstance (handles auth token, base URL /api/v1)
        const response = await axiosInstance.post<UploadResponse>('/upload', formData, {
             headers: {
                // Let Axios set Content-Type automatically for FormData
                'Content-Type': undefined,
             }
        });
        return response.data;
    },

    /**
     * Fetches the status and details of a specific job.
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
     * Requests email notification for a job completion.
     */
    async requestNotification(jobId: string, email: string): Promise<NotifyResponse> {
        const response = await axiosInstance.post<NotifyResponse>(`/jobs/${jobId}/notify`, { email });
        return response.data;
    },

    /**
     * Downloads the results file for a completed job.
     */
    async downloadResults(jobId: string): Promise<DownloadResult> {
        const response = await axiosInstance.get(`/jobs/${jobId}/download`, {
            responseType: 'blob', // Crucial for handling file downloads
        });

        // Extract filename from Content-Disposition header
        const disposition = response.headers['content-disposition'];
        let filename = `results_${jobId}.xlsx`; // Sensible default filename
        if (disposition?.includes('attachment')) {
            // Regex to find filename="some file.xlsx" or filename*=UTF-8''some%20file.xlsx
            const filenameMatch = disposition.match(/filename\*?=(?:(?:"((?:[^"\\]|\\.)*)")|(?:([^;\n]*)))/i);
            if (filenameMatch?.[1]) { // Quoted filename
                filename = filenameMatch[1].replace(/\\"/g, '"'); // Handle escaped quotes
            } else if (filenameMatch?.[2]) { // Unquoted filename
                 // Handle potential encoding like filename*=UTF-8''...
                 const utf8Match = filenameMatch[2].match(/^UTF-8''(.*)/i);
                 if (utf8Match?.[1]) {
                     try {
                         filename = decodeURIComponent(utf8Match[1]);
                     } catch (e) {
                         console.warn("Failed to decode UTF-8 filename, using raw:", utf8Match[1]);
                         filename = utf8Match[1]; // Fallback to raw value
                     }
                 } else {
                     filename = filenameMatch[2]; // Use as is if not UTF-8 encoded
                 }
            }
        }

        console.log(`api.ts: Determined download filename: ${filename}`); // Logging filename
        return { blob: response.data as Blob, filename };
    },

    /**
     * Fetches a list of jobs for the current user, with optional filtering/pagination.
     */
    async getJobs(params: GetJobsParams = {}): Promise<JobResponse[]> {
        // Clean up params: remove undefined/null values before sending
        const cleanedParams = Object.fromEntries(
          Object.entries(params).filter(([, value]) => value !== undefined && value !== null)
        );
        const response = await axiosInstance.get<JobResponse[]>('/jobs/', { params: cleanedParams });
        return response.data;
    },
};

export default apiService;