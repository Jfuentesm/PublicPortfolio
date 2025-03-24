# apps/assessments/urls.py
from django.urls import path
from .views import (
    AssessmentListView, AssessmentCreateView, AssessmentUpdateView,
    IROListView, IROCreateView, IROUpdateView, iro_save, assessment_save,
    assessment_data, iro_data
)
from .api.topic_views import (
    TopicMaterialityView, PriorityIROsView, RecentActivityView,
    BatchUpdateIROsView
)

app_name = 'assessments'

urlpatterns = [
    path('', AssessmentListView.as_view(), name='list'),
    path('create/', AssessmentCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', AssessmentUpdateView.as_view(), name='edit'),
    path('assessment/data/', assessment_data, name='assessment-data'),
    path('assessment/save/', assessment_save, name='assessment-save'),

    # IRO CRUD
    path('iro/', IROListView.as_view(), name='iro-list'),
    path('iro/create/', IROCreateView.as_view(), name='iro-create'),
    path('iro/<int:pk>/edit/', IROUpdateView.as_view(), name='iro-edit'),
    path('iro/data/', iro_data, name='iro-data'),
    path('iro/save/', iro_save, name='iro-save'),  

    # New API endpoints for topic-level data
    path('api/topics/materiality/', TopicMaterialityView.as_view(), name='topic-materiality'),
    path('api/iros/priority/', PriorityIROsView.as_view(), name='priority-iros'),
    path('api/iros/batch-update/', BatchUpdateIROsView.as_view(), name='batch-update-iros'),
    path('api/activity/recent/', RecentActivityView.as_view(), name='recent-activity'),
]