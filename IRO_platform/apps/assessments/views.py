# apps/assessments/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django import forms
from .models import Assessment, IRO

########################
# Existing CBVs for Assessment
########################

class AssessmentListView(ListView):
    model = Assessment
    template_name = 'assessments/assessment_list.html'
    context_object_name = 'assessments'


class AssessmentCreateView(CreateView):
    model = Assessment
    fields = ['name', 'description']
    template_name = 'assessments/assessment_form.html'
    success_url = reverse_lazy('assessments:list')


class AssessmentUpdateView(UpdateView):
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

class IROListView(ListView):
    model = IRO
    template_name = 'assessments/iro_list.html'
    context_object_name = 'iros'


class IROCreateView(CreateView):
    model = IRO
    form_class = IROForm
    template_name = 'assessments/iro_form.html'
    success_url = reverse_lazy('assessments:iro-list')


class IROUpdateView(UpdateView):
    model = IRO
    form_class = IROForm
    template_name = 'assessments/iro_form.html'
    success_url = reverse_lazy('assessments:iro-list')