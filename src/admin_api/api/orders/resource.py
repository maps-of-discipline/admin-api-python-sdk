from __future__ import annotations

from uuid import UUID

from pydantic import TypeAdapter

from admin_api.api.common import as_uuid, dump
from admin_api.api.dto import (
    OrderApprove,
    OrderCreate,
    OrderList,
    OrderResponse,
    OrderUpdate,
    TargetRole,
)
from admin_api.api.request import Operation


class Orders:
    def get(self, id: UUID | str) -> Operation[OrderResponse]:
        return Operation(
            "GET",
            "/api/v1/orders/{id}",
            adapter=TypeAdapter(OrderResponse),
            path_params={"id": id},
        )

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        service_id: UUID | str | None = None,
    ) -> Operation[list[OrderResponse]]:
        body = OrderList(limit=limit, offset=offset, service_id=as_uuid(service_id))
        return Operation(
            "POST",
            "/api/v1/orders/list",
            adapter=TypeAdapter(list[OrderResponse]),
            json=dump(body),
        )

    def create(
        self,
        *,
        target_role: TargetRole | str,
        comment: str,
        user_id: UUID | str | None = None,
        service_id: UUID | str | None = None,
    ) -> Operation[OrderResponse]:
        body = OrderCreate(
            target_role=TargetRole(target_role),
            comment=comment,
            user_id=as_uuid(user_id),
            service_id=as_uuid(service_id),
        )
        return Operation(
            "POST",
            "/api/v1/orders",
            adapter=TypeAdapter(OrderResponse),
            json=dump(body),
        )

    def update(
        self,
        id: UUID | str,
        *,
        target_role: TargetRole | str,
        comment: str,
        user_id: UUID | str | None = None,
        service_id: UUID | str | None = None,
    ) -> Operation[OrderResponse | None]:
        """Admin API currently answers with an empty body (null); the model is returned once it is fixed."""
        body = OrderUpdate(
            id=UUID(str(id)),
            target_role=TargetRole(target_role),
            comment=comment,
            user_id=as_uuid(user_id),
            service_id=as_uuid(service_id),
        )
        return Operation(
            "PATCH",
            "/api/v1/orders",
            adapter=TypeAdapter(OrderResponse | None),
            json=dump(body),
        )

    def approve(self, id: UUID | str, approve: bool = True) -> Operation[None]:
        return Operation(
            "POST",
            "/api/v1/orders/approve",
            adapter=TypeAdapter(None),
            json=dump(OrderApprove(id=UUID(str(id)), approve=approve)),
        )

    def delete(self, id: UUID | str) -> Operation[str]:
        return Operation(
            "DELETE",
            "/api/v1/orders/{id}",
            adapter=TypeAdapter(str),
            path_params={"id": id},
        )
