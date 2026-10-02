from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from admin_api.api.scopes import Scope, ScopeItem


class UserServiceRolesCreate(BaseModel):
    service_roles_id: UUID | None = None
    user_id: UUID | None = None
    scope: list[ScopeItem] | None = None


class UserServiceRolesUpdate(BaseModel):
    id: UUID
    user_id: UUID
    service_roles_id: UUID
    scope: list[ScopeItem] | None = None


class UserServiceRolesResponse(BaseModel):
    id: UUID
    service_roles_id: UUID | None = None
    user_id: UUID | None = None
    scope: list[Scope] = Field(default_factory=list)
