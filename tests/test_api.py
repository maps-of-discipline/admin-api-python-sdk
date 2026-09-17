from __future__ import annotations

import asyncio
from uuid import UUID

import httpx
import pytest
from pydantic import TypeAdapter

from admin_api import AdminApiAuth, AsyncApi, Operation, SyncApi
from admin_api.api.users import User, Users
from admin_api.exceptions import ApiError, InvalidTokenException, PermissionDenied, TokenNotProvided
from admin_api.sdk.token import decode_token_payload
from tests.conftest import (
    FOREIGN_SERVICE_TOKEN,
    ME_PAYLOAD,
    TOKEN,
    USER_ID,
    make_token,
)

UNIT_ID = UUID("22222222-2222-2222-2222-222222222222")
SCOPE_ID = UUID("33333333-3333-3333-3333-333333333333")

PERMISSIONS_PAYLOAD = {
    "user.read": [],
    "user.update": [
        {
            "id": str(SCOPE_ID),
            "type": "unit",
            "unit_id": str(UNIT_ID),
        },
    ],
}


def _handler(http_request: httpx.Request) -> httpx.Response:
    if http_request.url.path == "/api/v1/users/me":
        return httpx.Response(200, json=ME_PAYLOAD)
    if http_request.url.path == "/api/v1/users/permissions":
        assert http_request.url.params["service_name"] == "cabinet"
        return httpx.Response(200, json=PERMISSIONS_PAYLOAD)
    if http_request.url.path == "/custom":
        return httpx.Response(200, json={"ok": True})
    return httpx.Response(404, json={"status_code": 404, "error_code": "not_found", "detail": "missing"})


def _client(**kwargs) -> SyncApi:
    return SyncApi(
        "http://admin-api.local",
        transport=httpx.MockTransport(_handler),
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


def test_send_get_me():
    with _client(token="tok") as api:
        user = api.send(api.users.get_me())

    assert isinstance(user, User)
    assert user.id == USER_ID
    assert user.role == "student"
    assert user.fullname == "Иванов Иван Иванович"
    assert user.department_code == "2025-3445"
    assert user.study_group == "254-352"


def test_send_get_permissions():
    with _client(token="tok") as api:
        permissions = api.send(api.users.get_permissions(service_name="cabinet"))

    assert permissions["user.read"] == []
    assert permissions["user.update"][0].id == SCOPE_ID
    assert permissions["user.update"][0].unit_id == UNIT_ID


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

    with CabinetApi("http://admin-api.local", transport=httpx.MockTransport(_handler)) as root:
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
            transport=httpx.MockTransport(_handler),
        ) as api:
            user = await api.send(api.users.get_me())
        assert user.fullname == "Иванов Иван Иванович"

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

    with CabinetApi("http://admin-api.local", transport=httpx.MockTransport(_handler)) as api:
        auth = AdminApiAuth(api=api, service_name="cabinet")
        ctx = auth.context_from_token(TOKEN)
        assert type(ctx.api) is CabinetApi
        assert ctx.api._http is api._http
        assert isinstance(ctx.user, User)
        assert ctx.api.send(ctx.api.users.ping()) == {"ok": True}


def test_context_takes_permissions_from_token_claims():
    paths: list[str] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        paths.append(http_request.url.path)
        if http_request.url.path == "/api/v1/users/me":
            return httpx.Response(200, json=ME_PAYLOAD)
        return httpx.Response(404, json={"status_code": 404, "detail": "missing"})

    with SyncApi("http://admin-api.local", transport=httpx.MockTransport(handler)) as api:
        auth = AdminApiAuth(api=api, service_name="cabinet")
        ctx = auth.check(("canViewCabinet",), TOKEN)

    assert set(ctx.permissions) == {"user.approved", "canViewCabinet"}
    assert paths == ["/api/v1/users/me"]


def test_context_rejects_token_of_another_service():
    with _client() as api:
        auth = AdminApiAuth(api=api, service_name="cabinet")
        with pytest.raises(InvalidTokenException, match="kd_maps"):
            auth.context_from_token(FOREIGN_SERVICE_TOKEN)


def test_check_denies_missing_permission():
    with _client() as api:
        auth = AdminApiAuth(api=api, service_name="cabinet")
        with pytest.raises(PermissionDenied):
            auth.check(("user.isAdmin",), TOKEN)


def test_decode_token_payload():
    payload = decode_token_payload(TOKEN)
    assert payload.user_id == USER_ID
    assert payload.service_name == "cabinet"
    assert payload.permissions == ["user.approved", "canViewCabinet"]


@pytest.mark.parametrize("token", ["", "not-a-jwt", "a.b", "a.b.c", make_token({"role": "student"})])
def test_decode_token_payload_invalid(token: str):
    with pytest.raises(InvalidTokenException):
        decode_token_payload(token)
