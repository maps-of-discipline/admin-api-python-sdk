from collections.abc import Callable
from typing import TypeAlias

from admin_api.api.client import SyncApi
from admin_api.api.users.schemas import FullUser, UserPermissions
from admin_api.exceptions import InvalidTokenException, PermissionDenied
from admin_api.permissions.verifier import PermissionVerifier
from admin_api.sdk.auth_context import AuthContext
from admin_api.sdk.token import decode_token_payload

Middleware: TypeAlias = Callable[[AuthContext], dict | None]


class AdminApiAuth:
    def __init__(
        self,
        api: SyncApi | None = None,
        *,
        base_url: str | None = None,
        timeout_ms: int = 300,
        service_name: str | None = None,
    ) -> None:
        if api is None and base_url is not None:
            api = SyncApi(base_url, timeout=timeout_ms / 1000)
        self._root_api = api
        self._timeout_ms = timeout_ms
        self._service_name = service_name
        self._permission_verifiers: list[PermissionVerifier] = []
        self._middlewares: list[Middleware] = []

    def add_permission_verifier(self, verifier: PermissionVerifier) -> None:
        self._permission_verifiers.append(verifier)

    def set_middlewares(self, middlewares: list[Middleware]) -> None:
        self._middlewares = middlewares

    def context_from_token(self, token: str) -> AuthContext[SyncApi]:
        """Build the auth context: profile from admin_api, permissions from the token claims."""
        if self._root_api is None:
            raise ValueError("Provide api or base_url")
        if not self._service_name:
            raise ValueError("service_name is required")
        user_api = self._root_api.bind(token)
        user: FullUser = user_api.send(user_api.users.get_me())

        payload = decode_token_payload(token)
        if payload.service_name and payload.service_name != self._service_name:
            raise InvalidTokenException(
                f"Token was issued for service '{payload.service_name}', expected '{self._service_name}'",
            )
        permissions: UserPermissions = {title: [] for title in payload.permissions}
        return AuthContext(api=user_api, user=user, permissions=permissions)

    def build_context(self, token: str) -> AuthContext[SyncApi]:
        """Build the auth context and run the registered middlewares once."""
        auth_context = self.context_from_token(token)
        self._run_middlewares(auth_context)
        return auth_context

    def check(self, required: tuple[str, ...], token: str) -> AuthContext:
        auth_context = self.build_context(token)
        self.check_permissions(auth_context, required)
        return auth_context

    def check_permissions(self, auth_context: AuthContext, required: tuple[str, ...]) -> None:
        if required and not any(permission in auth_context.permissions for permission in required):
            raise PermissionDenied()

        for verifier in self._permission_verifiers:
            if not verifier.validate(auth_context, required):
                raise PermissionDenied()

    def _run_middlewares(self, auth_context: AuthContext) -> None:
        for middleware in self._middlewares:
            result = middleware(auth_context)
            if result:
                middleware_name = middleware.__name__
                auth_context.middleware_result.update({middleware_name: result})
