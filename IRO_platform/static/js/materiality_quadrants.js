/**
 * Materiality Quadrants JavaScript Module
 * 
 * This module handles the rendering and interaction with the topic-level
 * double materiality quadrants on the dashboard.
 */

class MaterialityQuadrants {
    constructor(container, data) {
        this.container = container;
        this.data = data;
        this.init();
    }

    init() {
        // Initialize tooltips for topic items
        this.initTooltips();
        
        // Add event listeners for topic items
        this.addEventListeners();
    }

    initTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(this.container.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    addEventListeners() {
        // Add click event listeners to topic items
        const topicLinks = this.container.querySelectorAll('.topic-item a');
        topicLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const topicName = link.querySelector('.topic-name').textContent;
                this.handleTopicClick(topicName);
            });
        });
    }

    handleTopicClick(topicName) {
        // Navigate to topic detail page or show topic detail modal
        console.log(`Topic clicked: ${topicName}`);
        
        // Example: Show a modal with topic details
        // You can implement this based on your application's requirements
        this.showTopicDetailModal(topicName);
    }

    showTopicDetailModal(topicName) {
        // Find the topic in the data
        let topic = null;
        for (const quadrant in this.data) {
            const found = this.data[quadrant].find(t => t.name === topicName);
            if (found) {
                topic = found;
                break;
            }
        }
        
        if (!topic) return;
        
        // Create modal content
        const modalTitle = `Topic: ${topic.name}`;
        const modalBody = `
            <div class="topic-detail">
                <div class="row mb-3">
                    <div class="col-6">
                        <div class="card">
                            <div class="card-body text-center">
                                <h3>${topic.impact_score.toFixed(1)}</h3>
                                <p class="mb-0">Impact Score</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="card">
                            <div class="card-body text-center">
                                <h3>${topic.financial_score.toFixed(1)}</h3>
                                <p class="mb-0">Financial Score</p>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="mb-3">
                    <h6>Related IROs (${topic.iro_count})</h6>
                    <p class="text-muted small">Click to view all IROs related to this topic</p>
                </div>
            </div>
        `;
        
        // Show modal (using Bootstrap modal)
        const modalEl = document.getElementById('topicDetailModal');
        let modal;
        
        if (modalEl) {
            // Update existing modal
            modal = bootstrap.Modal.getInstance(modalEl);
            modalEl.querySelector('.modal-title').textContent = modalTitle;
            modalEl.querySelector('.modal-body').innerHTML = modalBody;
        } else {
            // Create new modal
            const modalHTML = `
                <div class="modal fade" id="topicDetailModal" tabindex="-1" aria-labelledby="topicDetailModalLabel" aria-hidden="true">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="topicDetailModalLabel">${modalTitle}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                ${modalBody}
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                <button type="button" class="btn btn-primary">View IROs</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Append modal to body
            document.body.insertAdjacentHTML('beforeend', modalHTML);
            
            // Initialize modal
            modal = new bootstrap.Modal(document.getElementById('topicDetailModal'));
        }
        
        // Show the modal
        modal.show();
    }

    // Refresh the quadrants with new data
    refreshData(newData) {
        this.data = newData;
        
        // Update the UI based on the new data
        // This would require re-rendering the quadrants or updating the DOM
        // For simplicity, you might want to reload the page or implement a more sophisticated update mechanism
    }
}

// Initialize the materiality quadrants when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.materiality-quadrants-container');
    if (container) {
        // Get the data from the page
        const quadrantsData = JSON.parse(document.getElementById('topic-quadrants-data').textContent);
        
        // Initialize the materiality quadrants
        const materialityQuadrants = new MaterialityQuadrants(container, quadrantsData);
        
        // Store the instance in the window object for potential external access
        window.materialityQuadrants = materialityQuadrants;
    }
});
