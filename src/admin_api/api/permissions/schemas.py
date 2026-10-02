from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class PermissionGetByFiltersRequest(BaseModel):
    service_name: str | None = None


class PermissionCreate(BaseModel):
    service_id: UUID
    title: str
    verbose_name: str


class PermissionUpdate(PermissionCreate):
    id: UUID


class PermissionResponse(BaseModel):
    id: UUID
    service_id: UUID | None
    title: str
    verbose_name: str


class PermissionPaginatedResponse(BaseModel):
    data: list[PermissionResponse]
    page: int
    size: int
    total: int
