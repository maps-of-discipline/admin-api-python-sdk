from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import TypeAdapter

from admin_api.api.common import as_uuid, dump
from admin_api.api.dto import (
    AssignmentRuleCreate,
    AssignmentRuleResponse,
    AssignmentRuleUpdate,
    ScopeTemplate,
)
from admin_api.api.request import Operation


class AssignmentRules:
    def get(self, id: UUID | str) -> Operation[AssignmentRuleResponse]:
        return Operation(
            "GET",
            "/api/v1/assignment-rules/{id}",
            adapter=TypeAdapter(AssignmentRuleResponse),
            path_params={"id": id},
        )

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        service_role_id: UUID | str | None = None,
    ) -> Operation[list[AssignmentRuleResponse]]:
        return Operation(
            "GET",
            "/api/v1/assignment-rules",
            adapter=TypeAdapter(list[AssignmentRuleResponse]),
            params={
                "limit": limit,
                "offset": offset,
                "service_role_id": None if service_role_id is None else str(service_role_id),
            },
        )

    def get_metadata(self) -> Operation[dict[str, Any]]:
        return Operation(
            "GET",
            "/api/v1/assignment-rules/metadata",
            adapter=TypeAdapter(dict[str, Any]),
            auth=False,
        )

    def create(
        self,
        *,
        title: str,
        service_role_id: UUID | str,
        expression: Any,
        enabled: bool = True,
        scope_template: ScopeTemplate | str = ScopeTemplate.unscoped,
    ) -> Operation[AssignmentRuleResponse]:
        body = AssignmentRuleCreate.model_validate(
            {
                "title": title,
                "service_role_id": service_role_id,
                "expression": expression,
                "enabled": enabled,
                "scope_template": scope_template,
            },
        )
        return Operation(
            "POST",
            "/api/v1/assignment-rules",
            adapter=TypeAdapter(AssignmentRuleResponse),
            json=dump(body),
        )

    def update(
        self,
        id: UUID | str,
        *,
        title: str | None = None,
        service_role_id: UUID | str | None = None,
        expression: Any = None,
        enabled: bool | None = None,
        scope_template: ScopeTemplate | str | None = None,
    ) -> Operation[AssignmentRuleResponse]:
        body = AssignmentRuleUpdate.model_validate(
            {
                "id": id,
                "title": title,
                "service_role_id": as_uuid(service_role_id),
                "expression": expression,
                "enabled": enabled,
                "scope_template": scope_template,
            },
        )
        return Operation(
            "PATCH",
            "/api/v1/assignment-rules/{id}",
            adapter=TypeAdapter(AssignmentRuleResponse),
            path_params={"id": id},
            json=dump(body),
        )

    def delete(self, id: UUID | str) -> Operation[None]:
        return Operation(
            "DELETE",
            "/api/v1/assignment-rules/{id}",
            adapter=TypeAdapter(None),
            path_params={"id": id},
        )
