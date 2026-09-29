from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel

from admin_api.api.dto import SortOrder

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    data: list[T]
    page: int
    size: int
    total: int


def as_uuid(value: UUID | str | None) -> UUID | None:
    return None if value is None else UUID(str(value))


def dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json", exclude_none=True)


def page_params(
    page: int,
    size: int,
    sort_by: str | None,
    sort_order: SortOrder | str | None,
) -> dict[str, Any]:
    return {
        "page": page,
        "size": size,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }
