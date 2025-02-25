# tenants/views.py
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import TenantConfig

class TenantConfigListView(ListView):
    model = TenantConfig
    template_name = 'tenants/tenant_list.html'
    context_object_name = 'tenants'

class TenantConfigCreateView(CreateView):
    model = TenantConfig
    fields = ['tenant_name', 'schema_name']
    template_name = 'tenants/tenant_form.html'
    success_url = reverse_lazy('tenants:list')

class TenantConfigUpdateView(UpdateView):
    model = TenantConfig
    fields = ['tenant_name', 'schema_name']
    template_name = 'tenants/tenant_form.html'
    success_url = reverse_lazy('tenants:list')