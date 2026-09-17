from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from admin_api.api.dto import UnitScopeResponse, UnitTypeScopeResponse


class User(BaseModel):
    id: UUID
    external_id: str | None = None
    role: str
    external_role: str | None = None
    type_: str | None = None
    name: str
    surname: str
    patronymic: str
    email: str
    faculty: str | None = None
    login: str
    last_login: datetime | None = None
    created_at: datetime
    sex: str | None = None
    study_status: str | None = None
    degree_level: str | None = None
    study_group: str | None = None
    specialization: str | None = None
    finance: str | None = None
    form: str | None = None
    enter_year: str | None = None
    course: str | None = None
    department_code: str | None = None
    photo_url: str | None = None

    @property
    def fullname(self) -> str:
        parts = (self.surname, self.name, self.patronymic)
        return " ".join(part for part in parts if part).strip()


FullUser = User

Scope = Annotated[
    UnitScopeResponse | UnitTypeScopeResponse,
    Field(discriminator="type"),
]
UserPermissions = dict[str, list[Scope]]
