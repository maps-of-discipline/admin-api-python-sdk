from __future__ import annotations

from admin_api.api.users.schemas import UserPermissions
from admin_api.auth.context import AuthContext
from admin_api.exceptions import PermissionDenied


def has_any(permissions: UserPermissions, required: tuple[str, ...]) -> bool:
    return any(permission in permissions for permission in required)


def assert_has_permission(context: AuthContext, required: tuple[str, ...]) -> None:
    if required and not has_any(context.permissions, required):
        raise PermissionDenied()
