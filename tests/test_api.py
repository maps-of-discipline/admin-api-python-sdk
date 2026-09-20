from __future__ import annotations

import asyncio

import httpx
import pytest
from pydantic import TypeAdapter

from admin_api import AdminApiAuth, AsyncApi, Operation, SyncApi
from admin_api.api.dto import FullOrganizationalUser, UnitScopeResponse
from admin_api.api.users import Users
from admin_api.exceptions import ApiError, InvalidTokenException, TokenNotProvided
from tests.support import (
    ME_PAYLOAD,
    PERMISSIONS_PAYLOAD,
    SCOPE_ID,
    UNIT_ID,
    admin_http_handler,
)


def _client(**kwargs) -> SyncApi:
    return SyncApi(
        "http://admin-api.local",
        transport=httpx.MockTransport(admin_http_handler),
        **kwargs,
    )


def test_builder_does_not_send_http():
    calls: list[str] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        calls.append(http_request.url.path)
        return httpx.Response(200, json=ME_PAYLOAD)

    with SyncApi("http://admin-api.local", token="tok", transport=httpx.MockTransport(handler)) as api:
        operation = api.users.get_me()

    assert isinstance(operation, Operation)
    assert calls == []


def test_send_get_me_and_permissions():
    with _client(token="tok") as api:
        user = api.send(api.users.get_me())
        permissions = api.send(api.users.get_permissions(service_name="cabinet"))

    assert isinstance(user, FullOrganizationalUser)
    assert user.display_name == "Org"
    assert permissions["user.read"] == []
    assert permissions["user.update"][0] == UnitScopeResponse(id=SCOPE_ID, unit_id=UNIT_ID)


def test_bind_sets_authorization_and_shares_transport():
    seen: list[str] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        seen.append(http_request.headers["authorization"])
        return httpx.Response(200, json=ME_PAYLOAD)

    with SyncApi("http://admin-api.local", transport=httpx.MockTransport(handler)) as root:
        alice = root.bind("alice-token")
        alice.send(alice.users.get_me())
        assert alice._http is root._http

    assert seen == ["Bearer alice-token"]


def test_bind_preserves_subclass():
    class ExtraUsers(Users):
        def ping(self) -> Operation[dict[str, bool]]:
            return Operation("GET", "/custom", adapter=TypeAdapter(dict[str, bool]))

    class CabinetApi(SyncApi):
        users = ExtraUsers()

    with CabinetApi("http://admin-api.local", transport=httpx.MockTransport(admin_http_handler)) as root:
        bound = root.bind("tok")
        assert type(bound) is CabinetApi
        assert bound.send(bound.users.ping()) == {"ok": True}


def test_custom_operation():
    ping = Operation("GET", "/custom", adapter=TypeAdapter(dict[str, bool]))
    with _client(token="tok") as api:
        assert api.send(ping) == {"ok": True}


def test_token_not_provided():
    with _client() as api, pytest.raises(TokenNotProvided):
        api.send(api.users.get_me())


def test_invalid_token():
    def handler(http_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"status_code": 401, "error_code": "unauthorized", "detail": "Invalid token"},
        )

    with (
        SyncApi("http://admin-api.local", token="bad", transport=httpx.MockTransport(handler)) as api,
        pytest.raises(InvalidTokenException, match="Invalid token"),
    ):
        api.send(api.users.get_me())


def test_api_error_not_found():
    def handler(http_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={"status_code": 404, "error_code": "not_found", "detail": "user not found"},
        )

    with SyncApi("http://admin-api.local", token="tok", transport=httpx.MockTransport(handler)) as api:
        with pytest.raises(ApiError) as exc_info:
            api.send(api.users.get_me())

    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "not_found"


def test_async_send():
    async def main() -> None:
        async with AsyncApi(
            "http://admin-api.local",
            token="tok",
            transport=httpx.MockTransport(admin_http_handler),
        ) as api:
            user = await api.send(api.users.get_me())
        assert user.fullname == "Org User"

    asyncio.run(main())


def test_admin_api_auth_default_client():
    auth = AdminApiAuth(base_url="http://admin-api.local", service_name="cabinet")
    try:
        assert type(auth._root_api) is SyncApi
    finally:
        assert auth._root_api is not None
        auth._root_api.close()


def test_admin_api_auth_injects_subclass():
    class ExtraUsers(Users):
        def ping(self) -> Operation[dict[str, bool]]:
            return Operation("GET", "/custom", adapter=TypeAdapter(dict[str, bool]))

    class CabinetApi(SyncApi):
        users = ExtraUsers()

    with CabinetApi("http://admin-api.local", transport=httpx.MockTransport(admin_http_handler)) as api:
        auth = AdminApiAuth(api=api, service_name="cabinet")
        ctx, bound = auth.load("tok")
        assert type(bound) is CabinetApi
        assert bound._http is api._http
        assert isinstance(ctx.user, FullOrganizationalUser)
        assert bound.send(bound.users.ping()) == {"ok": True}
        assert "user.read" in ctx.permissions
        assert PERMISSIONS_PAYLOAD["user.read"] == []
