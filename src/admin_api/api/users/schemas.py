from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class MfaMethod(StrEnum):
    none = "none"
    email = "email"


class UserSex(StrEnum):
    male = "Male"
    female = "Female"


class AccountType(StrEnum):
    student = "stud"
    staff = "staff"


class UserSortFieldName(StrEnum):
    id = "id"
    external_id = "external_id"
    role = "role"
    external_role = "external_role"
    name = "name"
    surname = "surname"
    patronymic = "patronymic"
    email = "email"
    login = "login"
    password = "password"
    last_login = "last_login"
    created_at = "created_at"


class SortOrder(StrEnum):
    ASC = "ASC"
    DESC = "DESC"


class UserEmail(BaseModel):
    id: UUID
    email: str
    is_primary: bool
    verified_at: datetime | None


class UnitType(BaseModel):
    id: UUID
    title: str


class ShortUnit(BaseModel):
    id: UUID
    title: str
    type: UnitType


class Position(BaseModel):
    id: UUID
    unit: ShortUnit
    post: str
    job_type: str
    wage: float
    category: str
    status: str
    address: str
    room: str
    phone_inner: str
    phone_direct: str


class StudentAccount(BaseModel):
    id: UUID
    account_type: Literal["stud"] = "stud"
    mplk_user_id: int
    status: str
    course: int
    code: str
    study_group: str
    vacation_start: datetime | None
    vacation_end: datetime | None
    speciality: str
    specialization: str
    degree_length: str
    degree_length_standart: str
    education_form: str
    finance: str
    degree_level: str
    enter_year: str
    pass_expire_date: datetime | None
    pass_expired: bool
    last_access: date
    faculty: ShortUnit


class StaffAccount(BaseModel):
    id: UUID
    account_type: Literal["staff"] = "staff"
    mplk_user_id: int
    email_staff: str | None
    phone_staff: str | None
    allow_mobphone_in: bool
    allow_mobphone_out: bool
    positions: list[Position]


Account = Annotated[StudentAccount | StaffAccount, Field(discriminator="account_type")]


class User(BaseModel):
    id: UUID
    mfa_method: MfaMethod
    last_active_account_id: UUID | None
    last_login_at: datetime | None
    emails: list[UserEmail]
    fullname: str


class NaturalUser(User):
    kind: Literal["natural"] = "natural"
    mplk_individual_guid: UUID | None
    name: str | None
    surname: str | None
    patronymic: str | None
    sex: UserSex | None
    birthday: date | None
    phone: str | None
    photo_url: str | None


class OrganizationalUser(User):
    kind: Literal["organizational"] = "organizational"
    display_name: str


UserEntity = Annotated[NaturalUser | OrganizationalUser, Field(discriminator="kind")]


class UserGetByFiltersRequest(BaseModel):
    email: str | None = None
    service_name: str | None = None
    service_role: str | None = None
    role: AccountType | list[AccountType] | None = None
    can_manage_services: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def strip_empty_values(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {key: value for key, value in data.items() if value is not None and value != "" and value != []}
        return data


class UsersPaginatedResponse(BaseModel):
    data: list[UserEntity]
    page: int
    size: int
    total: int


class FullNaturalUser(NaturalUser):
    accounts: list[Account]


class FullOrganizationalUser(OrganizationalUser):
    units: list[ShortUnit]


FullUser = Annotated[FullNaturalUser | FullOrganizationalUser, Field(discriminator="kind")]


class UnitScopeResponse(BaseModel):
    id: UUID
    type: Literal["unit"] = "unit"
    unit_id: UUID


class UnitTypeScopeResponse(BaseModel):
    id: UUID
    type: Literal["unit_type"] = "unit_type"
    unit_type_id: UUID


Scope = Annotated[UnitScopeResponse | UnitTypeScopeResponse, Field(discriminator="type")]
UserPermissions = dict[str, list[Scope]]
