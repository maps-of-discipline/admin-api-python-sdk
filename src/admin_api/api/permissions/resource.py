from __future__ import annotations

from uuid import UUID

from pydantic import TypeAdapter

from admin_api.api.common import Page, dump, page_params
from admin_api.api.dto import (
    PermissionCreate,
    PermissionGetByFiltersRequest,
    PermissionResponse,
    PermissionSortFieldName,
    PermissionUpdate,
    SortOrder,
)
from admin_api.api.request import Operation


class Permissions:
    def get(self, id: UUID | str) -> Operation[PermissionResponse]:
        return Operation(
            "GET",
            "/api/v1/permission/{id}",
            adapter=TypeAdapter(PermissionResponse),
            path_params={"id": id},
        )

    def filter(
        self,
        *,
        service_name: str | None = None,
        page: int = 1,
        size: int = 10,
        sort_by: PermissionSortFieldName | None = None,
        sort_order: SortOrder = SortOrder.DESC,
    ) -> Operation[Page[PermissionResponse]]:
        return Operation(
            "POST",
            "/api/v1/permission/filters",
            adapter=TypeAdapter(Page[PermissionResponse]),
            params=page_params(page, size, sort_by, sort_order),
            json=dump(PermissionGetByFiltersRequest(service_name=service_name)),
        )

    def create(self, *, service_id: UUID | str, title: str, verbose_name: str) -> Operation[PermissionResponse]:
        body = PermissionCreate(service_id=UUID(str(service_id)), title=title, verbose_name=verbose_name)
        return Operation(
            "POST",
            "/api/v1/permission",
            adapter=TypeAdapter(PermissionResponse),
            json=dump(body),
        )

    def update(
        self,
        id: UUID | str,
        *,
        service_id: UUID | str,
        title: str,
        verbose_name: str,
    ) -> Operation[PermissionResponse]:
        body = PermissionUpdate(
            id=UUID(str(id)),
            service_id=UUID(str(service_id)),
            title=title,
            verbose_name=verbose_name,
        )
        return Operation(
            "PATCH",
            "/api/v1/permission",
            adapter=TypeAdapter(PermissionResponse),
            json=dump(body),
        )

    def delete(self, id: UUID | str) -> Operation[str]:
        return Operation(
            "DELETE",
            "/api/v1/permission/{id}",
            adapter=TypeAdapter(str),
            path_params={"id": id},
        )
