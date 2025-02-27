// static/js/context_manager.js

document.addEventListener('DOMContentLoaded', function() {
    // Function to update context display without reloading page
    function updateContextDisplay(contextData) {
        const tenantDisplay = document.getElementById('currentTenant');
        const assessmentDisplay = document.getElementById('currentAssessment');
        const iroDisplay = document.getElementById('currentIRO');
        
        if (tenantDisplay && contextData.tenant) {
            tenantDisplay.textContent = contextData.tenant.tenant_name;
            tenantDisplay.parentElement.classList.remove('text-muted');
        }
        
        if (assessmentDisplay) {
            if (contextData.assessment) {
                assessmentDisplay.textContent = contextData.assessment.name;
                assessmentDisplay.parentElement.classList.remove('text-muted');
            } else {
                assessmentDisplay.textContent = 'No assessment selected';
                assessmentDisplay.parentElement.classList.add('text-muted');
            }
        }
        
        if (iroDisplay) {
            if (contextData.iro) {
                iroDisplay.textContent = contextData.iro.title;
                iroDisplay.parentElement.classList.remove('text-muted');
                
                const iroBadge = document.getElementById('iroBadge');
                if (iroBadge) {
                    iroBadge.textContent = contextData.iro.type;
                    // Set badge color based on type
                    iroBadge.classList.remove('bg-danger', 'bg-success', 'bg-primary');
                    if (contextData.iro.type === 'Risk') {
                        iroBadge.classList.add('bg-danger');
                    } else if (contextData.iro.type === 'Opportunity') {
                        iroBadge.classList.add('bg-success');
                    } else {
                        iroBadge.classList.add('bg-primary');
                    }
                }
            } else {
                iroDisplay.textContent = 'No IRO selected';
                iroDisplay.parentElement.classList.add('text-muted');
            }
        }
    }
    
    // Handle context selection via Ajax
    const contextLinks = document.querySelectorAll('[data-context-link]');
    contextLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const url = this.getAttribute('href');
            
            fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateContextDisplay(data.context);
                    
                    // Close any open modals
                    const openModals = document.querySelectorAll('.modal.show');
                    openModals.forEach(modal => {
                        const modalInstance = bootstrap.Modal.getInstance(modal);
                        if (modalInstance) {
                            modalInstance.hide();
                        }
                    });
                    
                    // Optionally reload content sections
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    }
                }
            })
            .catch(error => console.error('Error updating context:', error));
        });
    });
});