# tenants/api/views.py
from rest_framework import viewsets, permissions
from tenants.models import TenantConfig
from .serializers import TenantConfigSerializer

class TenantConfigViewSet(viewsets.ModelViewSet):
    serializer_class = TenantConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # If user is staff, allow access to all tenants
        if self.request.user.is_staff:
            return TenantConfig.objects.all()
        
        # For non-staff users, use the current tenant from context
        # This assumes context middleware is being used
        tenant = getattr(self.request, 'context', {}).get('tenant')
        if tenant:
            return TenantConfig.objects.filter(tenant_id=tenant.tenant_id)
        
        # Fallback: return an empty queryset
        return TenantConfig.objects.none()