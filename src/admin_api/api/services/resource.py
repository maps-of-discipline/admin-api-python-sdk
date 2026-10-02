from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import TypeAdapter

from admin_api.api.request import Operation
from admin_api.api.services.schemas import (
    ServiceColorUpdate,
    ServiceCreate,
    ServiceGetByFiltersRequest,
    ServiceIconUpdate,
    ServiceResponse,
    ServicesPaginatedResponse,
    ServiceUpdate,
)


class Services:
    def get_by_filters(
        self,
        filters: ServiceGetByFiltersRequest | None = None,
        *,
        page: int = 1,
        size: int = 10,
        sort_by: Literal["id"] | None = None,
        sort_order: Literal["ASC", "DESC"] = "DESC",
    ) -> Operation[ServicesPaginatedResponse]:
        return Operation(
            "POST",
            "/api/v1/services/filters",
            adapter=TypeAdapter(ServicesPaginatedResponse),
            params={"page": page, "size": size, "sort_by": sort_by, "sort_order": sort_order},
            json=filters.model_dump(mode="json", exclude_none=True) if filters else {},
        )

    def get_by_id(self, service_id: UUID | str) -> Operation[ServiceResponse]:
        return Operation(
            "GET",
            "/api/v1/services/{service_id}",
            adapter=TypeAdapter(ServiceResponse),
            path_params={"service_id": service_id},
        )

    def create(self, service: ServiceCreate) -> Operation[ServiceResponse]:
        return Operation(
            "POST",
            "/api/v1/services",
            adapter=TypeAdapter(ServiceResponse),
            json=service.model_dump(mode="json"),
        )

    def update(self, service: ServiceUpdate) -> Operation[ServiceResponse]:
        return Operation(
            "PATCH",
            "/api/v1/services",
            adapter=TypeAdapter(ServiceResponse),
            json=service.model_dump(mode="json"),
        )

    def update_icon(self, service: ServiceIconUpdate) -> Operation[ServiceResponse]:
        return Operation(
            "PATCH",
            "/api/v1/services/branding/icon",
            adapter=TypeAdapter(ServiceResponse),
            json=service.model_dump(mode="json"),
        )

    def update_color(self, service: ServiceColorUpdate) -> Operation[ServiceResponse]:
        return Operation(
            "PATCH",
            "/api/v1/services/branding/color",
            adapter=TypeAdapter(ServiceResponse),
            json=service.model_dump(mode="json"),
        )

    def delete(self, service_id: UUID | str) -> Operation[str]:
        return Operation(
            "DELETE",
            "/api/v1/services/{service_id}",
            adapter=TypeAdapter(str),
            path_params={"service_id": service_id},
        )
