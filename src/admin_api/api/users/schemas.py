from __future__ import annotations

from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from admin_api.api.dto import (
    EmailLogin,
    FullNaturalUser,
    FullOrganizationalUser,
    MplkLogin,
    PasswordLogin,
    StaffAccount,
    StudentAccount,
    UnitScopeResponse,
    UnitTypeScopeResponse,
    User,
    UserSex,
)

FullUser = Annotated[
    FullNaturalUser | FullOrganizationalUser,
    Field(discriminator="kind"),
]
Scope = Annotated[
    UnitScopeResponse | UnitTypeScopeResponse,
    Field(discriminator="type"),
]
UserPermissions = dict[str, list[Scope]]

LoginCredentials = Annotated[
    EmailLogin | PasswordLogin | MplkLogin,
    Field(discriminator="type"),
]
Account = Annotated[
    StaffAccount | StudentAccount,
    Field(discriminator="account_type"),
]


class NaturalUser(User):
    kind: Literal["natural"] = "natural"  # type: ignore[assignment]
    mplk_individual_guid: UUID | None = None
    name: str | None = None
    surname: str | None = None
    patronymic: str | None = None
    sex: UserSex | None = None
    birthday: date | None = None
    phone: str | None = None
    photo_url: str | None = None


class OrganizationalUser(User):
    kind: Literal["organizational"] = "organizational"  # type: ignore[assignment]
    display_name: str


UserEntity = Annotated[
    NaturalUser | OrganizationalUser,
    Field(discriminator="kind"),
]


class ManagedService(BaseModel):
    id: UUID
    name: str
    verbose_name: str | None = None
    icon: str
    color: str


class ManagedServices(BaseModel):
    services: list[ManagedService]
