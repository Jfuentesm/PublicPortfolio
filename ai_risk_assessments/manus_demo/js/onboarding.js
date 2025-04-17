// Onboarding flow for AIRisk Demo

document.addEventListener('DOMContentLoaded', function() {
    setupOnboarding();
});

function setupOnboarding() {
    // Initialize onboarding steps
    const currentStep = getCurrentStep();
    showCurrentStep(currentStep);
    
    // Next button functionality
    const nextButtons = document.querySelectorAll('.next-step');
    nextButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const currentStep = getCurrentStep();
            const nextStep = currentStep + 1;
            
            // Validate current step before proceeding
            if (validateStep(currentStep)) {
                saveStepData(currentStep);
                setCurrentStep(nextStep);
                showCurrentStep(nextStep);
            }
        });
    });
    
    // Previous button functionality
    const prevButtons = document.querySelectorAll('.prev-step');
    prevButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const currentStep = getCurrentStep();
            const prevStep = currentStep - 1;
            
            if (prevStep >= 1) {
                setCurrentStep(prevStep);
                showCurrentStep(prevStep);
            }
        });
    });
    
    // Skip button functionality
    const skipButtons = document.querySelectorAll('.skip-step');
    skipButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const currentStep = getCurrentStep();
            const nextStep = currentStep + 1;
            
            setCurrentStep(nextStep);
            showCurrentStep(nextStep);
        });
    });
    
    // Complete onboarding button
    const completeButton = document.querySelector('.complete-onboarding');
    if (completeButton) {
        completeButton.addEventListener('click', function(e) {
            e.preventDefault();
            const currentStep = getCurrentStep();
            
            if (validateStep(currentStep)) {
                saveStepData(currentStep);
                
                // Show loading state
                this.disabled = true;
                this.textContent = 'Setting up your account...';
                
                // Simulate API call
                setTimeout(() => {
                    // Redirect to dashboard
                    window.location.href = 'dashboard.html';
                }, 2000);
            }
        });
    }
    
    // Industry selection
    const industrySelect = document.getElementById('industry');
    if (industrySelect) {
        industrySelect.addEventListener('change', function() {
            // Show industry-specific fields based on selection
            const selectedIndustry = this.value;
            const techFields = document.getElementById('tech-specific-fields');
            const financeFields = document.getElementById('finance-specific-fields');
            const healthcareFields = document.getElementById('healthcare-specific-fields');
            
            // Hide all industry-specific fields
            [techFields, financeFields, healthcareFields].forEach(field => {
                if (field) field.style.display = 'none';
            });
            
            // Show selected industry fields
            if (selectedIndustry === 'technology' && techFields) {
                techFields.style.display = 'block';
            } else if (selectedIndustry === 'finance' && financeFields) {
                financeFields.style.display = 'block';
            } else if (selectedIndustry === 'healthcare' && healthcareFields) {
                healthcareFields.style.display = 'block';
            }
        });
    }
    
    // Add department button
    const addDeptButton = document.getElementById('add-department');
    const departmentsContainer = document.getElementById('departments-container');
    
    if (addDeptButton && departmentsContainer) {
        addDeptButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            const deptCount = departmentsContainer.querySelectorAll('.department-row').length;
            const newDeptRow = document.createElement('div');
            newDeptRow.className = 'department-row form-group';
            newDeptRow.innerHTML = `
                <div style="display: flex; gap: 10px;">
                    <input type="text" class="form-control" placeholder="Department Name" style="flex: 2;">
                    <input type="text" class="form-control" placeholder="Department Head" style="flex: 2;">
                    <button class="btn btn-danger btn-sm remove-dept" style="flex: 0 0 auto;">Remove</button>
                </div>
            `;
            
            departmentsContainer.appendChild(newDeptRow);
            
            // Add event listener to remove button
            const removeButton = newDeptRow.querySelector('.remove-dept');
            removeButton.addEventListener('click', function(e) {
                e.preventDefault();
                newDeptRow.remove();
            });
        });
    }
    
    // Add user button
    const addUserButton = document.getElementById('add-user');
    const usersContainer = document.getElementById('users-container');
    
    if (addUserButton && usersContainer) {
        addUserButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            const userCount = usersContainer.querySelectorAll('.user-row').length;
            const newUserRow = document.createElement('div');
            newUserRow.className = 'user-row form-group';
            newUserRow.innerHTML = `
                <div style="display: flex; gap: 10px;">
                    <input type="text" class="form-control" placeholder="Full Name" style="flex: 2;">
                    <input type="email" class="form-control" placeholder="Email" style="flex: 2;">
                    <select class="form-select" style="flex: 1;">
                        <option value="">Role</option>
                        <option value="admin">Admin</option>
                        <option value="risk-owner">Risk Owner</option>
                        <option value="viewer">Viewer</option>
                    </select>
                    <button class="btn btn-danger btn-sm remove-user" style="flex: 0 0 auto;">Remove</button>
                </div>
            `;
            
            usersContainer.appendChild(newUserRow);
            
            // Add event listener to remove button
            const removeButton = newUserRow.querySelector('.remove-user');
            removeButton.addEventListener('click', function(e) {
                e.preventDefault();
                newUserRow.remove();
            });
        });
    }
    
    // Rubric customization
    const customizeRubricButton = document.getElementById('customize-rubric');
    const rubricCustomization = document.getElementById('rubric-customization');
    
    if (customizeRubricButton && rubricCustomization) {
        customizeRubricButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (rubricCustomization.style.display === 'none' || !rubricCustomization.style.display) {
                rubricCustomization.style.display = 'block';
                this.textContent = 'Hide Customization';
            } else {
                rubricCustomization.style.display = 'none';
                this.textContent = 'Customize Rubric';
            }
        });
    }
}

// Helper functions for onboarding
function getCurrentStep() {
    // Get current step from URL or default to 1
    const urlParams = new URLSearchParams(window.location.search);
    const step = parseInt(urlParams.get('step')) || 1;
    return step;
}

function setCurrentStep(step) {
    // Update URL with current step
    const url = new URL(window.location);
    url.searchParams.set('step', step);
    window.history.pushState({}, '', url);
}

function showCurrentStep(step) {
    // Hide all steps
    const steps = document.querySelectorAll('.onboarding-step');
    steps.forEach(s => s.style.display = 'none');
    
    // Show current step
    const currentStep = document.getElementById(`step-${step}`);
    if (currentStep) {
        currentStep.style.display = 'block';
    } else {
        // If step doesn't exist, default to step 1
        const firstStep = document.getElementById('step-1');
        if (firstStep) {
            firstStep.style.display = 'block';
            setCurrentStep(1);
        }
    }
    
    // Update progress indicator
    updateProgressIndicator(step, steps.length);
}

function updateProgressIndicator(currentStep, totalSteps) {
    const progressBar = document.querySelector('.progress-bar');
    const progressText = document.querySelector('.progress-text');
    
    if (progressBar) {
        const progressPercentage = (currentStep / totalSteps) * 100;
        progressBar.style.width = `${progressPercentage}%`;
    }
    
    if (progressText) {
        progressText.textContent = `Step ${currentStep} of ${totalSteps}`;
    }
}

function validateStep(step) {
    // Validate required fields for each step
    switch(step) {
        case 1: // Company Profile
            const companyName = document.getElementById('company-name');
            const industry = document.getElementById('industry');
            
            if (!companyName || !companyName.value.trim()) {
                showStepError(step, 'Please enter your company name.');
                return false;
            }
            
            if (!industry || !industry.value) {
                showStepError(step, 'Please select your industry.');
                return false;
            }
            
            return true;
            
        case 2: // Organization Structure
            // For demo purposes, we'll allow this step to be skipped
            return true;
            
        case 3: // Assessment Rubric
            // For demo purposes, we'll allow this step to be skipped
            return true;
            
        case 4: // Confirmation
            // No validation needed for confirmation step
            return true;
            
        default:
            return true;
    }
}

function showStepError(step, message) {
    const errorContainer = document.querySelector(`#step-${step} .alert-container`);
    
    if (errorContainer) {
        errorContainer.innerHTML = `
            <div class="alert alert-danger">
                ${message}
            </div>
        `;
    }
}

function saveStepData(step) {
    // In a real application, this would save data to the server
    // For the demo, we'll just simulate saving
    console.log(`Saving data for step ${step}`);
    
    // Clear any error messages
    const errorContainer = document.querySelector(`#step-${step} .alert-container`);
    if (errorContainer) {
        errorContainer.innerHTML = '';
    }
}
