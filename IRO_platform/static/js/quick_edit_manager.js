/**
 * Quick Edit Manager JavaScript Module
 * 
 * This module handles the quick-edit Handsontable functionality for priority IROs
 * on the dashboard.
 */

class QuickEditManager {
    constructor(container, data, saveUrl) {
        this.container = container;
        
        // Additional validation for data
        try {
            if (typeof data === 'string') {
                try {
                    // Try to parse if it's a string
                    this.data = JSON.parse(data);
                } catch (err) {
                    console.error("[QuickEditManager] Failed to parse data string:", err);
                    this.data = [];
                }
            } else {
                this.data = data || [];
            }
            
            if (!Array.isArray(this.data)) {
                console.error("[QuickEditManager] Data is not an array after processing:", this.data);
                this.data = [];
            }
        } catch (e) {
            console.error("[QuickEditManager] Error processing initial data:", e);
            this.data = [];
        }
        
        this.saveUrl = saveUrl;
        this.hot = null;
        this.originalData = JSON.parse(JSON.stringify(this.data)); // Deep copy for tracking changes
        this.hasChanges = false;
        this.saveButton = document.getElementById('save-priority-iros');
        
        this.init();
    }

    init() {
        console.log("[QuickEditManager] Initializing with data:", this.data);
        
        // Add validation for data before initialization
        if (!Array.isArray(this.data)) {
            console.error("[QuickEditManager] Expected data to be an array, got:", typeof this.data);
            this.container.innerHTML = `<div class="alert alert-danger">
                <strong>Error:</strong> Invalid data format. Expected an array of IROs.
            </div>`;
            return;
        }
        
        // Initialize Handsontable
        this.initHandsontable();
        
        // Add event listeners
        this.addEventListeners();
    }

    initHandsontable() {
        // Define column configurations
        const columnDefs = [
            { data: 'iro_id', title: 'IRO ID', readOnly: true, width: 80 },
            { data: 'title', title: 'Title', readOnly: true, width: 200 },
            { 
                data: 'type', 
                title: 'Type',
                readOnly: true,
                width: 100,
                renderer: this.typeRenderer
            },
            {
                data: 'topic',
                title: 'Topic',
                readOnly: true,
                width: 120
            },
            { 
                data: 'impact_score', 
                title: 'Impact Score', 
                type: 'numeric',
                numericFormat: {
                    pattern: '0.0'
                },
                readOnly: true,
                width: 120,
                renderer: this.scoreRenderer
            },
            { 
                data: 'financial_score', 
                title: 'Financial Score', 
                type: 'numeric',
                numericFormat: {
                    pattern: '0.0'
                },
                readOnly: true,
                width: 120,
                renderer: this.scoreRenderer
            },
            { 
                data: 'current_stage', 
                title: 'Status',
                type: 'dropdown',
                source: ['Draft', 'In Review', 'Approved', 'Rejected'],
                width: 120,
                renderer: this.statusRenderer
            },
            {
                title: 'Actions',
                data: 'iro_id',
                readOnly: true,
                width: 100,
                renderer: this.actionsRenderer
            }
        ];
        
        // Initialize Handsontable
        this.hot = new Handsontable(this.container, {
            data: this.data,
            columns: columnDefs,
            rowHeaders: true,
            colHeaders: true,
            stretchH: 'all',
            autoColumnSize: false,
            contextMenu: false,
            manualColumnResize: true,
            licenseKey: 'non-commercial-and-evaluation',
            afterChange: (changes, source) => {
                if (source === 'edit') {
                    this.handleDataChange(changes);
                }
            }
        });
    }

    addEventListeners() {
        // Add event listener for save button
        if (this.saveButton) {
            this.saveButton.addEventListener('click', () => {
                this.saveChanges();
            });
        }
    }

    handleDataChange(changes) {
        if (!changes) return;
        
        // Set hasChanges flag to true
        this.hasChanges = true;
        
        // Show save button
        if (this.saveButton) {
            this.saveButton.style.display = 'inline-block';
        }
    }

    saveChanges() {
        // Get the current data from Handsontable
        const currentData = this.hot.getData();
        const changedRows = [];
        
        // Find rows that have changed
        for (let i = 0; i < currentData.length; i++) {
            const currentRow = this.hot.getSourceDataAtRow(i);
            const originalRow = this.originalData.find(row => row.iro_id === currentRow.iro_id);
            
            if (originalRow && JSON.stringify(currentRow) !== JSON.stringify(originalRow)) {
                changedRows.push({
                    iro_id: currentRow.iro_id,
                    current_stage: currentRow.current_stage
                });
            }
        }
        
        // If no changes, return
        if (changedRows.length === 0) {
            console.log("[QuickEditManager] No changes to save.");
            return;
        }
        
        console.log("[QuickEditManager] Saving changes for rows:", changedRows);

        // Send changes to server
        fetch(this.saveUrl, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({ iros: changedRows })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log("[QuickEditManager] Changes saved successfully. Server response:", data);
            
            // Update original data with new data
            this.originalData = JSON.parse(JSON.stringify(this.hot.getSourceData()));
            
            // Reset hasChanges flag
            this.hasChanges = false;
            
            // Hide save button
            if (this.saveButton) {
                this.saveButton.style.display = 'none';
            }
            
            // Show success message
            this.showNotification('Changes saved successfully', 'success');
        })
        .catch(error => {
            console.error('[QuickEditManager] Error saving changes:', error);
            this.showNotification('Error saving changes', 'error');
        });
    }

    getCsrfToken() {
        // Get CSRF token from cookie
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Append to body
        document.body.appendChild(notification);
        
        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 150);
        }, 3000);
    }

    // Custom renderers for Handsontable
    typeRenderer(instance, td, row, col, prop, value, cellProperties) {
        Handsontable.renderers.TextRenderer.apply(this, arguments);
        
        // Add badge styling based on type
        if (value) {
            let badgeClass = 'primary';
            if (value === 'Risk') badgeClass = 'danger';
            else if (value === 'Opportunity') badgeClass = 'success';
            
            td.innerHTML = `<span class="badge bg-${badgeClass}">${value}</span>`;
        }
        
        return td;
    }

    scoreRenderer(instance, td, row, col, prop, value, cellProperties) {
        Handsontable.renderers.NumericRenderer.apply(this, arguments);
        
        // Add progress bar styling
        if (value) {
            let barClass = 'success';
            if (value > 3.5) barClass = 'danger';
            else if (value > 2.5) barClass = 'warning';
            
            const percentage = value * 20; // Scale to percentage (0-5 scale * 20 = 0-100%)
            
            td.innerHTML = `
                <div class="d-flex align-items-center">
                    <span class="me-2">${parseFloat(value).toFixed(1)}</span>
                    <div class="progress" style="width: 60px; height: 5px;">
                        <div class="progress-bar bg-${barClass}" style="width: ${percentage}%"></div>
                    </div>
                </div>
            `;
        }
        
        return td;
    }

    statusRenderer(instance, td, row, col, prop, value, cellProperties) {
        Handsontable.renderers.TextRenderer.apply(this, arguments);
        
        // Add badge styling based on status
        if (value) {
            let badgeClass = 'secondary';
            if (value === 'In Review') badgeClass = 'warning';
            else if (value === 'Approved') badgeClass = 'success';
            else if (value === 'Rejected') badgeClass = 'danger';
            
            td.innerHTML = `<span class="badge bg-${badgeClass}">${value}</span>`;
        }
        
        return td;
    }

    actionsRenderer(instance, td, row, col, prop, value, cellProperties) {
        Handsontable.renderers.TextRenderer.apply(this, arguments);
        
        // Add action buttons
        td.innerHTML = `
            <div class="d-flex justify-content-center">
                <a href="/assessments/iro/detail/${value}/" class="btn btn-sm btn-outline-primary me-1" title="View Details">
                    <i class="fas fa-eye"></i>
                </a>
                <a href="/assessments/iro/edit/${value}/" class="btn btn-sm btn-outline-secondary" title="Edit IRO">
                    <i class="fas fa-edit"></i>
                </a>
            </div>
        `;
        
        return td;
    }
}

// Initialize the quick edit manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('priority-iros-container');
    if (container) {
        // Use the global variable instead of the data attribute
        const data = window.priorityIrosData || [];
        console.log("[QuickEditManager] Data from global variable:", data);

        // Get the save URL from data attribute
        const saveUrl = container.dataset.saveUrl;

        // Initialize the quick edit manager
        const quickEditManager = new QuickEditManager(container, data, saveUrl);
        
        // Store the instance in the window object for potential external access
        window.quickEditManager = quickEditManager;
    }
});