# core/urls.py - Update the home URL pattern

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    # Replace this line:
    # path('', TemplateView.as_view(template_name='home.html'), name='home'),
    # With this:
    path('', views.home_dashboard, name='home'),
    
    # Keep the rest of the URL patterns the same
    path('admin/', admin.site.urls),
    path('assessments/', include('apps.assessments.urls')),
    path('tenants/', include('tenants.urls', namespace='tenants')),
    path('api/assessments/', include('apps.assessments.api.urls')),  
    path('api/tenants/', include('tenants.api.urls')), 
    path('set-context/', views.set_context, name='set_context'),
]