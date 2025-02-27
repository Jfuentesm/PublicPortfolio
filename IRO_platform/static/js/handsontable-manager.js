// static/js/handsontable-manager.js

/**
 * Handsontable manager for initializing and managing data grids
 * with tenant context awareness
 */
class HandsontableManager {
    constructor() {
        this.instances = {};
        this.currentTenant = null;
        this.currentAssessment = null;
    }

    /**
     * Initialize a Handsontable instance
     * 
     * @param {string} containerId - The container element ID
     * @param {object} options - Handsontable configuration options
     * @param {Array} data - Initial data for the table
     * @param {object} contextData - Object with tenant and assessment info
     * @returns {object} The Handsontable instance
     */
    initTable(containerId, options, data, contextData = {}) {
        // Store context info
        this.currentTenant = contextData.tenant || null;
        this.currentAssessment = contextData.assessment || null;

        // Get the container element
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container with ID "${containerId}" not found`);
            return null;
        }

        // Set default options
        const defaultOptions = {
            licenseKey: 'non-commercial-and-evaluation',
            rowHeaders: true,
            colHeaders: true,
            contextMenu: true,
            stretchH: 'all',
            autoColumnSize: true,
            manualColumnResize: true,
            manualRowResize: true,
            afterChange: (changes, source) => {
                if (source === 'loadData') return;
                this.handleDataChange(containerId, changes, source);
            }
        };

        // Combine options
        const tableOptions = { ...defaultOptions, ...options, data: data || [] };

        // Create the Handsontable instance
        const hot = new Handsontable(container, tableOptions);
        
        // Store the instance
        this.instances[containerId] = hot;

        return hot;
    }

    /**
     * Load data into an existing table
     * 
     * @param {string} containerId - The container element ID
     * @param {Array} data - The data to load
     */
    loadData(containerId, data) {
        const hot = this.instances[containerId];
        if (hot) {
            hot.loadData(data);
        } else {
            console.error(`No Handsontable instance found for "${containerId}"`);
        }
    }

    /**
     * Handle data changes and save to the server
     * 
     * @param {string} containerId - The container element ID
     * @param {Array} changes - Array of changes [row, prop, oldValue, newValue]
     * @param {string} source - Source of the change
     */
    handleDataChange(containerId, changes, source) {
        if (!changes || changes.length === 0) return;

        const hot = this.instances[containerId];
        if (!hot) return;

        const tableData = hot.getData();
        const tableHeaders = hot.getColHeader();
        const contextData = {
            tenant: this.currentTenant,
            assessment: this.currentAssessment
        };

        // Prepare the changes
        const changedRows = [];
        changes.forEach(([row, prop, oldValue, newValue]) => {
            // Find column index for the property
            const colIndex = typeof prop === 'number' ? prop : tableHeaders.indexOf(prop);
            if (colIndex === -1) return;

            // Get the row data
            const rowData = tableData[row];
            if (!rowData) return;

            // Add to changed rows
            changedRows.push({
                rowIndex: row,
                data: rowData,
                changes: { [prop]: newValue }
            });
        });

        // Send changes to the server
        this.saveChanges(containerId, changedRows, contextData);
    }

    /**
     * Save changes to the server
     * 
     * @param {string} containerId - The container element ID
     * @param {Array} changedRows - Array of changed rows
     * @param {object} contextData - Tenant and assessment info
     */
    saveChanges(containerId, changedRows, contextData) {
        // Get the save URL from data attribute
        const container = document.getElementById(containerId);
        const saveUrl = container.dataset.saveUrl;
        if (!saveUrl) {
            console.error(`No save URL found for "${containerId}"`);
            return;
        }

        // Get CSRF token
        const csrftoken = this.getCookie('csrftoken');

        // Send changes to the server
        fetch(saveUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                changes: changedRows,
                contextData: contextData
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Changes saved successfully:', data);
            
            // Check if we need to reload the table
            if (data.reload) {
                this.loadData(containerId, data.data);
            }
            
            // Show success message
            this.showMessage('success', 'Changes saved successfully');
        })
        .catch(error => {
            console.error('Error saving changes:', error);
            this.showMessage('error', 'Error saving changes: ' + error.message);
        });
    }

    /**
     * Get a cookie value by name
     * 
     * @param {string} name - The cookie name
     * @returns {string} The cookie value
     */
    getCookie(name) {
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

    /**
     * Show a message to the user
     * 
     * @param {string} type - Message type ('success', 'error', etc.)
     * @param {string} message - The message text
     */
    showMessage(type, message) {
        // Create message element
        const messageEl = document.createElement('div');
        messageEl.className = `alert alert-${type} position-fixed bottom-0 end-0 m-3`;
        messageEl.style.zIndex = 1050;
        messageEl.textContent = message;
        
        // Add to document
        document.body.appendChild(messageEl);
        
        // Remove after 3 seconds
        setTimeout(() => {
            messageEl.classList.add('fade');
            setTimeout(() => {
                document.body.removeChild(messageEl);
            }, 500);
        }, 3000);
    }
}

// Create global instance
window.handsonTableManager = new HandsontableManager();