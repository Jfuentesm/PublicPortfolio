
// frontend/vue_frontend/src/services/api.ts
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

// Matches backend response for /api/v1/upload
interface UploadResponse {
    job_id: string;
    status: string;
    message: string;
    created_at: string;
    progress: number;
    current_stage: string;
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
        const authStore = useAuthStore();
        const token = authStore.getToken();
        // No need for noAuthUrls here as login uses base axios
        if (token && config.url) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error: AxiosError) => {
        console.error('Axios request interceptor error:', error);
        return Promise.reject(error);
    }
);

// --- Response Interceptor (Handle Errors) ---
axiosInstance.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
        console.error('Axios response error:', error.config?.url, error.response?.status, error.message);
        const authStore = useAuthStore();

        if (error.response) {
            const { status, data } = error.response;

            // Handle 401 Unauthorized (except for login attempts)
            // Login uses base axios, so this interceptor won't catch its 401
            if (status === 401) {
                console.warn('Interceptor: Received 401 Unauthorized. Logging out.');
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
            return Promise.reject(new Error(errorMessage));

        } else if (error.request) {
            console.error('Network error or no response received:', error.request);
            return Promise.reject(new Error('Network error or server did not respond. Please check connection.'));
        } else {
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
        const response = await axiosInstance.post<UploadResponse>('/upload', formData, {
                headers: { 'Content-Type': undefined }
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
        console.log(`api.ts: Determined download filename: ${filename}`);
        return { blob: response.data as Blob, filename };
    },

    /**
        * Fetches a list of jobs for the current user, with optional filtering/pagination.
        */
    async getJobs(params: GetJobsParams = {}): Promise<JobResponse[]> {
        const cleanedParams = Object.fromEntries(
            Object.entries(params).filter(([, value]) => value !== undefined && value !== null)
        );
        const response = await axiosInstance.get<JobResponse[]>('/jobs/', { params: cleanedParams });
        return response.data;
    },

    // --- ADDED User Management API Methods ---

    /**
        * Fetches the current logged-in user's details.
        */
    async getCurrentUser(): Promise<UserResponse> {
        const response = await axiosInstance.get<UserResponse>('/users/me');
        return response.data;
    },

    /**
        * Fetches a list of all users (admin only).
        */
    async getUsers(skip: number = 0, limit: number = 100): Promise<UserResponse[]> {
        const response = await axiosInstance.get<UserResponse[]>('/users/', { params: { skip, limit } });
        return response.data;
    },

        /**
        * Fetches a specific user by ID (admin or self).
        */
        async getUserById(userId: string): Promise<UserResponse> {
        const response = await axiosInstance.get<UserResponse>(`/users/${userId}`);
        return response.data;
    },

    /**
        * Creates a new user (admin only).
        */
    async createUser(userData: UserCreateData): Promise<UserResponse> {
        const response = await axiosInstance.post<UserResponse>('/users/', userData);
        return response.data;
    },

    /**
        * Updates a user (admin or self).
        */
    async updateUser(userId: string, userData: UserUpdateData): Promise<UserResponse> {
        const response = await axiosInstance.put<UserResponse>(`/users/${userId}`, userData);
        return response.data;
    },

    /**
        * Deletes a user (admin only).
        */
    async deleteUser(userId: string): Promise<{ message: string }> {
        const response = await axiosInstance.delete<{ message: string }>(`/users/${userId}`);
        return response.data;
    },
    // --- END User Management API Methods ---
};

export default apiService;