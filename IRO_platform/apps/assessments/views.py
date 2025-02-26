# apps/assessments/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django import forms
from tenants.models import TenantConfig
from django_tenants.utils import schema_context
from apps.assessments.models import IRO, Assessment

class ContextMixin:
    """
    Mixin to add context-aware functionality to views.
    
    Adds context_data to the template context, including:
    - available_tenants: List of available tenants
    - available_assessments: List of available assessments
    - available_iros: List of available IROs
    
    Additionally sets up filtering based on the current context.
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add context selectors data
        if self.request.user.is_staff:
            context['available_tenants'] = TenantConfig.objects.all()
        
        # Filter assessments by tenant if a tenant is selected
        tenant = self.request.context.get('tenant')
        try:
            if tenant:
                with schema_context(tenant.schema_name):
                    context['available_assessments'] = list(Assessment.objects.filter(tenant=tenant))
            else:
                # If no tenant selected, try to get all assessments
                context['available_assessments'] = []
                for t in TenantConfig.objects.all():
                    with schema_context(t.schema_name):
                        tenant_assessments = list(Assessment.objects.filter(tenant=t))
                        context['available_assessments'].extend(tenant_assessments)
        except Exception as e:
            # Fallback if filtering fails (e.g., missing tenant field)
            context['available_assessments'] = []
        
        # Filter IROs by assessment if an assessment is selected
        assessment = self.request.context.get('assessment')
        try:
            from apps.assessments.utils import get_iros_for_tenant
            
            if tenant:
                # Get IROs for this tenant (possibly filtered by assessment)
                if assessment:
                    with schema_context(tenant.schema_name):
                        # Assuming IROs can be linked to assessments
                        # Adjust this query based on your actual data model
                        context['available_iros'] = list(IRO.objects.filter(tenant=tenant))
                else:
                    context['available_iros'] = get_iros_for_tenant(tenant)
            else:
                # If no tenant selected, get IROs from all tenant schemas
                context['available_iros'] = []
                for t in TenantConfig.objects.all():
                    with schema_context(t.schema_name):
                        tenant_iros = list(IRO.objects.filter(tenant=t))
                        context['available_iros'].extend(tenant_iros)
        except Exception as e:
            # Fallback if filtering fails
            context['available_iros'] = []
            
        return context
    
    def get_queryset(self):
        # Import the utility function
        from apps.assessments.utils import get_iros_for_tenant, get_all_tenant_iros
        
        # For IRO models, we need special handling with schema context
        if hasattr(self, 'model') and self.model == IRO:
            tenant = self.request.context.get('tenant')
            if tenant:
                queryset = get_iros_for_tenant(tenant)
            else:
                queryset = get_all_tenant_iros()
            return queryset
        
        # For other models, use the standard approach
        queryset = super().get_queryset()
        
        try:
            # Filter by tenant
            tenant = self.request.context.get('tenant')
            if tenant and hasattr(self.model, 'tenant'):
                queryset = queryset.filter(tenant=tenant)
            
            # Filter by assessment
            assessment = self.request.context.get('assessment')
            if assessment and hasattr(self.model, 'assessment'):
                queryset = queryset.filter(assessment=assessment)
            
            # Filter by IRO
            iro = self.request.context.get('iro')
            if iro and hasattr(self.model, 'iro'):
                queryset = queryset.filter(iro=iro)
        except Exception as e:
            # If any filtering fails, return the original queryset
            pass
            
        return queryset


########################
# Existing CBVs for Assessment
########################

class AssessmentListView(ContextMixin, ListView):
    model = Assessment
    template_name = 'assessments/assessment_list.html'
    context_object_name = 'assessments'


class AssessmentCreateView(ContextMixin, CreateView):
    model = Assessment
    fields = ['name', 'description']
    template_name = 'assessments/assessment_form.html'
    success_url = reverse_lazy('assessments:list')


class AssessmentUpdateView(ContextMixin, UpdateView):
    model = Assessment
    fields = ['name', 'description']
    template_name = 'assessments/assessment_form.html'
    success_url = reverse_lazy('assessments:list')


########################
# New: IRO CRUD Views
########################

class IROForm(forms.ModelForm):
    """Example usage of django-crispy-forms (optional). 
       Just ensure you have 'crispy_forms' in INSTALLED_APPS and 
       installed the library via pip."""
    class Meta:
        model = IRO
        fields = [
            'tenant',
            'type',
            'source_of_iro',
            'esrs_standard',
            'current_stage',
            'last_assessment_date',
        ]

class IROListView(ContextMixin, ListView):
    model = IRO
    template_name = 'assessments/iro_list.html'
    context_object_name = 'iros'


class IROCreateView(ContextMixin, CreateView):
    model = IRO
    form_class = IROForm
    template_name = 'assessments/iro_form.html'
    success_url = reverse_lazy('assessments:iro-list')


class IROUpdateView(ContextMixin, UpdateView):
    model = IRO
    form_class = IROForm
    template_name = 'assessments/iro_form.html'
    success_url = reverse_lazy('assessments:iro-list')