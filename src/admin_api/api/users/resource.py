from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import TypeAdapter

from admin_api.api.common import Page, dump, page_params
from admin_api.api.dto import (
    AccountType,
    AuthChallengeResponse,
    EmailLogin,
    LinkMplkRequest,
    MplkLogin,
    PasswordLogin,
    SortOrder,
    UserAccountsResponse,
    UserAssignService,
    UserAuthData,
    UserCreateResponse,
    UserGetByFiltersRequest,
    UserGetRolesFromServiceResp,
    UserLogoutRequest,
    UserRevokeService,
    UserSignUp,
    UserSortFieldName,
    VerificationAuthCode,
)
from admin_api.api.request import Operation
from admin_api.api.users.schemas import (
    Account,
    FullUser,
    LoginCredentials,
    ManagedServices,
    UserEntity,
    UserPermissions,
)


class Users:
    def get_me(self) -> Operation[FullUser]:
        return Operation("GET", "/api/v1/users/me", adapter=TypeAdapter(FullUser))

    def get_permissions(self, service_name: str) -> Operation[UserPermissions]:
        return Operation(
            "GET",
            "/api/v1/users/permissions",
            adapter=TypeAdapter(UserPermissions),
            params={"service_name": service_name},
        )

    def get(self, id: UUID | str) -> Operation[FullUser]:
        return Operation(
            "GET",
            "/api/v1/users/{id}",
            adapter=TypeAdapter(FullUser),
            path_params={"id": id},
        )

    def delete(self, id: UUID | str) -> Operation[str]:
        return Operation(
            "DELETE",
            "/api/v1/users/{id}",
            adapter=TypeAdapter(str),
            path_params={"id": id},
        )

    def filter(
        self,
        *,
        email: str | None = None,
        service_name: str | None = None,
        service_role: str | None = None,
        role: AccountType | list[AccountType] | None = None,
        can_manage_services: bool | None = None,
        page: int = 1,
        size: int = 10,
        sort_by: UserSortFieldName | None = None,
        sort_order: SortOrder = SortOrder.DESC,
    ) -> Operation[Page[UserEntity]]:
        body = UserGetByFiltersRequest(
            email=email,
            service_name=service_name,
            service_role=service_role,
            role=role,
            can_manage_services=can_manage_services,
        )
        return Operation(
            "POST",
            "/api/v1/users/filters",
            adapter=TypeAdapter(Page[UserEntity]),
            params=page_params(page, size, sort_by, sort_order),
            json=dump(body),
        )

    def get_roles_from_service(self, id: UUID | str, service_name: str) -> Operation[UserGetRolesFromServiceResp]:
        return Operation(
            "POST",
            "/api/v1/users/{id}/get_roles_from_service",
            adapter=TypeAdapter(UserGetRolesFromServiceResp),
            path_params={"id": id},
            params={"service_name": service_name},
        )

    def get_accounts(self) -> Operation[UserAccountsResponse]:
        return Operation("GET", "/api/v1/users/accounts", adapter=TypeAdapter(UserAccountsResponse))

    def activate_account(self, account_id: UUID | str) -> Operation[Account]:
        return Operation(
            "PATCH",
            "/api/v1/users/accounts/{account_id}/activate",
            adapter=TypeAdapter(Account),
            path_params={"account_id": account_id},
        )

    def get_managed_services(self) -> Operation[ManagedServices]:
        return Operation(
            "POST",
            "/api/v1/users/managed-services",
            adapter=TypeAdapter(ManagedServices),
        )

    def assign_service(self, user_id: UUID | str, service_id: UUID | str) -> Operation[None]:
        body = UserAssignService(user_id=UUID(str(user_id)), service_id=UUID(str(service_id)))
        return Operation(
            "POST",
            "/api/v1/users/assign-service",
            adapter=TypeAdapter(None),
            json=dump(body),
        )

    def revoke_service(self, user_id: UUID | str, service_id: UUID | str) -> Operation[None]:
        body = UserRevokeService(user_id=UUID(str(user_id)), service_id=UUID(str(service_id)))
        return Operation(
            "POST",
            "/api/v1/users/revoke-service",
            adapter=TypeAdapter(None),
            json=dump(body),
        )

    def link_mplk(self, login: str, password: str) -> Operation[UserAuthData]:
        body = LinkMplkRequest(login=login, raw_password=password)
        return Operation(
            "POST",
            "/api/v1/users/link-mplk",
            adapter=TypeAdapter(UserAuthData),
            json=dump(body),
        )

    def login(self, credentials: LoginCredentials | dict[str, Any]) -> Operation[AuthChallengeResponse]:
        validated: EmailLogin | PasswordLogin | MplkLogin = TypeAdapter(LoginCredentials).validate_python(credentials)
        return Operation(
            "POST",
            "/api/v1/users/login",
            adapter=TypeAdapter(AuthChallengeResponse),
            auth=False,
            json=dump(validated),
        )

    def login_by_password(self, email: str, password: str) -> Operation[AuthChallengeResponse]:
        return self.login(PasswordLogin(type="password", email=email, raw_password=password))

    def login_by_email(self, email: str) -> Operation[AuthChallengeResponse]:
        return self.login(EmailLogin(type="email", email=email))

    def login_by_mplk(self, login: str, password: str) -> Operation[AuthChallengeResponse]:
        return self.login(MplkLogin(type="mplk", login=login, raw_password=password))

    def verify_auth_code(self, pre_auth_token: str, code: str | None = None) -> Operation[UserAuthData]:
        body = VerificationAuthCode(pre_auth_token=pre_auth_token, code=code)
        return Operation(
            "POST",
            "/api/v1/users/verification_auth_code",
            adapter=TypeAdapter(UserAuthData),
            auth=False,
            json=dump(body),
        )

    def refresh(self, auth_data: UserAuthData) -> Operation[UserAuthData]:
        return Operation(
            "POST",
            "/api/v1/users/refresh",
            adapter=TypeAdapter(UserAuthData),
            auth=False,
            json=dump(auth_data),
        )

    def logout(self, refresh_token: UUID | str) -> Operation[str]:
        body = UserLogoutRequest(refresh_token=UUID(str(refresh_token)))
        return Operation(
            "POST",
            "/api/v1/users/logout",
            adapter=TypeAdapter(str),
            json=dump(body),
        )

    def sign_up(
        self,
        *,
        name: str,
        surname: str,
        patronymic: str,
        email: str,
        password: str,
    ) -> Operation[UserCreateResponse]:
        body = UserSignUp(
            name=name,
            surname=surname,
            patronymic=patronymic,
            email=email,
            raw_password=password,
        )
        return Operation(
            "POST",
            "/api/v1/users/sign-up",
            adapter=TypeAdapter(UserCreateResponse),
            auth=False,
            json=dump(body),
        )
