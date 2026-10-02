from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import TypeAdapter

from admin_api.api.request import Operation
from admin_api.api.service_roles.schemas import (
    ServiceRoleGetByFiltersRequest,
    ServiceRolesAssignPermission,
    ServiceRolesCreate,
    ServiceRolesPaginatedResponse,
    ServiceRolesPermissionsResponse,
    ServiceRolesResponse,
    ServiceRolesRevokePermission,
    ServiceRolesUpdate,
)


class ServiceRoles:
    def get_by_filters(
        self,
        filters: ServiceRoleGetByFiltersRequest | None = None,
        *,
        page: int = 1,
        size: int = 10,
        sort_by: Literal["id"] | None = None,
        sort_order: Literal["ASC", "DESC"] = "DESC",
    ) -> Operation[ServiceRolesPaginatedResponse]:
        return Operation(
            "POST",
            "/api/v1/service-roles/filters",
            adapter=TypeAdapter(ServiceRolesPaginatedResponse),
            params={"page": page, "size": size, "sort_by": sort_by, "sort_order": sort_order},
            json=filters.model_dump(mode="json", exclude_none=True) if filters else {},
        )

    def get_by_id(self, service_role_id: UUID | str) -> Operation[ServiceRolesResponse]:
        return Operation(
            "GET",
            "/api/v1/service-roles/{service_role_id}",
            adapter=TypeAdapter(ServiceRolesResponse),
            path_params={"service_role_id": service_role_id},
        )

    def create(self, role: ServiceRolesCreate) -> Operation[ServiceRolesResponse]:
        return Operation(
            "POST",
            "/api/v1/service-roles",
            adapter=TypeAdapter(ServiceRolesResponse),
            json=role.model_dump(mode="json"),
        )

    def update(self, role: ServiceRolesUpdate) -> Operation[None]:
        return Operation(
            "PATCH",
            "/api/v1/service-roles",
            adapter=TypeAdapter(type(None)),
            json=role.model_dump(mode="json"),
        )

    def delete(self, service_role_id: UUID | str) -> Operation[str]:
        return Operation(
            "DELETE",
            "/api/v1/service-roles/{service_role_id}",
            adapter=TypeAdapter(str),
            path_params={"service_role_id": service_role_id},
        )

    def get_permissions(self, service_role_id: UUID | str) -> Operation[ServiceRolesPermissionsResponse]:
        return Operation(
            "GET",
            "/api/v1/service-roles/{service_role_id}/permissions",
            adapter=TypeAdapter(ServiceRolesPermissionsResponse),
            path_params={"service_role_id": service_role_id},
        )

    def assign_permission(self, assignment: ServiceRolesAssignPermission) -> Operation[str]:
        return Operation(
            "POST",
            "/api/v1/service-roles/assign-permission",
            adapter=TypeAdapter(str),
            json=assignment.model_dump(mode="json"),
        )

    def revoke_permission(self, assignment: ServiceRolesRevokePermission) -> Operation[str]:
        return Operation(
            "POST",
            "/api/v1/service-roles/revoke-permission",
            adapter=TypeAdapter(str),
            json=assignment.model_dump(mode="json"),
        )
