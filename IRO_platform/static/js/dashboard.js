// static/js/dashboard.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the materiality matrix chart if the canvas exists
    const matrixCanvas = document.getElementById('materialityMatrix');
    if (matrixCanvas) {
        initializeMaterialityMatrix(matrixCanvas);
    }

    // Initialize IRO distribution chart if the canvas exists
    const distributionCanvas = document.getElementById('iroDistributionChart');
    if (distributionCanvas) {
        initializeIRODistributionChart(distributionCanvas);
    }

    // Initialize assessment progress chart if the canvas exists
    const progressCanvas = document.getElementById('assessmentProgressChart');
    if (progressCanvas) {
        initializeAssessmentProgressChart(progressCanvas);
    }

    // Setup event listeners for dashboard filters
    setupFilterListeners();

    // Initialize any tooltips
    initializeTooltips();
});

/**
 * Initializes the materiality matrix visualization
 * @param {HTMLCanvasElement} canvas - The canvas element for the chart
 */
function initializeMaterialityMatrix(canvas) {
    // Sample data for the materiality matrix
    const iroData = [
        { id: 1, title: "Climate Transition Risk", x: 4.2, y: 4.5, type: "Risk", size: 12 },
        { id: 2, title: "Water Scarcity", x: 3.8, y: 3.2, type: "Risk", size: 10 },
        { id: 3, title: "Renewable Energy Adoption", x: 3.5, y: 4.0, type: "Opportunity", size: 11 },
        { id: 4, title: "Supply Chain Emissions", x: 3.0, y: 2.8, type: "Impact", size: 9 },
        { id: 5, title: "Biodiversity Loss", x: 2.5, y: 3.5, type: "Impact", size: 10 },
        { id: 6, title: "Circular Economy", x: 3.2, y: 2.2, type: "Opportunity", size: 8 },
        { id: 7, title: "Labor Rights", x: 4.0, y: 3.0, type: "Risk", size: 9 },
        { id: 8, title: "Product Safety", x: 4.5, y: 3.8, type: "Risk", size: 11 },
        { id: 9, title: "Digital Innovation", x: 2.8, y: 4.2, type: "Opportunity", size: 10 },
        { id: 10, title: "Diversity & Inclusion", x: 2.0, y: 2.5, type: "Impact", size: 8 },
        { id: 11, title: "Energy Efficiency", x: 3.0, y: 3.0, type: "Opportunity", size: 9 },
        { id: 12, title: "Waste Management", x: 2.2, y: 2.0, type: "Impact", size: 7 }
    ];

    // Create datasets for different IRO types with different colors
    const datasets = [
        {
            label: 'Risks',
            data: iroData.filter(item => item.type === 'Risk').map(item => ({
                x: item.x,
                y: item.y,
                r: item.size,
                id: item.id,
                title: item.title
            })),
            backgroundColor: 'rgba(239, 68, 68, 0.7)',
            borderColor: 'rgba(239, 68, 68, 1)'
        },
        {
            label: 'Opportunities',
            data: iroData.filter(item => item.type === 'Opportunity').map(item => ({
                x: item.x,
                y: item.y,
                r: item.size,
                id: item.id,
                title: item.title
            })),
            backgroundColor: 'rgba(34, 197, 94, 0.7)',
            borderColor: 'rgba(34, 197, 94, 1)'
        },
        {
            label: 'Impacts',
            data: iroData.filter(item => item.type === 'Impact').map(item => ({
                x: item.x,
                y: item.y,
                r: item.size,
                id: item.id,
                title: item.title
            })),
            backgroundColor: 'rgba(59, 130, 246, 0.7)',
            borderColor: 'rgba(59, 130, 246, 1)'
        }
    ];

    // Create the bubble chart
    const matrixChart = new Chart(canvas, {
        type: 'bubble',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Financial Materiality',
                        font: {
                            weight: 'bold'
                        }
                    },
                    min: 0,
                    max: 5,
                    ticks: {
                        stepSize: 1
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Impact Materiality',
                        font: {
                            weight: 'bold'
                        }
                    },
                    min: 0,
                    max: 5,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const item = context.raw;
                            return [
                                `ID: #${item.id}`,
                                `Title: ${item.title}`,
                                `Financial Materiality: ${item.x.toFixed(1)}`,
                                `Impact Materiality: ${item.y.toFixed(1)}`
                            ];
                        }
                    }
                },
                legend: {
                    position: 'bottom'
                },
                annotation: {
                    annotations: {
                        quadrantLines: {
                            type: 'line',
                            xMin: 2.5,
                            xMax: 2.5,
                            yMin: 0,
                            yMax: 5,
                            borderColor: 'rgba(0, 0, 0, 0.2)',
                            borderWidth: 1,
                            borderDash: [5, 5]
                        },
                        horizontalLine: {
                            type: 'line',
                            xMin: 0,
                            xMax: 5,
                            yMin: 2.5,
                            yMax: 2.5,
                            borderColor: 'rgba(0, 0, 0, 0.2)',
                            borderWidth: 1,
                            borderDash: [5, 5]
                        }
                    }
                }
            }
        }
    });

    // Add click event to navigate to IRO details
    canvas.onclick = function(evt) {
        const points = matrixChart.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, true);
        if (points.length) {
            const firstPoint = points[0];
            const dataset = matrixChart.data.datasets[firstPoint.datasetIndex];
            const iro = dataset.data[firstPoint.index];
            // Navigate to IRO detail page
            window.location.href = `/assessments/iro/${iro.id}/`;
        }
    };
}

/**
 * Initializes the IRO distribution chart
 * @param {HTMLCanvasElement} canvas - The canvas element for the chart
 */
function initializeIRODistributionChart(canvas) {
    // Sample data for IRO distribution
    const data = {
        labels: ['Risks', 'Opportunities', 'Impacts'],
        datasets: [{
            data: [12, 8, 10],
            backgroundColor: [
                'rgba(239, 68, 68, 0.7)',
                'rgba(34, 197, 94, 0.7)',
                'rgba(59, 130, 246, 0.7)'
            ],
            borderColor: [
                'rgba(239, 68, 68, 1)',
                'rgba(34, 197, 94, 1)',
                'rgba(59, 130, 246, 1)'
            ],
            borderWidth: 1
        }]
    };

    // Create the pie chart
    const distributionChart = new Chart(canvas, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Initializes the assessment progress chart
 * @param {HTMLCanvasElement} canvas - The canvas element for the chart
 */
function initializeAssessmentProgressChart(canvas) {
    // Sample data for assessment progress
    const data = {
        labels: ['Draft', 'In Review', 'Approved', 'Disclosed'],
        datasets: [{
            label: 'Number of IROs',
            data: [15, 8, 6, 5],
            backgroundColor: [
                'rgba(156, 163, 175, 0.7)',
                'rgba(234, 179, 8, 0.7)',
                'rgba(34, 197, 94, 0.7)',
                'rgba(249, 115, 22, 0.7)'
            ],
            borderColor: [
                'rgba(156, 163, 175, 1)',
                'rgba(234, 179, 8, 1)',
                'rgba(34, 197, 94, 1)',
                'rgba(249, 115, 22, 1)'
            ],
            borderWidth: 1
        }]
    };

    // Create the bar chart
    const progressChart = new Chart(canvas, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of IROs',
                        font: {
                            weight: 'bold'
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

/**
 * Sets up event listeners for dashboard filters
 */
function setupFilterListeners() {
    // Time period filter for materiality matrix
    const matrixDropdown = document.getElementById('matrixDropdown');
    if (matrixDropdown) {
        const dropdownItems = document.querySelectorAll('[aria-labelledby="matrixDropdown"] .dropdown-item');
        dropdownItems.forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                const selectedPeriod = this.textContent;
                matrixDropdown.textContent = selectedPeriod;
                // Here you would typically fetch new data based on the selected period
                // and update the chart
                updateMatrixData(selectedPeriod);
            });
        });
    }

    // IRO type filter
    const typeFilter = document.getElementById('iroTypeFilter');
    if (typeFilter) {
        typeFilter.addEventListener('change', function() {
            // Filter dashboard data based on selected IRO type
            filterDashboardByType(this.value);
        });
    }

    // Status filter
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            // Filter dashboard data based on selected status
            filterDashboardByStatus(this.value);
        });
    }
}

/**
 * Updates the materiality matrix data based on selected time period
 * @param {string} period - The selected time period
 */
function updateMatrixData(period) {
    // This would typically involve an AJAX call to fetch new data
    console.log(`Updating matrix data for period: ${period}`);
    
    // Example of how you might update the chart with new data
    // In a real implementation, you would fetch this data from your backend
    const matrixCanvas = document.getElementById('materialityMatrix');
    if (matrixCanvas) {
        const chart = Chart.getChart(matrixCanvas);
        if (chart) {
            // Simulate data changes based on selected period
            chart.data.datasets.forEach(dataset => {
                dataset.data.forEach(point => {
                    // Slightly modify the data points to simulate changes
                    point.x += (Math.random() - 0.5) * 0.5;
                    point.y += (Math.random() - 0.5) * 0.5;
                    // Ensure values stay within bounds
                    point.x = Math.max(0, Math.min(5, point.x));
                    point.y = Math.max(0, Math.min(5, point.y));
                });
            });
            chart.update();
        }
    }
}

/**
 * Filters dashboard data based on IRO type
 * @param {string} type - The selected IRO type
 */
function filterDashboardByType(type) {
    console.log(`Filtering dashboard by IRO type: ${type}`);
    
    // This would typically involve updating all relevant dashboard components
    // based on the selected filter
    
    // Example: Update high-priority IROs table
    const iroTable = document.getElementById('highPriorityIROsTable');
    if (iroTable && iroTable.tBodies[0]) {
        const rows = iroTable.tBodies[0].rows;
        for (let i = 0; i < rows.length; i++) {
            const iroType = rows[i].cells[1].textContent.trim();
            if (type === 'All' || iroType === type) {
                rows[i].style.display = '';
            } else {
                rows[i].style.display = 'none';
            }
        }
    }
    
    // You would also update other dashboard components like charts
    // based on the selected filter
}

/**
 * Filters dashboard data based on status
 * @param {string} status - The selected status
 */
function filterDashboardByStatus(status) {
    console.log(`Filtering dashboard by status: ${status}`);
    
    // Similar to filterDashboardByType, but filtering based on status
    
    // Example: Update recent activity timeline
    const activityItems = document.querySelectorAll('.activity-item');
    activityItems.forEach(item => {
        const itemStatus = item.getAttribute('data-status');
        if (status === 'All' || itemStatus === status) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
    
    // You would also update other dashboard components
}

/**
 * Initializes Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

/**
 * Handles window resize events to ensure charts remain responsive
 */
window.addEventListener('resize', function() {
    const matrixCanvas = document.getElementById('materialityMatrix');
    if (matrixCanvas) {
        const chart = Chart.getChart(matrixCanvas);
        if (chart) {
            chart.resize();
        }
    }
    
    const distributionCanvas = document.getElementById('iroDistributionChart');
    if (distributionCanvas) {
        const chart = Chart.getChart(distributionCanvas);
        if (chart) {
            chart.resize();
        }
    }
    
    const progressCanvas = document.getElementById('assessmentProgressChart');
    if (progressCanvas) {
        const chart = Chart.getChart(progressCanvas);
        if (chart) {
            chart.resize();
        }
    }
});

/**
 * Exports the current materiality matrix as an image
 */
function exportMatrixAsImage() {
    const matrixCanvas = document.getElementById('materialityMatrix');
    if (matrixCanvas) {
        const link = document.createElement('a');
        link.download = 'materiality_matrix.png';
        link.href = matrixCanvas.toDataURL('image/png');
        link.click();
    }
}

/**
 * Initializes search functionality for IRO tables
 */
function initializeSearch() {
    const searchInput = document.getElementById('iroSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const table = document.getElementById('highPriorityIROsTable');
            if (table && table.tBodies[0]) {
                const rows = table.tBodies[0].rows;
                
                for (let i = 0; i < rows.length; i++) {
                    const text = rows[i].textContent.toLowerCase();
                    if (text.indexOf(searchTerm) > -1) {
                        rows[i].style.display = '';
                    } else {
                        rows[i].style.display = 'none';
                    }
                }
            }
        });
    }
}

// Initialize search when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();
});
