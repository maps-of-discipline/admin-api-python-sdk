from __future__ import annotations

from uuid import UUID

from pydantic import TypeAdapter

from admin_api.api.common import Page, as_uuid, dump, page_params
from admin_api.api.dto import (
    Role,
    ServiceRoleGetByFiltersRequest,
    ServiceRolesAssignPermission,
    ServiceRolesCreate,
    ServiceRoleSortFieldName,
    ServiceRolesPermissionsResponse,
    ServiceRolesResponse,
    ServiceRolesRevokePermission,
    ServiceRolesUpdate,
    SortOrder,
)
from admin_api.api.request import Operation


class ServiceRoles:
    def get(self, id: UUID | str) -> Operation[ServiceRolesResponse]:
        return Operation(
            "GET",
            "/api/v1/service-roles/{id}",
            adapter=TypeAdapter(ServiceRolesResponse),
            path_params={"id": id},
        )

    def filter(
        self,
        *,
        service_name: str | None = None,
        page: int = 1,
        size: int = 10,
        sort_by: ServiceRoleSortFieldName | None = None,
        sort_order: SortOrder = SortOrder.DESC,
    ) -> Operation[Page[ServiceRolesResponse]]:
        return Operation(
            "POST",
            "/api/v1/service-roles/filters",
            adapter=TypeAdapter(Page[ServiceRolesResponse]),
            params=page_params(page, size, sort_by, sort_order),
            json=dump(ServiceRoleGetByFiltersRequest(service_name=service_name)),
        )

    def create(
        self,
        *,
        role: Role | str,
        service_id: UUID | str | None = None,
        verbose_name: str | None = None,
    ) -> Operation[ServiceRolesResponse]:
        body = ServiceRolesCreate(role=Role(role), service_id=as_uuid(service_id), verbose_name=verbose_name)
        return Operation(
            "POST",
            "/api/v1/service-roles",
            adapter=TypeAdapter(ServiceRolesResponse),
            json=dump(body),
        )

    def update(
        self,
        id: UUID | str,
        *,
        role: Role | str,
        service_id: UUID | str | None = None,
        verbose_name: str | None = None,
    ) -> Operation[ServiceRolesResponse | None]:
        """Admin API currently answers with an empty body (null); the model is returned once it is fixed."""
        body = ServiceRolesUpdate(
            id=UUID(str(id)),
            role=Role(role),
            service_id=as_uuid(service_id),
            verbose_name=verbose_name,
        )
        return Operation(
            "PATCH",
            "/api/v1/service-roles",
            adapter=TypeAdapter(ServiceRolesResponse | None),
            json=dump(body),
        )

    def delete(self, id: UUID | str) -> Operation[str]:
        return Operation(
            "DELETE",
            "/api/v1/service-roles/{id}",
            adapter=TypeAdapter(str),
            path_params={"id": id},
        )

    def get_permissions(self, id: UUID | str) -> Operation[ServiceRolesPermissionsResponse]:
        return Operation(
            "GET",
            "/api/v1/service-roles/{id}/permissions",
            adapter=TypeAdapter(ServiceRolesPermissionsResponse),
            path_params={"id": id},
        )

    def assign_permission(self, service_role_id: UUID | str, permission_id: UUID | str) -> Operation[str]:
        body = ServiceRolesAssignPermission(
            service_role_id=UUID(str(service_role_id)),
            permission_id=UUID(str(permission_id)),
        )
        return Operation(
            "POST",
            "/api/v1/service-roles/assign-permission",
            adapter=TypeAdapter(str),
            json=dump(body),
        )

    def revoke_permission(self, service_role_id: UUID | str, permission_id: UUID | str) -> Operation[str]:
        body = ServiceRolesRevokePermission(
            service_role_id=UUID(str(service_role_id)),
            permission_id=UUID(str(permission_id)),
        )
        return Operation(
            "POST",
            "/api/v1/service-roles/revoke-permission",
            adapter=TypeAdapter(str),
            json=dump(body),
        )
