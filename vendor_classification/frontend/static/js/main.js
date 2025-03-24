document.addEventListener('DOMContentLoaded', function() {
    // Authentication elements
    const loginForm = document.getElementById('loginForm');
    const loginCard = document.getElementById('loginCard');
    const uploadCard = document.getElementById('uploadCard');
    const userInfo = document.getElementById('userInfo');
    const usernameDisplay = document.getElementById('usernameDisplay');
    const logoutButton = document.getElementById('logoutButton');
    
    // Existing form elements
    const uploadForm = document.getElementById('uploadForm');
    const jobStatusCard = document.getElementById('jobStatus');
    const jobStatsCard = document.getElementById('jobStats');
    const downloadDiv = document.getElementById('downloadDiv');
    const downloadLink = document.getElementById('downloadLink');
    const notifyButton = document.getElementById('notifyButton');
    
    // Authentication state
    let authToken = localStorage.getItem('authToken');
    let currentUser = localStorage.getItem('currentUser');
    
    // Process stage names for display
    const stageNames = {
        'ingestion': 'File Ingestion',
        'normalization': 'Vendor Name Normalization',
        'classification_level_1': 'Level 1 Classification',
        'classification_level_2': 'Level 2 Classification',
        'classification_level_3': 'Level 3 Classification',
        'classification_level_4': 'Level 4 Classification',
        'search_unknown_vendors': 'Vendor Research',
        'result_generation': 'Result Generation'
    };
    
    // Function to check if user is authenticated
    function isAuthenticated() {
        return authToken !== null;
    }
    
    // Function to update UI based on authentication status
    function updateAuthUI() {
        if (isAuthenticated()) {
            loginCard.classList.add('d-none');
            uploadCard.classList.remove('d-none');
            userInfo.classList.remove('d-none');
            usernameDisplay.textContent = currentUser || 'User';
        } else {
            loginCard.classList.remove('d-none');
            uploadCard.classList.add('d-none');
            userInfo.classList.add('d-none');
            jobStatusCard.classList.add('d-none');
            jobStatsCard.classList.add('d-none');
        }
    }
    
    // Login form submission handler
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        try {
            const response = await fetch('/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'username': username,
                    'password': password
                })
            });
            
            if (!response.ok) {
                throw new Error('Login failed. Please check your credentials.');
            }
            
            const data = await response.json();
            
            // Store authentication data
            authToken = data.access_token;
            currentUser = data.username;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', currentUser);
            
            // Update UI
            updateAuthUI();
            
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    });
    
    // Logout button handler
    logoutButton.addEventListener('click', function() {
        // Clear authentication data
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        authToken = null;
        currentUser = null;
        
        // Update UI
        updateAuthUI();
    });
    
    // Intercept fetch requests to add authorization header
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        // Clone the options to avoid modifying the original object
        const newOptions = { ...options };
        
        // If authenticated, add the token to API requests
        if (authToken && (url.startsWith('/api') || url === '/token')) {
            newOptions.headers = { 
                ...(newOptions.headers || {}),
                'Authorization': `Bearer ${authToken}`
            };
        }
        
        return originalFetch(url, newOptions);
    };

    // Update UI on page load based on authentication status
    updateAuthUI();
    
    // Form submission handler
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(uploadForm);
        
        try {
            // Updated to match the backend API routes
            const response = await fetch('/api/v1/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error uploading file');
            }
            
            const data = await response.json();
            
            // Show job status card
            jobStatusCard.classList.remove('d-none');
            
            // Update job status information
            document.getElementById('jobId').textContent = data.job_id;
            document.getElementById('status').textContent = data.status;
            document.getElementById('currentStage').textContent = stageNames[data.current_stage] || data.current_stage;
            document.getElementById('progressBar').style.width = `${data.progress * 100}%`;
            document.getElementById('createdAt').textContent = new Date(data.created_at).toLocaleString();
            document.getElementById('updatedAt').textContent = new Date(data.updated_at).toLocaleString();
            
            // Start polling for job status
            pollJobStatus(data.job_id);
            
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    });
    
    // Notification email handler
    notifyButton.addEventListener('click', async function() {
        const email = document.getElementById('notificationEmail').value;
        const jobId = document.getElementById('jobId').textContent;
        
        if (!email) {
            alert('Please enter an email address');
            return;
        }
        
        try {
            // Updated to match the backend API routes
            const response = await fetch(`/api/v1/jobs/${jobId}/notify`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email: email })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error setting notification');
            }
            
            alert('Notification set! You will receive an email when processing is complete.');
            
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    });
    
    // Function to poll job status
    async function pollJobStatus(jobId) {
        try {
            // Updated to match the backend API routes
            const response = await fetch(`/api/v1/jobs/${jobId}`);
            
            if (!response.ok) {
                throw new Error('Error fetching job status');
            }
            
            const data = await response.json();
            
            // Update job status information
            document.getElementById('status').textContent = data.status;
            document.getElementById('currentStage').textContent = stageNames[data.current_stage] || data.current_stage;
            document.getElementById('progressBar').style.width = `${data.progress * 100}%`;
            document.getElementById('updatedAt').textContent = new Date(data.updated_at).toLocaleString();
            
            // Calculate estimated completion time
            if (data.estimated_completion) {
                document.getElementById('estimatedCompletion').textContent = 
                    new Date(data.estimated_completion).toLocaleString();
            } else {
                document.getElementById('estimatedCompletion').textContent = 'Calculating...';
            }
            
            // Check if job is completed
            if (data.status === 'completed') {
                // Show download link
                downloadDiv.style.display = 'block';
                // Updated to match the backend API routes
                downloadLink.href = `/api/v1/jobs/${jobId}/download`;
                
                // Show job statistics
                fetchJobStats(jobId);
                
                // Stop polling
                return;
            }
            
            // Continue polling if job is still in progress
            if (data.status === 'processing') {
                setTimeout(() => pollJobStatus(jobId), 5000);
            }
            
        } catch (error) {
            console.error('Error polling job status:', error);
            // Retry after a longer delay if there was an error
            setTimeout(() => pollJobStatus(jobId), 10000);
        }
    }
    
    // Function to fetch job statistics
    async function fetchJobStats(jobId) {
        try {
            // Updated to match the backend API routes
            const response = await fetch(`/api/v1/jobs/${jobId}/stats`);
            
            if (!response.ok) {
                throw new Error('Error fetching job statistics');
            }
            
            const stats = await response.json();
            
            // Show job statistics card
            jobStatsCard.classList.remove('d-none');
            
            // Update statistics information
            document.getElementById('vendorsProcessed').textContent = stats.vendors_processed || 'N/A';
            document.getElementById('uniqueVendors').textContent = stats.unique_vendors || 'N/A';
            document.getElementById('apiCalls').textContent = stats.api_calls || 'N/A';
            document.getElementById('tokensUsed').textContent = stats.tokens_used || 'N/A';
            document.getElementById('tavilySearches').textContent = stats.tavily_searches || 'N/A';
            document.getElementById('processingTime').textContent = 
                stats.processing_time?.toFixed(2) || 'N/A';
            
        } catch (error) {
            console.error('Error fetching job statistics:', error);
        }
    }
    
    // Check if there's a job ID in the URL (for returning users)
    const urlParams = new URLSearchParams(window.location.search);
    const jobId = urlParams.get('job_id');
    
    if (jobId) {
        // Show job status card
        jobStatusCard.classList.remove('d-none');
        
        // Set job ID
        document.getElementById('jobId').textContent = jobId;
        
        // Start polling for job status
        pollJobStatus(jobId);
    }
});