// Chart.js initialization for the demo
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts if they exist on the page
    initializeRiskCategoryChart();
    initializeRiskTrendChart();
    initializeMitigationProgressChart();
    
    // Initialize interactive elements
    setupLoginAuthentication();
    setupRiskIdentification();
    setupRiskAssessment();
    setupMitigationPlanning();
    setupTaskManagement();
});

// Risk Category Chart
function initializeRiskCategoryChart() {
    const chartElement = document.getElementById('risk-category-chart');
    if (!chartElement) return;
    
    if (typeof Chart !== 'undefined') {
        new Chart(chartElement, {
            type: 'doughnut',
            data: {
                labels: ['Cybersecurity', 'Operational', 'Financial', 'Strategic', 'Compliance', 'Reputational'],
                datasets: [{
                    data: [12, 8, 6, 5, 4, 3],
                    backgroundColor: [
                        '#0050A0',
                        '#17a2b8',
                        '#28a745',
                        '#ffc107',
                        '#fd7e14',
                        '#dc3545'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    }
}

// Risk Trend Chart
function initializeRiskTrendChart() {
    const chartElement = document.getElementById('risk-trend-chart');
    if (!chartElement) return;
    
    if (typeof Chart !== 'undefined') {
        new Chart(chartElement, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'High Risks',
                    data: [12, 10, 11, 8, 7, 5],
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    tension: 0.3
                }, {
                    label: 'Medium Risks',
                    data: [8, 9, 10, 12, 11, 10],
                    borderColor: '#ffc107',
                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                    tension: 0.3
                }, {
                    label: 'Low Risks',
                    data: [5, 6, 8, 9, 10, 12],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

// Mitigation Progress Chart
function initializeMitigationProgressChart() {
    const chartElement = document.getElementById('mitigation-progress-chart');
    if (!chartElement) return;
    
    if (typeof Chart !== 'undefined') {
        new Chart(chartElement, {
            type: 'bar',
            data: {
                labels: ['Cybersecurity', 'Operational', 'Financial', 'Strategic', 'Compliance'],
                datasets: [{
                    label: 'Completed',
                    data: [8, 5, 4, 2, 3],
                    backgroundColor: '#28a745'
                }, {
                    label: 'In Progress',
                    data: [3, 2, 1, 2, 1],
                    backgroundColor: '#ffc107'
                }, {
                    label: 'Not Started',
                    data: [1, 1, 1, 1, 0],
                    backgroundColor: '#dc3545'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

// Login and Authentication
function setupLoginAuthentication() {
    // Login form handling
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            // Simple validation
            if (!email || !password) {
                showAlert('alert-container', 'Please enter both email and password.', 'danger');
                return;
            }
            
            // Simulate API call with loading state
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.textContent = 'Signing in...';
            
            setTimeout(() => {
                // Simulate successful login
                window.location.href = 'dashboard.html';
            }, 1500);
        });
    }
    
    // Registration form handling
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const name = document.getElementById('name')?.value;
            const company = document.getElementById('company')?.value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm-password')?.value;
            const terms = document.getElementById('terms')?.checked;
            
            // Simple validation
            if (!email || !password) {
                showAlert('alert-container', 'Please fill in all required fields.', 'danger');
                return;
            }
            
            if (password !== confirmPassword) {
                showAlert('alert-container', 'Passwords do not match.', 'danger');
                return;
            }
            
            if (terms !== undefined && !terms) {
                showAlert('alert-container', 'You must agree to the Terms of Service and Privacy Policy.', 'danger');
                return;
            }
            
            // Simulate API call with loading state
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.textContent = 'Creating account...';
            
            setTimeout(() => {
                // Simulate successful registration
                window.location.href = 'onboarding.html';
            }, 1500);
        });
    }
    
    // User menu dropdown
    const userMenu = document.querySelector('.user-menu');
    const dropdownMenu = document.querySelector('.dropdown-menu');
    
    if (userMenu && dropdownMenu) {
        userMenu.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdownMenu.classList.toggle('active');
        });
        
        document.addEventListener('click', function() {
            if (dropdownMenu.classList.contains('active')) {
                dropdownMenu.classList.remove('active');
            }
        });
    }
}

// Risk Identification
function setupRiskIdentification() {
    // AI Risk Suggestion
    const suggestRisksBtn = document.getElementById('suggest-risks-btn');
    
    if (suggestRisksBtn) {
        suggestRisksBtn.addEventListener('click', function() {
            this.disabled = true;
            this.textContent = 'Generating suggestions...';
            
            // Simulate API call delay
            setTimeout(() => {
                const suggestedRisksContainer = document.getElementById('suggested-risks');
                
                if (suggestedRisksContainer) {
                    // Predefined AI-suggested risks
                    const suggestedRisks = [
                        {
                            title: 'Data Breach Risk',
                            category: 'Cybersecurity',
                            description: 'Risk of unauthorized access to sensitive customer data due to inadequate security controls.',
                            source: 'AI'
                        },
                        {
                            title: 'Supply Chain Disruption',
                            category: 'Operational',
                            description: 'Risk of business interruption due to key supplier failure or logistics issues.',
                            source: 'Library'
                        },
                        {
                            title: 'Regulatory Non-Compliance',
                            category: 'Compliance',
                            description: 'Risk of penalties due to failure to comply with industry regulations.',
                            source: 'AI'
                        },
                        {
                            title: 'Key Personnel Departure',
                            category: 'Human Resources',
                            description: 'Risk of knowledge loss and operational disruption due to departure of key employees.',
                            source: 'Library'
                        },
                        {
                            title: 'Market Share Decline',
                            category: 'Strategic',
                            description: 'Risk of losing market position due to new competitors or changing customer preferences.',
                            source: 'AI'
                        }
                    ];
                    
                    // Clear existing content
                    suggestedRisksContainer.innerHTML = '';
                    
                    // Add suggested risks to the container
                    suggestedRisks.forEach(risk => {
                        const riskCard = document.createElement('div');
                        riskCard.className = 'card mb-20';
                        
                        riskCard.innerHTML = `
                            <div class="card-header">
                                <h3>${risk.title}</h3>
                                <span class="badge ${risk.source === 'AI' ? 'badge-primary' : 'badge-info'}">${risk.source}</span>
                            </div>
                            <div class="card-body">
                                <p><strong>Category:</strong> ${risk.category}</p>
                                <p>${risk.description}</p>
                            </div>
                            <div class="card-footer">
                                <button class="btn btn-sm accept-risk">Accept</button>
                                <button class="btn btn-secondary btn-sm edit-risk">Edit</button>
                                <button class="btn btn-danger btn-sm reject-risk">Reject</button>
                            </div>
                        `;
                        
                        suggestedRisksContainer.appendChild(riskCard);
                    });
                    
                    // Add event listeners to the buttons
                    const acceptButtons = document.querySelectorAll('.accept-risk');
                    const editButtons = document.querySelectorAll('.edit-risk');
                    const rejectButtons = document.querySelectorAll('.reject-risk');
                    
                    acceptButtons.forEach(button => {
                        button.addEventListener('click', function() {
                            const card = this.closest('.card');
                            const title = card.querySelector('h3').textContent;
                            showAlert('alert-container', `Risk "${title}" has been added to your risk register.`, 'success');
                            card.style.opacity = '0.5';
                            this.disabled = true;
                            this.textContent = 'Accepted';
                        });
                    });
                    
                    editButtons.forEach(button => {
                        button.addEventListener('click', function() {
                            const card = this.closest('.card');
                            const title = card.querySelector('h3').textContent;
                            showAlert('alert-container', `Editing risk "${title}" - feature coming soon.`, 'info');
                        });
                    });
                    
                    rejectButtons.forEach(button => {
                        button.addEventListener('click', function() {
                            const card = this.closest('.card');
                            card.style.display = 'none';
                        });
                    });
                    
                    // Re-enable button
                    this.disabled = false;
                    this.textContent = 'Suggest Risks';
                    
                    // Show success message
                    showAlert('alert-container', 'AI has suggested 5 risks based on your company profile. Review and accept them to add to your risk register.', 'success');
                }
            }, 2000);
        });
    }
    
    // Add Risk Form
    const addRiskForm = document.getElementById('add-risk-form');
    
    if (addRiskForm) {
        addRiskForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const title = document.getElementById('risk-title').value;
            const category = document.getElementById('risk-category').value;
            const description = document.getElementById('risk-description').value;
            
            // Simple validation
            if (!title || !category || !description) {
                showAlert('alert-container', 'Please fill in all required fields.', 'danger');
                return;
            }
            
            // Simulate successful addition
            showAlert('alert-container', `Risk "${title}" has been added to your risk register.`, 'success');
            
            // Clear form
            this.reset();
        });
    }
    
    // Risk Library Tabs
    const tabs = document.querySelectorAll('.tab');
    
    if (tabs.length > 0) {
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                // Remove active class from all tabs
                tabs.forEach(t => t.classList.remove('active'));
                
                // Add active class to clicked tab
                this.classList.add('active');
                
                // Show corresponding tab content
                const tabId = this.getAttribute('data-tab');
                const tabContents = document.querySelectorAll('.tab-content');
                
                tabContents.forEach(content => {
                    content.classList.remove('active');
                });
                
                document.getElementById(tabId)?.classList.add('active');
            });
        });
    }
    
    // Add to Register buttons in Risk Library
    const addToRegisterButtons = document.querySelectorAll('.table .btn');
    
    if (addToRegisterButtons.length > 0) {
        addToRegisterButtons.forEach(button => {
            button.addEventListener('click', function() {
                const row = this.closest('tr');
                const riskTitle = row.querySelector('td:first-child').textContent;
                
                showAlert('alert-container', `Risk "${riskTitle}" has been added to your risk register.`, 'success');
                
                // Disable button after adding
                this.disabled = true;
                this.textContent = 'Added';
            });
        });
    }
}

// Risk Assessment
function setupRiskAssessment() {
    // Start Assessment Button
    const assessRiskBtn = document.getElementById('assess-risk-btn');
    
    if (assessRiskBtn) {
        assessRiskBtn.addEventListener('click', function() {
            this.disabled = true;
            this.textContent = 'Assessing risks...';
            
            // Simulate API call delay
            setTimeout(() => {
                const assessmentResultsContainer = document.getElementById('assessment-results');
                
                if (assessmentResultsContainer) {
                    // Show assessment results
                    assessmentResultsContainer.style.display = 'block';
                    
                    // Scroll to results
                    assessmentResultsContainer.scrollIntoView({ behavior: 'smooth' });
                    
                    // Show success message
                    showAlert('alert-container', 'Assessment completed successfully. Review the results below.', 'success');
                }
                
                // Re-enable button
                this.disabled = false;
                this.textContent = 'Start Assessment';
            }, 2500);
        });
    }
    
    // Risk Detail Modal
    const reviewButtons = document.querySelectorAll('[data-modal="risk-detail-modal"]');
    const riskDetailModal = document.getElementById('risk-detail-modal');
    
    if (reviewButtons.length > 0 && riskDetailModal) {
        reviewButtons.forEach(button => {
            button.addEventListener('click', function() {
                riskDetailModal.classList.add('active');
            });
        });
        
        // Close modal when clicking on backdrop
        riskDetailModal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
            }
        });
        
        // Close modal when clicking on close button
        const closeButton = riskDetailModal.querySelector('.modal-close');
        if (closeButton) {
            closeButton.addEventListener('click', function() {
                riskDetailModal.classList.remove('active');
            });
        }
        
        // Save Assessment button
        const saveButton = riskDetailModal.querySelector('.modal-footer .btn:last-child');
        if (saveButton) {
            saveButton.addEventListener('click', function() {
                showAlert('alert-container', 'Risk assessment has been updated.', 'success');
                riskDetailModal.classList.remove('active');
            });
        }
    }
}

// Mitigation Planning
function setupMitigationPlanning() {
    // Generate Mitigation Plan Button
    const generatePlanBtn = document.getElementById('generate-plan-btn');
    
    if (generatePlanBtn) {
        generatePlanBtn.addEventListener('click', function() {
            this.disabled = true;
            this.textContent = 'Generating plan...';
            
            // Simulate API call delay
            setTimeout(() => {
                const mitigationPlanContainer = document.getElementById('mitigation-plan');
                
                if (mitigationPlanContainer) {
                    // Predefined mitigation tasks
                    const mitigationTasks = [
                        {
                            title: 'Implement Multi-Factor Authentication',
                            owner: 'IT Security Manager',
                            dueDate: '2025-05-15',
                            status: 'Not Started'
                        },
                        {
                            title: 'Conduct Security Awareness Training',
                            owner: 'HR Director',
                            dueDate: '2025-05-30',
                            status: 'Not Started'
                        },
                        {
                            title: 'Update Data Protection Policy',
                            owner: 'Compliance Officer',
                            dueDate: '2025-06-10',
                            status: 'Not Started'
                        },
                        {
                            title: 'Perform Penetration Testing',
                            owner: 'IT Security Manager',
                            dueDate: '2025-06-30',
                            status: 'Not Started'
                        }
                    ];
                    
                    // Clear existing content
                    mitigationPlanContainer.innerHTML = '';
                    
                    // Create table for mitigation tasks
                    const table = document.createElement('table');
                    
                    // Add table header
                    table.innerHTML = `
                        <thead>
                            <tr>
                                <th>Task</th>
                                <th>Owner</th>
                                <th>Due Date</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    `;
                    
                    // Add tasks to table
                    const tbody = table.querySelector('tbody');
                    
                    mitigationTasks.forEach(task => {
                        const tr = document.createElement('tr');
                        
                        tr.innerHTML = `
                            <td>${task.title}</td>
                            <td>${task.owner}</td>
                            <td>${task.dueDate}</td>
                            <td><span class="badge badge-warning">${task.status}</span></td>
                            <td>
                                <button class="btn btn-sm edit-task">Edit</button>
                                <button class="btn btn-danger btn-sm delete-task">Delete</button>
                            </td>
                        `;
                        
                        tbody.appendChild(tr);
                    });
                    
                    mitigationPlanContainer.appendChild(table);
                    
                    // Add event listeners to the buttons
                    const editButtons = document.querySelectorAll('.edit-task');
                    const deleteButtons = document.querySelectorAll('.delete-task');
                    
                    editButtons.forEach(button => {
                        button.addEventListener('click', function() {
                            const row = this.closest('tr');
                            const taskTitle = row.querySelector('td:first-child').textContent;
                            showAlert('alert-container', `Editing task "${taskTitle}" - feature coming soon.`, 'info');
                        });
                    });
                    
                    deleteButtons.forEach(button => {
                        button.addEventListener('click', function() {
                            const row = this.closest('tr');
                            row.style.display = 'none';
                        });
                    });
                    
                    // Show success message
                    showAlert('alert-container', 'AI has generated a mitigation plan with 4 tasks. Assign owners and track progress.', 'success');
                    
                    // Show mitigation plan container
                    mitigationPlanContainer.style.display = 'block';
                }
                
                // Re-enable button
                this.disabled = false;
                this.textContent = 'Generate Mitigation Plan';
            }, 2000);
        });
    }
    
    // Add Task Form
    const addTaskForm = document.getElementById('add-task-form');
    
    if (addTaskForm) {
        addTaskForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const title = document.getElementById('task-title').value;
            const description = document.getElementById('task-description').value;
            const owner = document.getElementById('task-owner').value;
            const dueDate = document.getElementById('due-date').value;
            
            // Simple validation
            if (!title || !owner || !dueDate) {
                showAlert('alert-container', 'Please fill in all required fields.', 'danger');
                return;
            }
            
            // Simulate successful addition
            showAlert('alert-container', `Task "${title}" has been added to the mitigation plan.`, 'success');
            
            // Clear form
            this.reset();
        });
    }
}

// Task Management
function setupTaskManagement() {
    // Task Detail Modal
    const updateButtons = document.querySelectorAll('[data-modal="task-detail-modal"]');
    const taskDetailModal = document.getElementById('task-detail-modal');
    
    if (updateButtons.length > 0 && taskDetailModal) {
        updateButtons.forEach(button => {
            button.addEventListener('click', function() {
                taskDetailModal.classList.add('active');
            });
        });
        
        // Close modal when clicking on backdrop
        taskDetailModal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
            }
        });
        
        // Close modal when clicking on close button
        const closeButton = taskDetailModal.querySelector('.modal-close');
        if (closeButton) {
            closeButton.addEventListener('click', function() {
                taskDetailModal.classList.remove('active');
            });
        }
        
        // Save Update button
        const saveButton = taskDetailModal.querySelector('.modal-footer .btn:last-child');
        if (saveButton) {
            saveButton.addEventListener('click', function() {
                showAlert('alert-container', 'Task update has been saved.', 'success');
                taskDetailModal.classList.remove('active');
                
                // Update the task status in the table
                const statusSelect = document.getElementById('task-status');
                if (statusSelect) {
                    const selectedStatus = statusSelect.options[statusSelect.selectedIndex].text;
                    const taskRow = document.querySelector('tr:first-child');
                    if (taskRow) {
                        const statusCell = taskRow.querySelector('td:nth-child(4)');
                        if (statusCell) {
                            let badgeClass = 'badge-warning';
                            if (selectedStatus === 'Completed') {
                                badgeClass = 'badge-success';
                            } else if (selectedStatus === 'Blocked') {
                                badgeClass = 'badge-danger';
                            }
                            
                            statusCell.innerHTML = `<span class="badge ${badgeClass}">${selectedStatus}</span>`;
                        }
                    }
                }
            });
        }
    }
    
    // Task Filters
    const statusFilter = document.getElementById('status-filter');
    const riskFilter = document.getElementById('risk-filter');
    const dueDateFilter = document.getElementById('due-date-filter');
    
    const filters = [statusFilter, riskFilter, dueDateFilter];
    
    filters.forEach(filter => {
        if (filter) {
            filter.addEventListener('change', function() {
                // In a real application, this would filter the tasks
                // For the demo, we'll just show a message
                showAlert('alert-container', 'Filters applied. This would filter the task list in a real application.', 'info');
            });
        }
    });
}

// Helper function to show alerts
function showAlert(containerId, message, type) {
    const alertContainer = document.getElementById(containerId);
    if (!alertContainer) return;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    // Clear existing alerts
    alertContainer.innerHTML = '';
    alertContainer.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.style.opacity = '0';
        setTimeout(() => {
            alertDiv.remove();
        }, 300);
    }, 5000);
}
