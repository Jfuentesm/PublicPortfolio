# tenants/api/urls.py
from rest_framework.routers import DefaultRouter
from .views import TenantConfigViewSet

router = DefaultRouter()
router.register(r'tenant-configs', TenantConfigViewSet, basename='tenant-config')

urlpatterns = router.urls