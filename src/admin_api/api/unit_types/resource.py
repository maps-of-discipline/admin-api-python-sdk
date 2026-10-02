from __future__ import annotations

from pydantic import TypeAdapter

from admin_api.api.request import Operation
from admin_api.api.units.schemas import UnitType


class UnitTypes:
    def get_all(self) -> Operation[list[UnitType]]:
        return Operation("GET", "/api/v1/unit-types", adapter=TypeAdapter(list[UnitType]))
