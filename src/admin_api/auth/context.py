from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from admin_api.api.users.schemas import FullUser, Scope, UserPermissions


@dataclass
class AuthContext:
    user: FullUser
    permissions: UserPermissions
    extras: dict[str, Any] = field(default_factory=dict)

    def has(self, permission: str) -> bool:
        return permission in self.permissions

    def scopes(self, permission: str) -> list[Scope]:
        return self.permissions.get(permission, [])
