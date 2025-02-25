# tenants/api/views.py
from rest_framework import viewsets, permissions
from tenants.models import TenantConfig
from .serializers import TenantConfigSerializer

class TenantConfigViewSet(viewsets.ModelViewSet):
    queryset = TenantConfig.objects.all()
    serializer_class = TenantConfigSerializer
    permission_classes = [permissions.IsAuthenticated]