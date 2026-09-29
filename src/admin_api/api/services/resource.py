from __future__ import annotations

from uuid import UUID

from pydantic import TypeAdapter

from admin_api.api.common import Page, dump, page_params
from admin_api.api.dto import (
    ServiceColorUpdate,
    ServiceCreate,
    ServiceGetByFiltersRequest,
    ServiceIconUpdate,
    ServiceResponse,
    ServiceSortFieldName,
    ServiceUpdate,
    SortOrder,
)
from admin_api.api.request import Operation


class Services:
    def get(self, id: UUID | str) -> Operation[ServiceResponse]:
        return Operation(
            "GET",
            "/api/v1/services/{id}",
            adapter=TypeAdapter(ServiceResponse),
            path_params={"id": id},
        )

    def filter(
        self,
        *,
        service_name: str | None = None,
        page: int = 1,
        size: int = 10,
        sort_by: ServiceSortFieldName | None = None,
        sort_order: SortOrder = SortOrder.DESC,
    ) -> Operation[Page[ServiceResponse]]:
        return Operation(
            "POST",
            "/api/v1/services/filters",
            adapter=TypeAdapter(Page[ServiceResponse]),
            params=page_params(page, size, sort_by, sort_order),
            json=dump(ServiceGetByFiltersRequest(service_name=service_name)),
        )

    def create(
        self,
        *,
        name: str,
        verbose_name: str | None = None,
        icon: str | None = None,
        color: str | None = None,
    ) -> Operation[ServiceResponse]:
        body = ServiceCreate(name=name, verbose_name=verbose_name, icon=icon, color=color)
        return Operation(
            "POST",
            "/api/v1/services",
            adapter=TypeAdapter(ServiceResponse),
            json=dump(body),
        )

    def update(self, id: UUID | str, *, name: str, verbose_name: str | None = None) -> Operation[ServiceResponse]:
        body = ServiceUpdate(id=UUID(str(id)), name=name, verbose_name=verbose_name)
        return Operation(
            "PATCH",
            "/api/v1/services",
            adapter=TypeAdapter(ServiceResponse),
            json=dump(body),
        )

    def update_icon(self, id: UUID | str, icon: str) -> Operation[ServiceResponse]:
        return Operation(
            "PATCH",
            "/api/v1/services/branding/icon",
            adapter=TypeAdapter(ServiceResponse),
            json=dump(ServiceIconUpdate(id=UUID(str(id)), icon=icon)),
        )

    def update_color(self, id: UUID | str, color: str) -> Operation[ServiceResponse]:
        return Operation(
            "PATCH",
            "/api/v1/services/branding/color",
            adapter=TypeAdapter(ServiceResponse),
            json=dump(ServiceColorUpdate(id=UUID(str(id)), color=color)),
        )

    def delete(self, id: UUID | str) -> Operation[str]:
        return Operation(
            "DELETE",
            "/api/v1/services/{id}",
            adapter=TypeAdapter(str),
            path_params={"id": id},
        )
