# tenants/api/serializers.py
from rest_framework import serializers
from tenants.models import TenantConfig

class TenantConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantConfig
        fields = ['tenant_id', 'tenant_name', 'schema_name', 'created_on']