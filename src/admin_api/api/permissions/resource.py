from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import TypeAdapter

from admin_api.api.permissions.schemas import (
    PermissionCreate,
    PermissionGetByFiltersRequest,
    PermissionPaginatedResponse,
    PermissionResponse,
    PermissionUpdate,
)
from admin_api.api.request import Operation


class Permissions:
    def get_by_filters(
        self,
        filters: PermissionGetByFiltersRequest | None = None,
        *,
        page: int = 1,
        size: int = 10,
        sort_by: Literal["id"] | None = None,
        sort_order: Literal["ASC", "DESC"] = "DESC",
    ) -> Operation[PermissionPaginatedResponse]:
        return Operation(
            "POST",
            "/api/v1/permission/filters",
            adapter=TypeAdapter(PermissionPaginatedResponse),
            params={"page": page, "size": size, "sort_by": sort_by, "sort_order": sort_order},
            json=filters.model_dump(mode="json", exclude_none=True) if filters else {},
        )

    def get_by_id(self, permission_id: UUID | str) -> Operation[PermissionResponse]:
        return Operation(
            "GET",
            "/api/v1/permission/{permission_id}",
            adapter=TypeAdapter(PermissionResponse),
            path_params={"permission_id": permission_id},
        )

    def create(self, permission: PermissionCreate) -> Operation[PermissionResponse]:
        return Operation(
            "POST",
            "/api/v1/permission",
            adapter=TypeAdapter(PermissionResponse),
            json=permission.model_dump(mode="json"),
        )

    def update(self, permission: PermissionUpdate) -> Operation[PermissionResponse]:
        return Operation(
            "PATCH",
            "/api/v1/permission",
            adapter=TypeAdapter(PermissionResponse),
            json=permission.model_dump(mode="json"),
        )

    def delete(self, permission_id: UUID | str) -> Operation[str]:
        return Operation(
            "DELETE",
            "/api/v1/permission/{permission_id}",
            adapter=TypeAdapter(str),
            path_params={"permission_id": permission_id},
        )
