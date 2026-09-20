from __future__ import annotations

from collections.abc import Mapping

import httpx

from admin_api.api.client import AsyncApi, SyncApi
from admin_api.auth.cache import AuthCache, AuthSnapshot, NoCache, token_hash
from admin_api.auth.catalog import CatalogStrategy, DoNothing
from admin_api.auth.check import assert_has_permission
from admin_api.auth.context import AuthContext
from admin_api.auth.fail import FailPolicy
from admin_api.auth.hooks import (
    AsyncMiddleware,
    AsyncPermissionBase,
    AsyncPermissionVerifier,
    Middleware,
    PermissionBase,
    PermissionVerifier,
    apply_middleware_result,
)
from admin_api.exceptions import ApiError, InvalidTokenException, PermissionDenied


class BaseAdminApiAuth:
    def __init__(
        self,
        *,
        timeout_ms: int = 300,
        service_name: str | None = None,
        cache: AuthCache | None = None,
        fail_policy: FailPolicy = FailPolicy.DENY,
        catalog: CatalogStrategy | None = None,
    ) -> None:
        self._timeout_ms = timeout_ms
        self._service_name = service_name
        self._cache = cache or NoCache()
        self._fail_policy = fail_policy
        self._catalog = catalog or DoNothing()

    def _require_service_name(self) -> str:
        if not self._service_name:
            raise ValueError("service_name is required")
        return self._service_name

    def _read_cache(self, token: str) -> AuthSnapshot | None:
        return self._cache.get(token_hash(token))

    def _store_cache(self, token: str, snapshot: AuthSnapshot) -> None:
        self._cache.set(token_hash(token), snapshot)

    def _recover_snapshot(self, token: str, error: Exception) -> AuthSnapshot:
        if isinstance(error, InvalidTokenException):
            self._cache.drop(token_hash(token))
            raise error
        if isinstance(error, ApiError | httpx.HTTPError) and self._fail_policy is FailPolicy.USE_STALE:
            stale = self._cache.get_stale(token_hash(token))
            if stale is not None:
                return stale
        raise error

    def _context_from_snapshot(self, snapshot: AuthSnapshot) -> AuthContext:
        return AuthContext(user=snapshot.user, permissions=snapshot.permissions)


class AdminApiAuth(BaseAdminApiAuth):
    def __init__(
        self,
        api: SyncApi | None = None,
        *,
        base_url: str | None = None,
        timeout_ms: int = 300,
        service_name: str | None = None,
        cache: AuthCache | None = None,
        fail_policy: FailPolicy = FailPolicy.DENY,
        catalog: CatalogStrategy | None = None,
    ) -> None:
        super().__init__(
            timeout_ms=timeout_ms,
            service_name=service_name,
            cache=cache,
            fail_policy=fail_policy,
            catalog=catalog,
        )
        if api is None and base_url is not None:
            api = SyncApi(base_url, timeout=timeout_ms / 1000)
        self._root_api = api
        self._middlewares: list[Middleware] = []
        self._verifier = PermissionVerifier()

    def add_permission(self, permission: type[PermissionBase]) -> None:
        self._verifier.add_permission(permission)

    def add_permission_verifier(self, verifier: PermissionVerifier) -> None:
        for title, permission in verifier._permissions.items():
            self._verifier._permissions[title] = permission

    def set_middlewares(self, middlewares: list[Middleware]) -> None:
        self._middlewares = middlewares

    def local_catalog(self) -> Mapping[str, str]:
        return self._verifier.catalog()

    def sync_catalog(self) -> None:
        self._catalog.apply(self.local_catalog())

    def context_from_token(self, token: str) -> AuthContext:
        context, _api = self.load(token)
        return context

    def load(self, token: str) -> tuple[AuthContext, SyncApi]:
        snapshot = self._load_snapshot(token)
        context = self._context_from_snapshot(snapshot)
        self._run_middlewares(context)
        return context, self._bind(token)

    def check(self, required: tuple[str, ...], token: str, request: object | None = None) -> AuthContext:
        context, _api = self.load(token)
        self.assert_permissions(context, required, request=request)
        return context

    def assert_permissions(
        self,
        context: AuthContext,
        required: tuple[str, ...],
        request: object | None = None,
    ) -> None:
        assert_has_permission(context, required)
        if not self._verifier.validate(context, required, request=request):
            raise PermissionDenied()

    def _bind(self, token: str) -> SyncApi:
        if self._root_api is None:
            raise ValueError("Provide api or base_url")
        return self._root_api.bind(token)

    def _load_snapshot(self, token: str) -> AuthSnapshot:
        cached = self._read_cache(token)
        if cached is not None:
            return cached
        try:
            snapshot = self._fetch_snapshot(token)
        except Exception as error:
            return self._recover_snapshot(token, error)
        self._store_cache(token, snapshot)
        return snapshot

    def _fetch_snapshot(self, token: str) -> AuthSnapshot:
        api = self._bind(token)
        user = api.send(api.users.get_me())
        permissions = api.send(api.users.get_permissions(self._require_service_name()))
        return AuthSnapshot(user=user, permissions=permissions)

    def _run_middlewares(self, context: AuthContext) -> None:
        for middleware in self._middlewares:
            apply_middleware_result(context, middleware, middleware(context))


class AsyncAdminApiAuth(BaseAdminApiAuth):
    def __init__(
        self,
        api: AsyncApi | None = None,
        *,
        base_url: str | None = None,
        timeout_ms: int = 300,
        service_name: str | None = None,
        cache: AuthCache | None = None,
        fail_policy: FailPolicy = FailPolicy.DENY,
        catalog: CatalogStrategy | None = None,
    ) -> None:
        super().__init__(
            timeout_ms=timeout_ms,
            service_name=service_name,
            cache=cache,
            fail_policy=fail_policy,
            catalog=catalog,
        )
        if api is None and base_url is not None:
            api = AsyncApi(base_url, timeout=timeout_ms / 1000)
        self._root_api = api
        self._middlewares: list[AsyncMiddleware] = []
        self._verifier = AsyncPermissionVerifier()

    def add_permission(self, permission: type[AsyncPermissionBase]) -> None:
        self._verifier.add_permission(permission)

    def set_middlewares(self, middlewares: list[AsyncMiddleware]) -> None:
        self._middlewares = middlewares

    def local_catalog(self) -> Mapping[str, str]:
        return self._verifier.catalog()

    async def sync_catalog(self) -> None:
        await self._catalog.aapply(self.local_catalog())

    async def context_from_token(self, token: str) -> AuthContext:
        context, _api = await self.load(token)
        return context

    async def load(self, token: str) -> tuple[AuthContext, AsyncApi]:
        snapshot = await self._load_snapshot(token)
        context = self._context_from_snapshot(snapshot)
        await self._run_middlewares(context)
        return context, self._bind(token)

    async def check(
        self,
        required: tuple[str, ...],
        token: str,
        request: object | None = None,
    ) -> AuthContext:
        context, _api = await self.load(token)
        await self.assert_permissions(context, required, request=request)
        return context

    async def assert_permissions(
        self,
        context: AuthContext,
        required: tuple[str, ...],
        request: object | None = None,
    ) -> None:
        assert_has_permission(context, required)
        if not await self._verifier.validate(context, required, request=request):
            raise PermissionDenied()

    def _bind(self, token: str) -> AsyncApi:
        if self._root_api is None:
            raise ValueError("Provide api or base_url")
        return self._root_api.bind(token)

    async def _load_snapshot(self, token: str) -> AuthSnapshot:
        cached = self._read_cache(token)
        if cached is not None:
            return cached
        try:
            snapshot = await self._fetch_snapshot(token)
        except Exception as error:
            return self._recover_snapshot(token, error)
        self._store_cache(token, snapshot)
        return snapshot

    async def _fetch_snapshot(self, token: str) -> AuthSnapshot:
        api = self._bind(token)
        user = await api.send(api.users.get_me())
        permissions = await api.send(api.users.get_permissions(self._require_service_name()))
        return AuthSnapshot(user=user, permissions=permissions)

    async def _run_middlewares(self, context: AuthContext) -> None:
        for middleware in self._middlewares:
            apply_middleware_result(context, middleware, await middleware(context))
