"""
Package per l'autenticazione e autorizzazione multi-tenant.
"""

from .rbac import (
    require_role_in_tenant,
    require_any_role_in_tenant,
    require_permission_in_tenant,
    require_any_permission_in_tenant,
    get_user_tenant_roles,
    get_user_tenants
)

__all__ = [
    'require_role_in_tenant',
    'require_any_role_in_tenant',
    'require_permission_in_tenant',
    'require_any_permission_in_tenant',
    'get_user_tenant_roles',
    'get_user_tenants'
] 