from __future__ import annotations

from uuid import UUID

from pydantic import TypeAdapter

from admin_api.api.request import Operation
from admin_api.api.user_service_roles.schemas import (
    UserServiceRolesCreate,
    UserServiceRolesResponse,
    UserServiceRolesUpdate,
)


class UserServiceRoles:
    def get_by_id(self, assignment_id: UUID | str) -> Operation[UserServiceRolesResponse]:
        return Operation(
            "GET",
            "/api/v1/user_service_roles/{assignment_id}",
            adapter=TypeAdapter(UserServiceRolesResponse),
            path_params={"assignment_id": assignment_id},
        )

    def create(self, assignment: UserServiceRolesCreate) -> Operation[UserServiceRolesResponse]:
        return Operation(
            "POST",
            "/api/v1/user_service_roles",
            adapter=TypeAdapter(UserServiceRolesResponse),
            json=assignment.model_dump(mode="json"),
        )

    def update(self, assignment: UserServiceRolesUpdate) -> Operation[UserServiceRolesResponse]:
        return Operation(
            "PATCH",
            "/api/v1/user_service_roles",
            adapter=TypeAdapter(UserServiceRolesResponse),
            json=assignment.model_dump(mode="json"),
        )

    def delete(self, assignment_id: UUID | str) -> Operation[str]:
        return Operation(
            "DELETE",
            "/api/v1/user_service_roles/{assignment_id}",
            adapter=TypeAdapter(str),
            path_params={"assignment_id": assignment_id},
        )
