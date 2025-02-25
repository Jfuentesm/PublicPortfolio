# apps/assessments/urls.py
from django.urls import path
from .views import (
    AssessmentListView, AssessmentCreateView, AssessmentUpdateView,
    IROListView, IROCreateView, IROUpdateView
)

app_name = 'assessments'

urlpatterns = [
    path('', AssessmentListView.as_view(), name='list'),
    path('create/', AssessmentCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', AssessmentUpdateView.as_view(), name='edit'),

    # IRO CRUD
    path('iro/', IROListView.as_view(), name='iro-list'),
    path('iro/create/', IROCreateView.as_view(), name='iro-create'),
    path('iro/<int:pk>/edit/', IROUpdateView.as_view(), name='iro-edit'),
]