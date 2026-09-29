from __future__ import annotations

import builtins
from collections.abc import Sequence
from uuid import UUID

from pydantic import BaseModel, TypeAdapter

from admin_api.api.dto import UnitType
from admin_api.api.request import Operation


class Unit(BaseModel):
    id: UUID
    title: str
    type: UnitType | None = None
    parent_unit_id: UUID | None = None
    has_children: bool


class UnitTree(Unit):
    children: list[UnitTree] = []


class Units:
    def list(
        self,
        *,
        root_id: UUID | str | None = None,
        search: str | None = None,
        type_ids: Sequence[UUID | str] | None = None,
        max_depth: int | None = None,
    ) -> Operation[list[UnitTree]]:
        return Operation(
            "GET",
            "/api/v1/units",
            adapter=TypeAdapter(list[UnitTree]),
            params=self._params(False, root_id, search, type_ids, max_depth),
        )

    def list_flat(
        self,
        *,
        root_id: UUID | str | None = None,
        search: str | None = None,
        type_ids: Sequence[UUID | str] | None = None,
        max_depth: int | None = None,
    ) -> Operation[builtins.list[Unit]]:
        return Operation(
            "GET",
            "/api/v1/units",
            adapter=TypeAdapter(list[Unit]),
            params=self._params(True, root_id, search, type_ids, max_depth),
        )

    def get_types(self) -> Operation[builtins.list[UnitType]]:
        return Operation("GET", "/api/v1/unit-types", adapter=TypeAdapter(list[UnitType]))

    @staticmethod
    def _params(
        flat: bool,
        root_id: UUID | str | None,
        search: str | None,
        type_ids: Sequence[UUID | str] | None,
        max_depth: int | None,
    ) -> dict[str, object]:
        return {
            "flat": flat,
            "root_id": None if root_id is None else str(root_id),
            "search": search,
            "type_ids": [str(type_id) for type_id in type_ids] if type_ids else None,
            "max_depth": max_depth,
        }
