# core/urls.py - Update the URL patterns

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    # Keep existing URLs
    path('', views.home_dashboard, name='home'),
    path('admin/', admin.site.urls),
    path('assessments/', include('apps.assessments.urls')),
    path('tenants/', include('tenants.urls', namespace='tenants')),
    path('api/assessments/', include('apps.assessments.api.urls')),  
    path('api/tenants/', include('tenants.api.urls')), 
    path('set-context/', views.set_context, name='set_context'),
    
    # Add new URL for frontend logs
    path('api/logs/frontend/', views.frontend_log, name='frontend_log'),
]