from __future__ import annotations

import re
from uuid import UUID

from pydantic import BaseModel, field_validator

DEFAULT_SERVICE_ICON = "mdi-briefcase-outline"
DEFAULT_SERVICE_COLOR = "#4B6EB9"
_HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _validate_icon(value: str) -> str:
    icon = value.strip()
    if not icon:
        raise ValueError("icon must not be empty")
    return icon


def _validate_color(value: str) -> str:
    color = value.strip()
    if not _HEX_COLOR_PATTERN.fullmatch(color):
        raise ValueError("color must be #RRGGBB hexadecimal")
    return color.upper()


class ServiceGetByFiltersRequest(BaseModel):
    service_name: str | None = None


class ServiceCreate(BaseModel):
    name: str
    verbose_name: str | None = None
    icon: str = DEFAULT_SERVICE_ICON
    color: str = DEFAULT_SERVICE_COLOR

    @field_validator("icon")
    @classmethod
    def validate_icon(cls, value: str) -> str:
        return _validate_icon(value)

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        return _validate_color(value)


class ServiceUpdate(BaseModel):
    id: UUID
    name: str
    verbose_name: str | None = None


class ServiceIconUpdate(BaseModel):
    id: UUID
    icon: str

    @field_validator("icon")
    @classmethod
    def validate_icon(cls, value: str) -> str:
        return _validate_icon(value)


class ServiceColorUpdate(BaseModel):
    id: UUID
    color: str

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        return _validate_color(value)


class ServiceResponse(BaseModel):
    id: UUID | None = None
    name: str
    verbose_name: str | None = None
    icon: str = DEFAULT_SERVICE_ICON
    color: str = DEFAULT_SERVICE_COLOR


class ServicesPaginatedResponse(BaseModel):
    data: list[ServiceResponse]
    page: int
    size: int
    total: int
