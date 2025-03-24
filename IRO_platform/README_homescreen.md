# IRO Platform Homescreen Implementation

## Overview

This README provides instructions for setting up, testing, and extending the new homescreen implementation for the IRO Platform. The new homescreen features topic-level data aggregation and visualization, providing users with a more comprehensive view of their sustainability topics and IROs.

## Features

- **Topic-Level Double Materiality Quadrants**: Visualize topics based on their impact and financial materiality
- **Priority IROs Quick-Edit Table**: Quickly view and edit high-priority IROs
- **Collapsible Recent Activity**: Track recent changes in the system
- **Key Metrics Cards**: Get an overview of important platform metrics

## Setup Instructions

### 1. Install Dependencies

The homescreen implementation uses Handsontable for the quick-edit functionality. Make sure you have the required dependencies:

```bash
# If using pip
pip install django-tenants django-rest-framework

# If using Docker
# The dependencies are included in the Dockerfile
```

### 2. Run Migrations

After pulling the code, run migrations to create the Topic model:

```bash
python manage.py makemigrations assessments
python manage.py migrate
```

### 3. Synchronize Topics

To populate topics from existing IROs, run the sync_topics management command:

```bash
python manage.py sync_topics

# For a specific tenant
python manage.py sync_topics --tenant=your_tenant_schema
```

## Testing

### Running the Test Script

A test script is provided to populate test data and verify the functionality:

```bash
python scripts/test_homescreen.py
```

This script will:
1. Create a test tenant if it doesn't exist
2. Create test topics and IROs with varying materiality scores
3. Synchronize topics from IROs
4. Test the topic materiality quadrants and priority IROs

### Running Unit Tests

Unit tests for the Topic model and topic aggregator service are available:

```bash
python manage.py test apps.assessments.tests.test_topic_model
```

## Implementation Details

### Backend Components

- **Topic Model**: `apps/assessments/models.py`
- **Topic Aggregator Service**: `apps/assessments/topic_aggregator.py`
- **API Views**: `apps/assessments/api/topic_views.py`
- **URL Configuration**: `apps/assessments/urls.py`
- **Home Dashboard View**: `core/views.py`

### Frontend Components

- **Template Components**:
  - `templates/components/materiality_quadrants.html`
  - `templates/components/priority_iros.html`
  - `templates/components/recent_activity.html`
- **JavaScript Modules**:
  - `static/js/materiality_quadrants.js`
  - `static/js/quick_edit_manager.js`
- **CSS Styles**: `static/css/dashboard.css`
- **Home Template**: `templates/home.html`

## API Endpoints

- **Topic Materiality**: `GET /api/topics/materiality/`
- **Priority IROs**: `GET /api/iros/priority/`
- **Batch Update IROs**: `PATCH /api/iros/batch-update/`
- **Recent Activity**: `GET /api/activity/recent/`

## Extending the Implementation

### Adding New Topic Metrics

To add new metrics for topics:

1. Add the new fields to the Topic model in `apps/assessments/models.py`
2. Add calculation methods for the new metrics
3. Update the topic aggregator service in `apps/assessments/topic_aggregator.py`
4. Update the API views to include the new metrics
5. Modify the frontend components to display the new metrics

### Customizing the Materiality Quadrants

To customize the materiality quadrants:

1. Modify the `get_materiality_quadrant` method in the Topic model
2. Update the `get_topics_by_materiality_quadrant` function in the topic aggregator service
3. Adjust the materiality thresholds as needed
4. Update the frontend components to reflect the changes

## Troubleshooting

### Common Issues

- **Topics not appearing in quadrants**: Run the sync_topics management command to ensure topics are synchronized from IROs
- **Priority IROs table not loading**: Check the browser console for JavaScript errors and ensure Handsontable is properly loaded
- **API endpoints returning errors**: Verify that the tenant context is properly set and the user is authenticated

### Debugging

For debugging issues:

1. Enable Django's debug logging:
   ```python
   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'handlers': {
           'console': {
               'class': 'logging.StreamHandler',
           },
       },
       'loggers': {
           'apps.assessments': {
               'handlers': ['console'],
               'level': 'DEBUG',
           },
       },
   }
   ```

2. Check the browser console for JavaScript errors
3. Use the Django Debug Toolbar for detailed request information

## Documentation

For more detailed documentation, refer to:

- [Homescreen Implementation Documentation](docs/homescreen_implementation.md)
- [API Reference](docs/api_reference.md)
- [Topic Model Documentation](docs/topic_model.md)
