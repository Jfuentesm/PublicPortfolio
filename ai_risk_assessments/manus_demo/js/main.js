// Main JavaScript for AIRisk Demo

// DOM Ready Event
document.addEventListener('DOMContentLoaded', function() {
    // Mobile Menu Toggle
    const mobileToggle = document.querySelector('.mobile-toggle');
    const navMenu = document.querySelector('nav ul');
    
    if (mobileToggle && navMenu) {
        mobileToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }
    
    // User Dropdown Menu
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
    
    // Tabs Functionality
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
                
                document.getElementById(tabId).classList.add('active');
            });
        });
    }
    
    // Modal Functionality
    const modalTriggers = document.querySelectorAll('[data-modal]');
    
    if (modalTriggers.length > 0) {
        modalTriggers.forEach(trigger => {
            trigger.addEventListener('click', function() {
                const modalId = this.getAttribute('data-modal');
                const modal = document.getElementById(modalId);
                
                if (modal) {
                    modal.classList.add('active');
                }
            });
        });
        
        // Close modal when clicking on backdrop or close button
        const modalBackdrops = document.querySelectorAll('.modal-backdrop');
        const modalCloseButtons = document.querySelectorAll('.modal-close');
        
        modalBackdrops.forEach(backdrop => {
            backdrop.addEventListener('click', function(e) {
                if (e.target === this) {
                    this.classList.remove('active');
                }
            });
        });
        
        modalCloseButtons.forEach(button => {
            button.addEventListener('click', function() {
                const modal = this.closest('.modal-backdrop');
                modal.classList.remove('active');
            });
        });
    }
    
    // Initialize any charts if Chart.js is available
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
    
    // Initialize any demo-specific functionality
    initializeDemo();
});

// Demo-specific functionality
function initializeDemo() {
    // Simulate login functionality
    const loginForm = document.getElementById('login-form');
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            // Simple validation
            if (email && password) {
                // Simulate successful login
                window.location.href = 'dashboard.html';
            } else {
                // Show error
                const errorAlert = document.createElement('div');
                errorAlert.className = 'alert alert-danger';
                errorAlert.textContent = 'Please enter both email and password.';
                
                const existingAlert = loginForm.querySelector('.alert');
                if (existingAlert) {
                    existingAlert.remove();
                }
                
                loginForm.prepend(errorAlert);
            }
        });
    }
    
    // Simulate risk identification AI suggestions
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
                                <button class="btn btn-sm">Accept</button>
                                <button class="btn btn-secondary btn-sm">Edit</button>
                                <button class="btn btn-danger btn-sm">Reject</button>
                            </div>
                        `;
                        
                        suggestedRisksContainer.appendChild(riskCard);
                    });
                    
                    // Re-enable button
                    this.disabled = false;
                    this.textContent = 'Suggest Risks';
                    
                    // Show success message
                    const alertContainer = document.getElementById('alert-container');
                    if (alertContainer) {
                        alertContainer.innerHTML = `
                            <div class="alert alert-success">
                                AI has suggested 5 risks based on your company profile. Review and accept them to add to your risk register.
                            </div>
                        `;
                    }
                }
            }, 2000);
        });
    }
    
    // Simulate risk assessment
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
                }
                
                // Re-enable button
                this.disabled = false;
                this.textContent = 'Start Assessment';
            }, 2000);
        });
    }
    
    // Simulate mitigation plan generation
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
                                <button class="btn btn-sm">Edit</button>
                                <button class="btn btn-danger btn-sm">Delete</button>
                            </td>
                        `;
                        
                        tbody.appendChild(tr);
                    });
                    
                    mitigationPlanContainer.appendChild(table);
                    
                    // Show success message
                    const alertContainer = document.getElementById('alert-container');
                    if (alertContainer) {
                        alertContainer.innerHTML = `
                            <div class="alert alert-success">
                                AI has generated a mitigation plan with 4 tasks. Assign owners and track progress.
                            </div>
                        `;
                    }
                    
                    // Show mitigation plan container
                    mitigationPlanContainer.style.display = 'block';
                }
                
                // Re-enable button
                this.disabled = false;
                this.textContent = 'Generate Mitigation Plan';
            }, 2000);
        });
    }
}

// Chart initialization function
function initializeCharts() {
    // Risk by Category Chart
    const riskCategoryChart = document.getElementById('risk-category-chart');
    
    if (riskCategoryChart) {
        new Chart(riskCategoryChart, {
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
    
    // Risk Trend Chart
    const riskTrendChart = document.getElementById('risk-trend-chart');
    
    if (riskTrendChart) {
        new Chart(riskTrendChart, {
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
    
    // Mitigation Progress Chart
    const mitigationProgressChart = document.getElementById('mitigation-progress-chart');
    
    if (mitigationProgressChart) {
        new Chart(mitigationProgressChart, {
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
