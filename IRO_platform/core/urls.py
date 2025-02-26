# core/urls.py
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.views.generic import TemplateView
from . import views  # Add this import to reference the core/views.py module

def home(request):
    return HttpResponse("Welcome to the IRO Platform!")

urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('admin/', admin.site.urls),
    path('assessments/', include('apps.assessments.urls')),  # Existing
    path('tenants/', include('tenants.urls', namespace='tenants')),  # Existing

    # NEW: Register the DRF endpoints
    path('api/assessments/', include('apps.assessments.api.urls')),  
    path('api/tenants/', include('tenants.api.urls')), 

    path('set-context/', views.set_context, name='set_context'),
]