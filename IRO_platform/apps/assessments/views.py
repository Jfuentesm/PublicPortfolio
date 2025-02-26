# apps/assessments/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django import forms
from .models import Assessment, IRO
from tenants.models import TenantConfig

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
                context['available_assessments'] = Assessment.objects.filter(tenant=tenant)
            else:
                context['available_assessments'] = Assessment.objects.all()
        except Exception as e:
            # Fallback if filtering fails (e.g., missing tenant field)
            context['available_assessments'] = Assessment.objects.all()
        
        # Filter IROs by assessment if an assessment is selected
        assessment = self.request.context.get('assessment')
        try:
            if assessment:
                # Assuming IROs can be linked to assessments
                # Adjust this query based on your actual data model
                context['available_iros'] = IRO.objects.filter(assessment=assessment)
            elif tenant:
                # If only tenant is selected, show all IROs for that tenant
                context['available_iros'] = IRO.objects.filter(tenant=tenant)
            else:
                context['available_iros'] = IRO.objects.all()
        except Exception as e:
            # Fallback if filtering fails
            context['available_iros'] = IRO.objects.all()
            
        return context
    
    def get_queryset(self):
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