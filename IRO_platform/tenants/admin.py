# tenants/admin.py

from django.contrib import admin
from .models import TenantConfig, TenantDomain

@admin.register(TenantConfig)
class TenantConfigAdmin(admin.ModelAdmin):
    list_display = ('tenant_id', 'tenant_name', 'schema_name', 'created_on')
    search_fields = ('tenant_name', 'schema_name')
    list_filter = ('created_on',)

@admin.register(TenantDomain)
class TenantDomainAdmin(admin.ModelAdmin):
    list_display = ('id', 'domain', 'tenant', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('domain',)