from __future__ import annotations

from uuid import UUID

from pydantic import TypeAdapter

from admin_api.api.request import Operation
from admin_api.api.users.schemas import (
    FullUser,
    SortOrder,
    UserGetByFiltersRequest,
    UserPermissions,
    UserSortFieldName,
    UsersPaginatedResponse,
)


class Users:
    def get_me(self) -> Operation[FullUser]:
        return Operation("GET", "/api/v1/users/me", adapter=TypeAdapter(FullUser))

    def get_by_id(self, user_id: UUID | str) -> Operation[FullUser]:
        return Operation(
            "GET",
            "/api/v1/users/{user_id}",
            adapter=TypeAdapter(FullUser),
            path_params={"user_id": user_id},
        )

    def get_by_filters(
        self,
        filters: UserGetByFiltersRequest,
        *,
        page: int = 1,
        size: int = 10,
        sort_by: UserSortFieldName | None = None,
        sort_order: SortOrder = SortOrder.DESC,
    ) -> Operation[UsersPaginatedResponse]:
        return Operation(
            "POST",
            "/api/v1/users/filters",
            adapter=TypeAdapter(UsersPaginatedResponse),
            params={"page": page, "size": size, "sort_by": sort_by, "sort_order": sort_order},
            json=filters.model_dump(mode="json", exclude_none=True),
        )

    def get_permissions(self, service_name: str) -> Operation[UserPermissions]:
        return Operation(
            "GET",
            "/api/v1/users/permissions",
            adapter=TypeAdapter(UserPermissions),
            params={"service_name": service_name},
        )
