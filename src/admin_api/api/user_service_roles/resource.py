from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Any
from uuid import UUID

from pydantic import Field, TypeAdapter

from admin_api.api.common import as_uuid, dump
from admin_api.api.dto import (
    UnitScopeItem,
    UnitTypeScopeItem,
    UserServiceRolesCreate,
    UserServiceRolesResponse,
    UserServiceRolesUpdate,
)
from admin_api.api.request import Operation

ScopeItem = Annotated[UnitScopeItem | UnitTypeScopeItem, Field(discriminator="type")]


def _scope(scope: Sequence[ScopeItem | dict[str, Any]] | None) -> list[ScopeItem] | None:
    if scope is None:
        return None
    return TypeAdapter(list[ScopeItem]).validate_python(list(scope))


class UserServiceRoles:
    def get(self, id: UUID | str) -> Operation[UserServiceRolesResponse]:
        return Operation(
            "GET",
            "/api/v1/user_service_roles/{id}",
            adapter=TypeAdapter(UserServiceRolesResponse),
            path_params={"id": id},
        )

    def create(
        self,
        *,
        user_id: UUID | str,
        service_roles_id: UUID | str,
        scope: Sequence[ScopeItem | dict[str, Any]] | None = None,
    ) -> Operation[UserServiceRolesResponse]:
        body = UserServiceRolesCreate(
            user_id=as_uuid(user_id),
            service_roles_id=as_uuid(service_roles_id),
            scope=_scope(scope),
        )
        return Operation(
            "POST",
            "/api/v1/user_service_roles",
            adapter=TypeAdapter(UserServiceRolesResponse),
            json=dump(body),
        )

    def update(
        self,
        id: UUID | str,
        *,
        user_id: UUID | str,
        service_roles_id: UUID | str,
        scope: Sequence[ScopeItem | dict[str, Any]] | None = None,
    ) -> Operation[UserServiceRolesResponse]:
        body = UserServiceRolesUpdate(
            id=UUID(str(id)),
            user_id=UUID(str(user_id)),
            service_roles_id=UUID(str(service_roles_id)),
            scope=_scope(scope),
        )
        return Operation(
            "PATCH",
            "/api/v1/user_service_roles",
            adapter=TypeAdapter(UserServiceRolesResponse),
            json=dump(body),
        )

    def delete(self, id: UUID | str) -> Operation[str]:
        return Operation(
            "DELETE",
            "/api/v1/user_service_roles/{id}",
            adapter=TypeAdapter(str),
            path_params={"id": id},
        )
