from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class UnitScopeItem(BaseModel):
    type: Literal["unit"] = "unit"
    unit_id: UUID


class UnitTypeScopeItem(BaseModel):
    type: Literal["unit_type"] = "unit_type"
    unit_type_id: UUID


ScopeItem = Annotated[UnitScopeItem | UnitTypeScopeItem, Field(discriminator="type")]


class UnitScopeResponse(UnitScopeItem):
    id: UUID


class UnitTypeScopeResponse(UnitTypeScopeItem):
    id: UUID


Scope = Annotated[UnitScopeResponse | UnitTypeScopeResponse, Field(discriminator="type")]
