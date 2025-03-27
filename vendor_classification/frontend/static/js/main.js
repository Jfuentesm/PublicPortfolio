// frontend/static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded and parsed.');

    // --- Elements ---
    const loginForm = document.getElementById('loginForm');
    const loginCard = document.getElementById('loginCard');
    const uploadCard = document.getElementById('uploadCard');
    const userInfo = document.getElementById('userInfo');
    const usernameDisplay = document.getElementById('usernameDisplay');
    const logoutButton = document.getElementById('logoutButton');
    const uploadForm = document.getElementById('uploadForm');
    const jobStatusCard = document.getElementById('jobStatus');
    const jobStatsCard = document.getElementById('jobStats');
    const downloadDiv = document.getElementById('downloadDiv');
    // --- MODIFICATION: Get the button/link itself ---
    const downloadButton = document.getElementById('downloadLink'); // Treat it as a button now
    // --- END MODIFICATION ---
    const notifyButton = document.getElementById('notifyButton');
    const uploadButton = document.getElementById('uploadButton');
    const jobIdEl = document.getElementById('jobId');
    const statusEl = document.getElementById('status');
    const stageEl = document.getElementById('currentStage');
    const progressEl = document.getElementById('progressBar');
    const createdEl = document.getElementById('createdAt');
    const updatedEl = document.getElementById('updatedAt');
    const estimatedEl = document.getElementById('estimatedCompletion');
    const vendorsProcessedEl = document.getElementById('vendorsProcessed');
    const uniqueVendorsEl = document.getElementById('uniqueVendors');
    const apiCallsEl = document.getElementById('apiCalls');
    const tokensUsedEl = document.getElementById('tokensUsed');
    const tavilySearchesEl = document.getElementById('tavilySearches');
    const processingTimeEl = document.getElementById('processingTime');

    console.log('Verifying initial elements:', { loginForm: !!loginForm, loginCard: !!loginCard, uploadCard: !!uploadCard, userInfo: !!userInfo, usernameDisplay: !!usernameDisplay, logoutButton: !!logoutButton, uploadForm: !!uploadForm, jobStatusCard: !!jobStatusCard, jobStatsCard: !!jobStatsCard, uploadButton: !!uploadButton, downloadDiv: !!downloadDiv, downloadButton: !!downloadButton, notifyButton: !!notifyButton }); // Changed downloadLink to downloadButton
    if (!loginCard || !uploadCard || !userInfo || !uploadForm || !jobStatusCard || !jobStatsCard || !uploadButton || !downloadButton) { // Added downloadButton check
         console.error("CRITICAL: One or more essential UI elements are missing.");
         alert("UI Error: Essential page elements could not be found.");
    }

    // --- State ---
    let authToken = localStorage.getItem('authToken');
    let currentUser = localStorage.getItem('currentUser');
    let pollingIntervalId = null;
    let currentJobId = null; // Store the current job ID

    // --- Constants ---
    const stageNames = { 'ingestion': 'File Ingestion', 'normalization': 'Vendor Name Normalization', 'classification_level_1': 'Level 1 Classification', 'classification_level_2': 'Level 2 Classification', 'classification_level_3': 'Level 3 Classification', 'classification_level_4': 'Level 4 Classification', 'search_unknown_vendors': 'Vendor Research', 'result_generation': 'Result Generation' };
    const POLLING_INTERVAL = 5000;
    const POLLING_RETRY_INTERVAL = 15000;

    // --- Auth Functions ---
    function isAuthenticated() {
        return authToken !== null;
    }

    function updateAuthUI() {
        console.log('Updating Auth UI...');
        if (!loginCard || !uploadCard || !userInfo || !jobStatusCard || !jobStatsCard) {
            console.error('One or more UI elements missing in updateAuthUI!'); return;
        }
        console.log('All elements verified in updateAuthUI.');

        if (isAuthenticated()) {
            console.log('User IS authenticated.');
            loginCard.classList.add('d-none');
            uploadCard.classList.remove('d-none');
            userInfo.classList.remove('d-none');
            if(usernameDisplay) usernameDisplay.textContent = currentUser || 'User';
        } else {
            console.log('User IS NOT authenticated.');
            loginCard.classList.remove('d-none');
            uploadCard.classList.add('d-none');
            userInfo.classList.add('d-none');
            jobStatusCard.classList.add('d-none');
            jobStatsCard.classList.add('d-none');
            stopPolling();
            currentJobId = null; // Clear job ID on logout
        }
        console.log('Auth UI update complete.');
    }

    function handleLogout() {
        console.log('Logout initiated.');
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        authToken = null;
        currentUser = null;
        updateAuthUI();
        if(uploadForm) uploadForm.reset();
        if(uploadButton) uploadButton.disabled = false;
        if(uploadButton) uploadButton.textContent = 'Upload and Process';
    }

    // --- API Fetch Interceptor ---
    const originalFetch = window.fetch;
    window.fetch = async function(url, options = {}) {
        const newOptions = { ...options };
        console.log(`Making fetch request: ${options.method || 'GET'} ${url}`);

        if (authToken && url.startsWith('/api') && url !== '/token') {
             console.log(`Adding Auth token for request to: ${url}`);
            newOptions.headers = { ...(newOptions.headers || {}), 'Authorization': `Bearer ${authToken}` };
             console.log('Request headers:', newOptions.headers);
        } else {
            console.log(`Skipping Auth token for: ${url}`);
        }

        try {
            const response = await originalFetch(url, newOptions);

            if (response.status === 401 && url !== '/token') {
                console.warn(`Received 401 Unauthorized for ${url}. Token likely expired. Logging out.`);
                alert("Your session has expired. Please log in again.");
                handleLogout();
                const error = new Error("Session expired (401)");
                error.isHandledAuthError = true;
                throw error;
            }

            return response;

        } catch (error) {
            console.error(`Fetch interceptor error for ${url}:`, error);
            throw error;
        }
    };


    // --- Event Listeners ---
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('Login form submitted.');
            const usernameInput = document.getElementById('username');
            const passwordInput = document.getElementById('password');
            const username = usernameInput ? usernameInput.value : '';
            const password = passwordInput ? passwordInput.value : '';

            try {
                console.log('Attempting login request...');
                const response = await fetch('/token', { // Login uses non-intercepted fetch logic for 401
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({ 'username': username, 'password': password })
                });

                console.log('Login response status:', response.status);
                if (!response.ok) {
                    let errorMsg = 'Login failed. Please check credentials.';
                    try { const errorData = await response.json(); errorMsg = errorData.detail || errorMsg; } catch (jsonError) {}
                    throw new Error(errorMsg);
                }

                const data = await response.json();
                console.log('Login successful:', data);
                authToken = data.access_token;
                currentUser = data.username;
                localStorage.setItem('authToken', authToken);
                localStorage.setItem('currentUser', currentUser);
                updateAuthUI();
            } catch (error) {
                console.error('Login error:', error);
                alert(`Login Error: ${error.message}`);
            }
        });
    } else { console.error("Login form not found!"); }

    if (logoutButton) {
        logoutButton.addEventListener('click', handleLogout);
    } else { console.error("Logout button not found!"); }

    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('Upload form submitted.');
            if(uploadButton) uploadButton.disabled = true;
            if(uploadButton) uploadButton.textContent = 'Processing...';

            const formData = new FormData(uploadForm);
            const fileInput = document.getElementById('vendorFile');
            const file = fileInput ? fileInput.files[0] : null;

            console.log('Form Data prepared:', { company_name: formData.get('company_name'), file_name: file?.name, file_size: file?.size, file_type: file?.type });
            if (!file) {
                alert("Please select a file to upload.");
                if(uploadButton) uploadButton.disabled = false;
                if(uploadButton) uploadButton.textContent = 'Upload and Process';
                return;
            }

            let response;
            try {
                console.log('Attempting file upload request...');
                response = await fetch('/api/v1/upload', { method: 'POST', body: formData }); // Uses interceptor

                console.log('Upload response status:', response.status);
                console.log('Upload response headers:', Object.fromEntries(response.headers.entries()));

                if (!response.ok) { // Interceptor handles 401
                    let errorMsg = 'Error uploading file';
                    let errorDetails = null;
                    try {
                        const errorData = await response.json();
                        console.error('Upload failed with JSON response:', errorData);
                        if (response.status === 422 && errorData.detail && Array.isArray(errorData.detail)) {
                           errorMsg = `Validation Error: ${errorData.detail.map(err => `${err.loc.join('.')}: ${err.msg}`).join('; ')}`;
                           errorDetails = errorData.detail;
                        } else if (errorData.detail) { errorMsg = errorData.detail; }
                        else { errorMsg = JSON.stringify(errorData); }
                    } catch (jsonError) {
                        const errorText = await response.text();
                        console.error('Upload failed with non-JSON response:', errorText);
                        errorMsg = `Server returned status ${response.status}. Response: ${errorText.substring(0, 200)}`;
                    }
                    const error = new Error(errorMsg);
                    error.status = response.status;
                    error.details = errorDetails;
                    throw error;
                }

                const data = await response.json();
                console.log('Upload successful, job started:', data);
                currentJobId = data.job_id; // Store current job ID

                if (jobStatusCard) jobStatusCard.classList.remove('d-none');
                if (jobStatsCard) jobStatsCard.classList.add('d-none');
                if (downloadDiv) downloadDiv.style.display = 'none';

                if(jobIdEl) jobIdEl.textContent = data.job_id;
                if(statusEl) statusEl.textContent = data.status || 'N/A';
                if(stageEl) stageEl.textContent = stageNames[data.current_stage] || data.current_stage || 'N/A';
                if(progressEl) { progressEl.style.width = `${(data.progress || 0) * 100}%`; progressEl.classList.remove('bg-danger'); }
                if(createdEl) createdEl.textContent = data.created_at ? new Date(data.created_at).toLocaleString() : 'N/A';
                if(updatedEl) updatedEl.textContent = data.updated_at ? new Date(data.updated_at).toLocaleString() : 'N/A';

                startPolling(data.job_id);

            } catch (error) {
                console.error('Upload error caught:', error);
                if (!error.isHandledAuthError) {
                    let alertMessage = `Upload Error: ${error.message}`;
                    if (error.status === 422 && error.details) {
                         const validationErrors = error.details.map(err => `${err.loc.join('.')}: ${err.msg}`).join('\n');
                         alertMessage = `Validation Error:\n${validationErrors}`;
                         console.error("Detailed Validation Errors:", error.details);
                    } else if (error.status) { alertMessage = `Upload Error (Status ${error.status}): ${error.message}`; }
                    alert(alertMessage);
                }
                if(uploadButton) uploadButton.disabled = false;
                if(uploadButton) uploadButton.textContent = 'Upload and Process';
            }
        });
    } else { console.error("Upload form not found!"); }

    if (notifyButton) {
        notifyButton.addEventListener('click', async function() {
            console.log('Notify button clicked.');
            const emailInput = document.getElementById('notificationEmail');
            const email = emailInput ? emailInput.value : null;
            // Use stored currentJobId
            if (!email) { alert('Please enter an email address'); return; }
            if (!currentJobId) { alert('Job ID not found.'); return; }

            console.log(`Requesting notification for Job ID: ${currentJobId} to Email: ${email}`);

            try {
                console.log('Attempting notification request...');
                const response = await fetch(`/api/v1/jobs/${currentJobId}/notify`, { // Uses interceptor
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email })
                });

                console.log('Notification response status:', response.status);
                if (!response.ok) { // Interceptor handles 401
                     let errorMsg = 'Error setting notification';
                     try { const errorData = await response.json(); errorMsg = errorData.detail || errorMsg; } catch (jsonError) {}
                    throw new Error(errorMsg);
                }
                console.log('Notification request successful.');
                alert('Notification set! You will receive an email when processing is complete.');
            } catch (error) {
                 console.error('Notification error:', error);
                 if (!error.isHandledAuthError) {
                     alert(`Error: ${error.message}`);
                 }
            }
        });
    } else { console.error("Notify button not found!"); }

    // --- MODIFICATION: Add event listener for download button ---
    if (downloadButton) {
        downloadButton.addEventListener('click', async function(e) {
            e.preventDefault(); // Prevent default link navigation
            console.log('Download button clicked.');

            if (!currentJobId) {
                alert('Cannot download results: No active Job ID found.');
                return;
            }
            if (!isAuthenticated()) {
                alert('Please log in to download results.');
                handleLogout(); // Ensure user is logged out
                return;
            }

            const downloadUrl = `/api/v1/jobs/${currentJobId}/download`;
            console.log(`Attempting to download results from: ${downloadUrl}`);
            downloadButton.textContent = 'Downloading...';
            downloadButton.disabled = true;

            try {
                // Use intercepted fetch to get the file blob
                const response = await fetch(downloadUrl); // GET request by default

                console.log('Download response status:', response.status);

                if (!response.ok) { // Interceptor handles 401
                    let errorMsg = 'Error downloading file';
                    try {
                        const errorData = await response.json(); // Try parsing error
                        errorMsg = errorData.detail || JSON.stringify(errorData);
                    } catch (jsonError) {
                        const errorText = await response.text(); // Fallback to text
                        errorMsg = `Server returned status ${response.status}. ${errorText.substring(0,100)}`;
                    }
                    throw new Error(errorMsg);
                }

                // Get filename from Content-Disposition header
                const disposition = response.headers.get('content-disposition');
                let filename = `job_${currentJobId}_results.xlsx`; // Default filename
                if (disposition && disposition.indexOf('attachment') !== -1) {
                    const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                    const matches = filenameRegex.exec(disposition);
                    if (matches != null && matches[1]) {
                      filename = matches[1].replace(/['"]/g, '');
                    }
                }
                console.log(`Attempting to save file as: ${filename}`);

                // Get the file data as a Blob
                const blob = await response.blob();

                // Create a temporary link to trigger the download
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = filename; // Use the extracted or default filename
                document.body.appendChild(a);
                a.click(); // Simulate click
                window.URL.revokeObjectURL(url); // Clean up the object URL
                document.body.removeChild(a); // Clean up the link
                console.log('File download triggered.');

            } catch (error) {
                console.error('Download error:', error);
                if (!error.isHandledAuthError) { // Only alert if not handled by interceptor
                    alert(`Download failed: ${error.message}`);
                }
            } finally {
                // Re-enable button
                downloadButton.textContent = 'Download Results';
                downloadButton.disabled = false;
            }
        });
    } else { console.error("Download button/link not found!"); }
    // --- END MODIFICATION ---

    // --- Polling Functions ---
    function startPolling(jobId) {
        stopPolling();
        console.log(`Starting polling for Job ID: ${jobId}`);
        currentJobId = jobId; // Store the job ID being polled
        pollJobStatus(jobId); // Initial poll
        pollingIntervalId = setInterval(() => pollJobStatus(jobId), POLLING_INTERVAL);
    }

    function stopPolling() {
        if (pollingIntervalId) {
            console.log("Stopping polling.");
            clearInterval(pollingIntervalId);
            pollingIntervalId = null;
            // Don't clear currentJobId here, might be needed for download
        }
    }

    async function pollJobStatus(jobId) {
        if (!isAuthenticated()) {
            console.log("Not authenticated, stopping polling.");
            stopPolling();
            return;
        }
        if (jobId !== currentJobId) { // Stop polling if a new job was started
            console.log(`Polling stopped for ${jobId} because a new job (${currentJobId}) was started.`);
            stopPolling();
            return;
        }

        try {
            const response = await fetch(`/api/v1/jobs/${jobId}`); // Uses interceptor

            if (!response.ok) { // Interceptor handles 401
                 let errorMsg = 'Error fetching job status';
                 try { const errorData = await response.json(); errorMsg = errorData.detail || JSON.stringify(errorData); }
                 catch (jsonError) { const errorText = await response.text(); errorMsg = `Server returned status ${response.status}. ${errorText.substring(0,100)}`; }
                 console.error(`Polling error for Job ID ${jobId}: ${errorMsg}. Stopping polling.`);
                 if(statusEl) statusEl.textContent = `Error polling: ${errorMsg}`;
                 if(progressEl) progressEl.classList.add('bg-danger');
                 stopPolling();
                 if(uploadButton) uploadButton.disabled = false;
                 if(uploadButton) uploadButton.textContent = 'Upload and Process';
                 return;
            }

            const data = await response.json();

            if(statusEl) statusEl.textContent = data.status || 'N/A';
            if(stageEl) stageEl.textContent = stageNames[data.current_stage] || data.current_stage || 'N/A';
            if(progressEl) progressEl.style.width = `${(data.progress || 0) * 100}%`;
            if(updatedEl) updatedEl.textContent = data.updated_at ? new Date(data.updated_at).toLocaleString() : 'N/A';
            if (estimatedEl) { estimatedEl.textContent = data.estimated_completion ? new Date(data.estimated_completion).toLocaleString() : 'Calculating...'; }

            if (data.status === 'completed' || data.status === 'failed') {
                console.log(`Job ${jobId} finished with status: ${data.status}`);
                stopPolling();
                if(uploadButton) uploadButton.disabled = false;
                if(uploadButton) uploadButton.textContent = 'Upload and Process';

                if (data.status === 'completed') {
                    if (downloadDiv) downloadDiv.style.display = 'block';
                    // No need to set href anymore, button click handles it
                    if(progressEl) progressEl.classList.remove('bg-danger');
                    fetchJobStats(jobId);
                } else {
                     const errorMsg = data.error_message || 'Processing failed.';
                     if(statusEl) statusEl.textContent = `Failed: ${errorMsg.substring(0, 100)}${errorMsg.length > 100 ? '...' : ''}`;
                     if(progressEl) progressEl.classList.add('bg-danger');
                     console.error(`Job ${jobId} Failed: ${errorMsg}`);
                     alert(`Job Failed: ${errorMsg}`);
                }
                return;
            }
        } catch (error) {
            console.error(`Error during pollJobStatus execution for ${jobId}:`, error);
             if (!error.isHandledAuthError) {
                if(statusEl) statusEl.textContent = `Polling Error: ${error.message}`;
                console.warn(`Retrying polling for ${jobId} in ${POLLING_RETRY_INTERVAL/1000} seconds after error.`);
                stopPolling();
                setTimeout(() => startPolling(jobId), POLLING_RETRY_INTERVAL);
            }
        }
    }

    async function fetchJobStats(jobId) {
         console.log(`Fetching stats for Job ID: ${jobId}`);
        try {
            const response = await fetch(`/api/v1/jobs/${jobId}/stats`); // Uses interceptor

            console.log(`Stats response status for Job ID ${jobId}:`, response.status);
            if (!response.ok) { // Interceptor handles 401
                let errorMsg = 'Error fetching job statistics';
                 try { const errorData = await response.json(); errorMsg = errorData.detail || JSON.stringify(errorData); }
                 catch (jsonError) { const errorText = await response.text(); errorMsg = `Server returned status ${response.status}. ${errorText.substring(0,100)}`; }
                throw new Error(errorMsg);
            }

            const stats = await response.json();
            console.log(`Received job stats for ${jobId}:`, stats);

            if (jobStatsCard) jobStatsCard.classList.remove('d-none');
            if(vendorsProcessedEl) vendorsProcessedEl.textContent = stats.vendors_processed ?? 'N/A';
            if(uniqueVendorsEl) uniqueVendorsEl.textContent = stats.unique_vendors ?? 'N/A';
            if(apiCallsEl) apiCallsEl.textContent = stats.api_calls ?? 'N/A';
            if(tokensUsedEl) tokensUsedEl.textContent = stats.tokens_used ?? 'N/A';
            if(tavilySearchesEl) tavilySearchesEl.textContent = stats.tavily_searches ?? 'N/A';
            if(processingTimeEl) processingTimeEl.textContent = stats.processing_time != null ? stats.processing_time.toFixed(2) : 'N/A';

        } catch (error) {
            console.error(`Error fetching job statistics for ${jobId}:`, error);
             if (!error.isHandledAuthError) {
                 if (jobStatsCard) jobStatsCard.classList.add('d-none');
                 alert(`Could not load job statistics: ${error.message}`);
             }
        }
    }

    // --- Initial Load ---
    updateAuthUI();

    const urlParams = new URLSearchParams(window.location.search);
    const jobIdFromUrl = urlParams.get('job_id');
    if (jobIdFromUrl && isAuthenticated()) {
        console.log(`Found Job ID in URL: ${jobIdFromUrl}. Starting polling.`);
        if (jobStatusCard) jobStatusCard.classList.remove('d-none');
        if(jobIdEl) jobIdEl.textContent = jobIdFromUrl;
        startPolling(jobIdFromUrl);
    } else if (jobIdFromUrl && !isAuthenticated()) {
         console.log(`Found Job ID in URL: ${jobIdFromUrl}, but user not authenticated.`);
    }
});