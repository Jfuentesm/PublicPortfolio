# Homescreen Implementation Documentation

## Overview

This document provides an overview of the new homescreen implementation for the IRO Platform. The new design focuses on topic-level data aggregation and visualization, providing users with a more comprehensive view of their sustainability topics and IROs.

## Key Features

### 1. Topic-Level Double Materiality Quadrants

The centerpiece of the new homescreen is the Topic-Level Double Materiality Quadrants visualization. This feature:

- Aggregates IROs into sustainability topics
- Calculates topic-level materiality scores (impact and financial)
- Displays topics in four quadrants based on their materiality scores:
  - **Double Material**: High impact and high financial materiality
  - **Impact Material**: High impact but low financial materiality
  - **Financially Material**: Low impact but high financial materiality
  - **Not Material**: Low impact and low financial materiality

Each topic shows the number of IROs it contains, and users can click on a topic to see more details.

### 2. Priority IROs Quick-Edit Table

The Priority IROs section allows users to:

- View high-priority IROs based on materiality scores
- Quickly edit IRO status directly from the dashboard
- Access detailed IRO information via action buttons

This feature uses Handsontable for an Excel-like editing experience.

### 3. Collapsible Recent Activity

The Recent Activity section shows:

- Latest actions performed on IROs and assessments
- Color-coded icons for different action types
- Timestamps for when actions occurred

The section is collapsible to save space when needed.

### 4. Key Metrics Cards

The top of the dashboard displays key metrics:

- Total IROs
- High Materiality IROs
- Pending Reviews
- Completed Assessments

## Technical Implementation

### Backend Components

#### Topic Model

The `Topic` model represents sustainability topics and includes:

- Hierarchical structure with levels
- Methods for calculating topic-level materiality scores
- Logic for determining materiality quadrants

```python
class Topic(models.Model):
    """Model representing a sustainability topic."""
    tenant = models.ForeignKey(TenantConfig, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    level = models.IntegerField(default=1)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField(null=True, blank=True)
    
    def calculate_impact_score(self):
        """Calculate the average impact score for all IROs in this topic."""
        # Implementation details...
    
    def calculate_financial_score(self):
        """Calculate the average financial score for all IROs in this topic."""
        # Implementation details...
    
    def get_materiality_quadrant(self):
        """Determine which materiality quadrant this topic belongs to."""
        # Implementation details...
```

#### Topic Aggregator Service

The `topic_aggregator.py` service handles:

- Synchronizing topics from IRO versions
- Retrieving topics by materiality quadrant
- Getting high-priority IROs for quick editing

```python
def sync_topics_from_iro_versions(tenant):
    """Synchronize topics from IRO versions."""
    # Implementation details...

def get_topics_by_materiality_quadrant(tenant):
    """Get topics organized by materiality quadrant."""
    # Implementation details...

def get_priority_iros(tenant, limit=10):
    """Get high-priority IROs for quick editing."""
    # Implementation details...
```

#### API Views

The following API views provide data for the frontend components:

- `TopicMaterialityView`: Provides topic-level materiality data
- `PriorityIROsView`: Returns high-priority IROs for quick editing
- `BatchUpdateIROsView`: Handles batch updates for IROs
- `RecentActivityView`: Provides recent activity data

### Frontend Components

#### Template Components

- `materiality_quadrants.html`: Displays the four materiality quadrants
- `priority_iros.html`: Contains the quick-edit table for priority IROs
- `recent_activity.html`: Shows the collapsible recent activity section

#### JavaScript Modules

- `materiality_quadrants.js`: Handles interaction with the quadrants
- `quick_edit_manager.js`: Manages the Handsontable for priority IROs

#### CSS Styles

The `dashboard.css` file contains styles for:

- Materiality quadrants
- Priority IROs table
- Recent activity timeline
- Responsive adjustments

## Usage

### Viewing Topic-Level Data

1. Navigate to the dashboard
2. The materiality quadrants show topics grouped by their materiality
3. Click on a topic to see details and related IROs

### Quick-Editing IROs

1. Scroll to the Priority IROs section
2. Click on a cell to edit the value
3. Click the "Save Changes" button to save your edits

### Viewing Recent Activity

1. The Recent Activity section shows the latest actions
2. Click the collapse button to hide/show the activity list
3. Click "View All" to see a complete activity history

## API Reference

### Topic Materiality API

- **Endpoint**: `/api/topics/materiality/`
- **Method**: GET
- **Response**: JSON object with topics grouped by materiality quadrant

### Priority IROs API

- **Endpoint**: `/api/iros/priority/`
- **Method**: GET
- **Response**: JSON array of high-priority IROs

### Batch Update IROs API

- **Endpoint**: `/api/iros/batch-update/`
- **Method**: PATCH
- **Request Body**: JSON object with IROs to update
- **Response**: JSON object with updated IROs and any errors

### Recent Activity API

- **Endpoint**: `/api/activity/recent/`
- **Method**: GET
- **Response**: JSON array of recent activity items
