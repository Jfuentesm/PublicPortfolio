<design of user-facing views in Django>
Based on the provided solution design documents, here's a high-level summary of the key frameworks and modules recommended for building the main user-facing views in Django:

## Core Framework Stack

1. **View Layer**
- Django Class-Based Views (CBVs) for structured CRUD operations
- HTMX + Alpine.js for interactive features (lighter than React/Vue.js)
- django-formtools for multi-step wizards
- django-crispy-forms for form layouts

2. **Data Visualization**
- Chart.js + django-chartjs for materiality matrices and dashboards
- django-tables2 + django-filter for sortable data grids

3. **Authentication & Authorization**
- django-guardian for object-level permissions
- django-allauth for authentication (integrates with Amazon Cognito)

4. **API Integration**
- Django REST framework for API construction and documentation
</design of user-facing views in Django>
