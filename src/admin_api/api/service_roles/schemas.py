from __future__ import annotations

from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field


class ServiceRoleGetByFiltersRequest(BaseModel):
    service_name: str | None = None


class ServiceRolesCreate(BaseModel):
    service_id: UUID | None = None
    role: str
    verbose_name: str | None = None


class ServiceRolesUpdate(ServiceRolesCreate):
    id: UUID


class ServiceRolesResponse(BaseModel):
    id: UUID
    service_id: UUID | None = None
    role: str
    verbose_name: str | None = None
    permanent: bool = False


class ServiceRolesPaginatedResponse(BaseModel):
    data: list[ServiceRolesResponse]
    page: int
    size: int
    total: int


class ServiceRolesPermissionDto(BaseModel):
    permission_id: UUID
    service_role_id: UUID = Field(validation_alias=AliasChoices("service_role_id", "service_roles_id"))


class ServiceRolesAssignPermission(ServiceRolesPermissionDto):
    pass


class ServiceRolesRevokePermission(ServiceRolesPermissionDto):
    pass


class ServiceRolesPermissionsResponse(BaseModel):
    data: list[ServiceRolesPermissionDto]
