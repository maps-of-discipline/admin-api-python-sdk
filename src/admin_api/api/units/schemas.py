from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class UnitType(BaseModel):
    id: UUID
    title: str


class ShortUnit(BaseModel):
    id: UUID
    title: str
    type: UnitType


class UnitGet(BaseModel):
    flat: bool = False
    max_depth: int | None = Field(default=None, ge=1)
    root_id: UUID | None = None
    search: str | None = Field(default=None, min_length=2)
    type_ids: list[UUID] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_lookup_options(self) -> UnitGet:
        if not self.flat and (self.search is not None or self.type_ids):
            raise ValueError("search and type_ids are only supported for flat responses")
        return self


class UnitResponse(BaseModel):
    id: UUID
    title: str
    type: UnitType | None
    parent_unit_id: UUID | None
    has_children: bool


class UnitTreeResponse(UnitResponse):
    children: list[UnitTreeResponse]
