from __future__ import annotations

from uuid import UUID

from pydantic import TypeAdapter

from admin_api.api.request import Operation
from admin_api.api.units.schemas import UnitGet, UnitResponse, UnitTreeResponse


class Units:
    def get_all(
        self,
        *,
        flat: bool = False,
        max_depth: int | None = None,
        root_id: UUID | None = None,
        search: str | None = None,
        type_ids: list[UUID] | None = None,
    ) -> Operation[list[UnitResponse] | list[UnitTreeResponse]]:
        options = UnitGet(
            flat=flat,
            max_depth=max_depth,
            root_id=root_id,
            search=search,
            type_ids=type_ids or [],
        )
        return Operation(
            "GET",
            "/api/v1/units",
            adapter=TypeAdapter(list[UnitTreeResponse] | list[UnitResponse]),
            params={
                "flat": options.flat,
                "max_depth": options.max_depth,
                "root_id": options.root_id,
                "search": options.search,
                "type_ids": options.type_ids or None,
            },
        )
