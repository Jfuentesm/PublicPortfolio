# apps/assessments/api/urls.py
from rest_framework.routers import DefaultRouter
from .views import IROViewSet

router = DefaultRouter()
router.register(r'iros', IROViewSet, basename='iro')

urlpatterns = router.urls