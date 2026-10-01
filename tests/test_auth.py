from __future__ import annotations

import asyncio

import httpx
import pytest

from admin_api.api.client import AsyncApi, SyncApi
from admin_api.auth.cache import TtlCache
from admin_api.auth.catalog import CreateUnexisted, FullSync, MemoryCatalog
from admin_api.auth.context import AuthContext
from admin_api.auth.fail import FailPolicy
from admin_api.auth.hooks import AsyncPermissionBase, AsyncPermissionValidator, PermissionBase, PermissionValidator
from admin_api.auth.manager import AdminApiAuth, AsyncAdminApiAuth
from admin_api.exceptions import ApiError, PermissionDenied
from tests.support import UNIT_ID, USER_ID, admin_http_handler, recording_handler


class _AllowAll(PermissionValidator):
    def validate(self, auth: AuthContext, request: object | None = None) -> bool:
        return True


class _UnitScoped(PermissionValidator):
    def validate(self, auth: AuthContext, request: object | None = None) -> bool:
        return any(scope.unit_id == UNIT_ID for scope in auth.scopes("user.update") if scope.type == "unit")


class _Reject(PermissionValidator):
    def validate(self, auth: AuthContext, request: object | None = None) -> bool:
        return False


class UserRead(PermissionBase):
    title = "user.read"
    validator = _AllowAll


class UserUpdate(PermissionBase):
    title = "user.update"
    validator = _UnitScoped


class RejectedUserUpdate(PermissionBase):
    title = "user.update"
    validator = _Reject


class MissingPermission(PermissionBase):
    title = "missing.perm"
    validator = _AllowAll


def test_sync_load_and_require():
    with SyncApi("http://admin-api.local", transport=httpx.MockTransport(admin_http_handler)) as api:
        auth = AdminApiAuth(api=api, service_name="cabinet")
        ctx = auth.check(("user.read",), "tok")
        assert ctx.user.id == USER_ID
        assert ctx.has("user.read")
        with pytest.raises(PermissionDenied):
            auth.check(("missing.perm",), "tok")


def test_custom_validator_and_middleware():
    def stash_user(context: AuthContext) -> dict | None:
        return {"id": str(context.user.id)}

    with SyncApi("http://admin-api.local", transport=httpx.MockTransport(admin_http_handler)) as api:
        auth = AdminApiAuth(api=api, service_name="cabinet")
        auth.add_permission(UserUpdate)
        auth.set_middlewares([stash_user])
        ctx = auth.check(("user.update",), "tok")
        assert ctx.extras["stash_user"]["id"] == str(USER_ID)


def test_permission_alternatives_and_argument_forms():
    with SyncApi("http://admin-api.local", transport=httpx.MockTransport(admin_http_handler)) as api:
        auth = AdminApiAuth(api=api, service_name="cabinet")
        auth.add_permission(RejectedUserUpdate)
        auth.add_permission(UserRead)
        auth.add_permission(MissingPermission)
        assert auth.check("user.read", "tok").user.id == USER_ID
        assert auth.check(None, "tok").user.id == USER_ID
        assert auth.check(("user.update", "user.read"), "tok").user.id == USER_ID
        assert auth.check(["user.update", "user.read"], "tok").user.id == USER_ID
        assert auth.check({"user.update", "user.read"}, "tok").user.id == USER_ID
        with pytest.raises(PermissionDenied):
            auth.check("user.update", "tok")
        with pytest.raises(PermissionDenied):
            auth.check(("user.update", "missing.perm"), "tok")
        with pytest.raises(PermissionDenied):
            auth.check("missing.perm", "tok")
        with pytest.raises(PermissionDenied):
            auth.check([], "tok")


def test_ttl_cache_skips_second_fetch():
    calls: list[str] = []
    with SyncApi("http://admin-api.local", transport=httpx.MockTransport(recording_handler(calls))) as api:
        auth = AdminApiAuth(api=api, service_name="cabinet", cache=TtlCache(ttl_seconds=60))
        auth.load("tok")
        auth.load("tok")
    assert calls.count("/api/v1/users/me") == 1
    assert calls.count("/api/v1/users/permissions") == 1


def test_fail_policy_uses_stale():
    calls: list[str] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        calls.append(http_request.url.path)
        if len(calls) > 2:
            return httpx.Response(503, json={"detail": "down"})
        return admin_http_handler(http_request)

    cache = TtlCache(ttl_seconds=0)
    with SyncApi("http://admin-api.local", transport=httpx.MockTransport(handler)) as api:
        auth = AdminApiAuth(
            api=api,
            service_name="cabinet",
            cache=cache,
            fail_policy=FailPolicy.USE_STALE,
        )
        first, _ = auth.load("tok")
        second, _ = auth.load("tok")
    assert first.user.id == second.user.id
    assert any(path == "/api/v1/users/me" for path in calls)


def test_fail_policy_deny():
    def handler(http_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "down"})

    with SyncApi("http://admin-api.local", transport=httpx.MockTransport(handler)) as api:
        auth = AdminApiAuth(api=api, service_name="cabinet", fail_policy=FailPolicy.DENY)
        with pytest.raises(ApiError):
            auth.load("tok")


def test_catalog_create_unexisted_and_full_sync():
    remote = MemoryCatalog({"legacy.perm"})
    auth = AdminApiAuth(
        base_url="http://admin-api.local",
        service_name="cabinet",
        catalog=CreateUnexisted(remote),
    )
    auth.add_permission(UserRead)
    auth.sync_catalog()
    assert remote.titles == {"legacy.perm", "user.read"}

    auth._catalog = FullSync(remote)
    auth.sync_catalog()
    assert remote.titles == {"user.read"}
    if auth._root_api is not None:
        auth._root_api.close()


class _AsyncAllow(AsyncPermissionValidator):
    async def validate(self, auth: AuthContext, request: object | None = None) -> bool:
        return True


class _AsyncReject(AsyncPermissionValidator):
    async def validate(self, auth: AuthContext, request: object | None = None) -> bool:
        return False


class AsyncUserRead(AsyncPermissionBase):
    title = "user.read"
    validator = _AsyncAllow


class AsyncRejectedUserUpdate(AsyncPermissionBase):
    title = "user.update"
    validator = _AsyncReject


def test_async_load():
    async def main() -> None:
        async with AsyncApi(
            "http://admin-api.local",
            transport=httpx.MockTransport(admin_http_handler),
        ) as api:
            auth = AsyncAdminApiAuth(api=api, service_name="cabinet")
            auth.add_permission(AsyncUserRead)
            ctx, bound = await auth.load("tok")
            await auth.assert_permissions(ctx, ("user.read",))
            assert ctx.user.id == USER_ID
            assert bound._token == "tok"

    asyncio.run(main())


def test_async_permission_alternatives_and_argument_forms():
    async def main() -> None:
        async with AsyncApi("http://admin-api.local", transport=httpx.MockTransport(admin_http_handler)) as api:
            auth = AsyncAdminApiAuth(api=api, service_name="cabinet")
            auth.add_permission(AsyncRejectedUserUpdate)
            auth.add_permission(AsyncUserRead)
            assert (await auth.check("user.read", "tok")).user.id == USER_ID
            assert (await auth.check(None, "tok")).user.id == USER_ID
            assert (await auth.check(("user.update", "user.read"), "tok")).user.id == USER_ID
            assert (await auth.check(["user.update", "user.read"], "tok")).user.id == USER_ID
            assert (await auth.check({"user.update", "user.read"}, "tok")).user.id == USER_ID
            with pytest.raises(PermissionDenied):
                await auth.check("user.update", "tok")
            with pytest.raises(PermissionDenied):
                await auth.check([], "tok")

    asyncio.run(main())
