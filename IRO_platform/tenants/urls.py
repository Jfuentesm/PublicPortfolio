# tenants/urls.py
from django.urls import path
from .views import TenantConfigListView, TenantConfigCreateView, TenantConfigUpdateView

app_name = 'tenants'

urlpatterns = [
    path('', TenantConfigListView.as_view(), name='list'),
    path('create/', TenantConfigCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', TenantConfigUpdateView.as_view(), name='edit'),
]