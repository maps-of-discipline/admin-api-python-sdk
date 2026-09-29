from __future__ import annotations

import asyncio
import json
from typing import Any
from uuid import UUID

import httpx
import pytest

from admin_api import AsyncApi, SyncApi
from admin_api.api import Page
from admin_api.api.dto import (
    AssignmentRuleResponse,
    AuthChallengeResponse,
    MessengerResponse,
    OrderResponse,
    PermissionResponse,
    ServiceResponse,
    ServiceRolesResponse,
    StaffAccount,
    UnitType,
    User,
    UserAuthData,
    UserServiceRolesResponse,
)
from admin_api.api.units import Unit, UnitTree
from admin_api.api.users import ManagedServices, NaturalUser, OrganizationalUser
from admin_api.auth import ApiPermissionCatalog, AsyncApiPermissionCatalog, CreateUnexisted, FullSync
from tests.support import ME_PAYLOAD, TYPE_ID, UNIT_ID, USER_ID

ID = UUID("66666666-6666-6666-6666-666666666666")
SERVICE_ID = UUID("77777777-7777-7777-7777-777777777777")
ROLE_ID = UUID("88888888-8888-8888-8888-888888888888")
PERMISSION_ID = UUID("99999999-9999-9999-9999-999999999999")

SERVICE = {"id": str(SERVICE_ID), "name": "cabinet", "verbose_name": "Cabinet", "icon": "mdi-x", "color": "#000000"}
ROLE = {"id": str(ROLE_ID), "service_id": str(SERVICE_ID), "role": "admin", "verbose_name": None, "permanent": False}
PERMISSION = {"id": str(PERMISSION_ID), "service_id": str(SERVICE_ID), "title": "user.read", "verbose_name": "Read"}
USER = {k: v for k, v in ME_PAYLOAD.items() if k not in ("display_name", "units")}
NATURAL_USER = {
    **USER,
    "kind": "natural",
    "mplk_individual_guid": None,
    "name": "Ivan",
    "surname": "Ivanov",
    "patronymic": None,
    "sex": "Male",
    "birthday": "2000-01-01",
    "phone": None,
    "photo_url": None,
}
USER_SERVICE_ROLE = {
    "id": str(ID),
    "service_roles_id": str(ROLE_ID),
    "user_id": str(USER_ID),
    "scope": [{"id": str(ID), "type": "unit", "unit_id": str(UNIT_ID)}],
}
ORDER = {"id": str(ID), "user_id": None, "service_id": None, "target_role": "staff", "comment": "pls", "user": USER}
AUTH_DATA = {"user_id": str(USER_ID), "access_token": "jwt", "refresh_token": str(ID)}
STAFF_ACCOUNT = {
    "id": str(ID),
    "account_type": "staff",
    "mplk_user_id": 1,
    "email_staff": None,
    "phone_staff": None,
    "allow_mobphone_in": False,
    "allow_mobphone_out": False,
    "positions": [],
}
EXPRESSION = {"kind": "predicate", "field": "group", "predicate": {"operator": "equal", "value": "221-321"}}
RULE = {
    "id": str(ID),
    "title": "Students",
    "enabled": True,
    "service_role_id": str(ROLE_ID),
    "expression": EXPRESSION,
    "scope_template": "unscoped",
}
UNIT = {"id": str(UNIT_ID), "title": "IT", "type": {"id": str(TYPE_ID), "title": "faculty"}, "parent_unit_id": None}


def page(*items: Any) -> dict[str, Any]:
    return {"data": list(items), "page": 1, "size": 10, "total": len(items)}


class Recorder:
    def __init__(self, status: int, payload: Any) -> None:
        self.status = status
        self.payload = payload
        self.request: httpx.Request | None = None

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.request = request
        if self.payload is None:
            return httpx.Response(self.status)
        return httpx.Response(self.status, json=self.payload)

    @property
    def body(self) -> Any:
        assert self.request is not None
        return json.loads(self.request.content) if self.request.content else None


def call(build, status: int, payload: Any, token: str | None = "tok"):
    recorder = Recorder(status, payload)
    with SyncApi("http://admin-api.local", token=token, transport=httpx.MockTransport(recorder)) as api:
        result = api.send(build(api))
    assert recorder.request is not None
    return result, recorder


CASES = [
    # users
    (
        lambda api: api.users.get(USER_ID),
        "GET",
        f"/api/v1/users/{USER_ID}",
        None,
        {},
        200,
        NATURAL_USER | {"accounts": []},
    ),
    (lambda api: api.users.delete(USER_ID), "DELETE", f"/api/v1/users/{USER_ID}", None, {}, 200, "success"),
    (
        lambda api: api.users.filter(email="a@b.c", role="staff", page=2, size=5),
        "POST",
        "/api/v1/users/filters",
        {"email": "a@b.c", "role": "staff"},
        {"page": "2", "size": "5", "sort_order": "DESC"},
        200,
        page(NATURAL_USER, ME_PAYLOAD),
    ),
    (
        lambda api: api.users.get_roles_from_service(USER_ID, "cabinet"),
        "POST",
        f"/api/v1/users/{USER_ID}/get_roles_from_service",
        None,
        {"service_name": "cabinet"},
        200,
        {"roles": [USER_SERVICE_ROLE]},
    ),
    (
        lambda api: api.users.get_accounts(),
        "GET",
        "/api/v1/users/accounts",
        None,
        {},
        200,
        {"accounts": [STAFF_ACCOUNT], "active_account_id": str(ID)},
    ),
    (
        lambda api: api.users.activate_account(ID),
        "PATCH",
        f"/api/v1/users/accounts/{ID}/activate",
        None,
        {},
        200,
        STAFF_ACCOUNT,
    ),
    (
        lambda api: api.users.get_managed_services(),
        "POST",
        "/api/v1/users/managed-services",
        None,
        {},
        200,
        {"services": [SERVICE]},
    ),
    (
        lambda api: api.users.assign_service(USER_ID, SERVICE_ID),
        "POST",
        "/api/v1/users/assign-service",
        {"user_id": str(USER_ID), "service_id": str(SERVICE_ID)},
        {},
        200,
        None,
    ),
    (
        lambda api: api.users.revoke_service(USER_ID, SERVICE_ID),
        "POST",
        "/api/v1/users/revoke-service",
        {"user_id": str(USER_ID), "service_id": str(SERVICE_ID)},
        {},
        200,
        None,
    ),
    (
        lambda api: api.users.link_mplk("login", "secret"),
        "POST",
        "/api/v1/users/link-mplk",
        {"login": "login", "raw_password": "secret"},
        {},
        200,
        AUTH_DATA,
    ),
    (
        lambda api: api.users.logout(ID),
        "POST",
        "/api/v1/users/logout",
        {"refresh_token": str(ID)},
        {},
        200,
        "success",
    ),
    # services
    (lambda api: api.services.get(SERVICE_ID), "GET", f"/api/v1/services/{SERVICE_ID}", None, {}, 200, SERVICE),
    (
        lambda api: api.services.filter(service_name="cab"),
        "POST",
        "/api/v1/services/filters",
        {"service_name": "cab"},
        {"page": "1", "size": "10", "sort_order": "DESC"},
        200,
        page(SERVICE),
    ),
    (
        lambda api: api.services.create(name="cabinet", verbose_name="Cabinet"),
        "POST",
        "/api/v1/services",
        {"name": "cabinet", "verbose_name": "Cabinet"},
        {},
        201,
        SERVICE,
    ),
    (
        lambda api: api.services.update(SERVICE_ID, name="cabinet2"),
        "PATCH",
        "/api/v1/services",
        {"id": str(SERVICE_ID), "name": "cabinet2"},
        {},
        200,
        SERVICE,
    ),
    (
        lambda api: api.services.update_icon(SERVICE_ID, "mdi-y"),
        "PATCH",
        "/api/v1/services/branding/icon",
        {"id": str(SERVICE_ID), "icon": "mdi-y"},
        {},
        200,
        SERVICE,
    ),
    (
        lambda api: api.services.update_color(SERVICE_ID, "#FFFFFF"),
        "PATCH",
        "/api/v1/services/branding/color",
        {"id": str(SERVICE_ID), "color": "#FFFFFF"},
        {},
        200,
        SERVICE,
    ),
    (
        lambda api: api.services.delete(SERVICE_ID),
        "DELETE",
        f"/api/v1/services/{SERVICE_ID}",
        None,
        {},
        200,
        "success",
    ),
    # service roles
    (lambda api: api.service_roles.get(ROLE_ID), "GET", f"/api/v1/service-roles/{ROLE_ID}", None, {}, 200, ROLE),
    (
        lambda api: api.service_roles.filter(service_name="cabinet"),
        "POST",
        "/api/v1/service-roles/filters",
        {"service_name": "cabinet"},
        {"page": "1", "size": "10", "sort_order": "DESC"},
        200,
        page(ROLE),
    ),
    (
        lambda api: api.service_roles.create(role="admin", service_id=SERVICE_ID),
        "POST",
        "/api/v1/service-roles",
        {"role": "admin", "service_id": str(SERVICE_ID)},
        {},
        200,
        ROLE,
    ),
    (
        lambda api: api.service_roles.update(ROLE_ID, role="staff", verbose_name="Staff"),
        "PATCH",
        "/api/v1/service-roles",
        {"id": str(ROLE_ID), "role": "staff", "verbose_name": "Staff"},
        {},
        200,
        ROLE,
    ),
    (
        lambda api: api.service_roles.delete(ROLE_ID),
        "DELETE",
        f"/api/v1/service-roles/{ROLE_ID}",
        None,
        {},
        200,
        "success",
    ),
    (
        lambda api: api.service_roles.get_permissions(ROLE_ID),
        "GET",
        f"/api/v1/service-roles/{ROLE_ID}/permissions",
        None,
        {},
        200,
        {"data": [{"permission_id": str(PERMISSION_ID), "service_role_id": str(ROLE_ID)}]},
    ),
    (
        lambda api: api.service_roles.assign_permission(ROLE_ID, PERMISSION_ID),
        "POST",
        "/api/v1/service-roles/assign-permission",
        {"service_role_id": str(ROLE_ID), "permission_id": str(PERMISSION_ID)},
        {},
        200,
        "success",
    ),
    (
        lambda api: api.service_roles.revoke_permission(ROLE_ID, PERMISSION_ID),
        "POST",
        "/api/v1/service-roles/revoke-permission",
        {"service_role_id": str(ROLE_ID), "permission_id": str(PERMISSION_ID)},
        {},
        200,
        "success",
    ),
    # permissions
    (
        lambda api: api.permissions.get(PERMISSION_ID),
        "GET",
        f"/api/v1/permission/{PERMISSION_ID}",
        None,
        {},
        200,
        PERMISSION,
    ),
    (
        lambda api: api.permissions.filter(service_name="cabinet", size=100),
        "POST",
        "/api/v1/permission/filters",
        {"service_name": "cabinet"},
        {"page": "1", "size": "100", "sort_order": "DESC"},
        200,
        page(PERMISSION),
    ),
    (
        lambda api: api.permissions.create(service_id=SERVICE_ID, title="user.read", verbose_name="Read"),
        "POST",
        "/api/v1/permission",
        {"service_id": str(SERVICE_ID), "title": "user.read", "verbose_name": "Read"},
        {},
        200,
        PERMISSION,
    ),
    (
        lambda api: api.permissions.update(PERMISSION_ID, service_id=SERVICE_ID, title="t", verbose_name="v"),
        "PATCH",
        "/api/v1/permission",
        {"id": str(PERMISSION_ID), "service_id": str(SERVICE_ID), "title": "t", "verbose_name": "v"},
        {},
        200,
        PERMISSION,
    ),
    (
        lambda api: api.permissions.delete(PERMISSION_ID),
        "DELETE",
        f"/api/v1/permission/{PERMISSION_ID}",
        None,
        {},
        200,
        "success",
    ),
    # user service roles
    (
        lambda api: api.user_service_roles.get(ID),
        "GET",
        f"/api/v1/user_service_roles/{ID}",
        None,
        {},
        200,
        USER_SERVICE_ROLE,
    ),
    (
        lambda api: api.user_service_roles.create(
            user_id=USER_ID,
            service_roles_id=ROLE_ID,
            scope=[{"type": "unit", "unit_id": str(UNIT_ID)}],
        ),
        "POST",
        "/api/v1/user_service_roles",
        {
            "user_id": str(USER_ID),
            "service_roles_id": str(ROLE_ID),
            "scope": [{"type": "unit", "unit_id": str(UNIT_ID)}],
        },
        {},
        200,
        USER_SERVICE_ROLE,
    ),
    (
        lambda api: api.user_service_roles.update(ID, user_id=USER_ID, service_roles_id=ROLE_ID, scope=[]),
        "PATCH",
        "/api/v1/user_service_roles",
        {"id": str(ID), "user_id": str(USER_ID), "service_roles_id": str(ROLE_ID), "scope": []},
        {},
        200,
        USER_SERVICE_ROLE,
    ),
    (
        lambda api: api.user_service_roles.delete(ID),
        "DELETE",
        f"/api/v1/user_service_roles/{ID}",
        None,
        {},
        200,
        "success",
    ),
    # orders
    (lambda api: api.orders.get(ID), "GET", f"/api/v1/orders/{ID}", None, {}, 200, ORDER),
    (
        lambda api: api.orders.list(limit=10, offset=20),
        "POST",
        "/api/v1/orders/list",
        {"limit": 10, "offset": 20},
        {},
        200,
        [ORDER],
    ),
    (
        lambda api: api.orders.create(target_role="staff", comment="pls", service_id=SERVICE_ID),
        "POST",
        "/api/v1/orders",
        {"target_role": "staff", "comment": "pls", "service_id": str(SERVICE_ID)},
        {},
        201,
        ORDER,
    ),
    (
        lambda api: api.orders.update(ID, target_role="admin", comment="upd"),
        "PATCH",
        "/api/v1/orders",
        {"id": str(ID), "target_role": "admin", "comment": "upd"},
        {},
        200,
        ORDER,
    ),
    (
        lambda api: api.orders.approve(ID, approve=False),
        "POST",
        "/api/v1/orders/approve",
        {"id": str(ID), "approve": False},
        {},
        200,
        None,
    ),
    (lambda api: api.orders.delete(ID), "DELETE", f"/api/v1/orders/{ID}", None, {}, 200, "success"),
    # messengers
    (
        lambda api: api.messengers.list(),
        "GET",
        "/api/v1/messengers",
        None,
        {},
        200,
        [{"id": str(ID), "messenger_type": "tg", "messenger_user_id": "1", "linked_at": "2026-01-01T00:00:00"}],
    ),
    (
        lambda api: api.messengers.link("tg", "id-token"),
        "POST",
        "/api/v1/messengers/link",
        {"messenger_type": "tg", "id_token": "id-token"},
        {},
        201,
        {"id": str(ID), "messenger_type": "tg", "messenger_user_id": "1", "linked_at": "2026-01-01T00:00:00"},
    ),
    (
        lambda api: api.messengers.unlink("tg"),
        "DELETE",
        "/api/v1/messengers/tg",
        None,
        {},
        200,
        {"detail": "unlinked"},
    ),
    (
        lambda api: api.messengers.get_user("tg", "42"),
        "GET",
        "/api/v1/messengers/user/tg/42",
        None,
        {},
        200,
        USER,
    ),
    # units
    (
        lambda api: api.units.list(root_id=UNIT_ID, max_depth=2),
        "GET",
        "/api/v1/units",
        None,
        {"flat": "false", "root_id": str(UNIT_ID), "max_depth": "2"},
        200,
        [UNIT | {"has_children": True, "children": [UNIT | {"has_children": False, "children": []}]}],
    ),
    (
        lambda api: api.units.list_flat(search="IT", type_ids=[TYPE_ID]),
        "GET",
        "/api/v1/units",
        None,
        {"flat": "true", "search": "IT", "type_ids": str(TYPE_ID)},
        200,
        [UNIT | {"has_children": False}],
    ),
    (
        lambda api: api.units.get_types(),
        "GET",
        "/api/v1/unit-types",
        None,
        {},
        200,
        [{"id": str(TYPE_ID), "title": "faculty"}],
    ),
    # assignment rules
    (lambda api: api.assignment_rules.get(ID), "GET", f"/api/v1/assignment-rules/{ID}", None, {}, 200, RULE),
    (
        lambda api: api.assignment_rules.list(service_role_id=ROLE_ID),
        "GET",
        "/api/v1/assignment-rules",
        None,
        {"limit": "50", "offset": "0", "service_role_id": str(ROLE_ID)},
        200,
        [RULE],
    ),
    (
        lambda api: api.assignment_rules.get_metadata(),
        "GET",
        "/api/v1/assignment-rules/metadata",
        None,
        {},
        200,
        {"fields": []},
    ),
    (
        lambda api: api.assignment_rules.create(title="Students", service_role_id=ROLE_ID, expression=EXPRESSION),
        "POST",
        "/api/v1/assignment-rules",
        {
            "title": "Students",
            "service_role_id": str(ROLE_ID),
            "expression": EXPRESSION,
            "enabled": True,
            "scope_template": "unscoped",
        },
        {},
        201,
        RULE,
    ),
    (
        lambda api: api.assignment_rules.update(ID, enabled=False),
        "PATCH",
        f"/api/v1/assignment-rules/{ID}",
        {"id": str(ID), "enabled": False},
        {},
        200,
        RULE,
    ),
    (lambda api: api.assignment_rules.delete(ID), "DELETE", f"/api/v1/assignment-rules/{ID}", None, {}, 204, None),
    # mplk
    (
        lambda api: api.mplk.generic("/api/data", "POST", query={"a": 1}, body={"x": 1}),
        "POST",
        "/api/v1/mplk/generic",
        {"body": {"method": "POST", "url": "/api/data", "headers": None, "query": {"a": 1}, "body": {"x": 1}}},
        {},
        200,
        {"ok": True},
    ),
]


@pytest.mark.parametrize(("build", "method", "path", "body", "params", "status", "payload"), CASES)
def test_operation_contract(build, method, path, body, params, status, payload):
    _, recorder = call(build, status, payload)
    assert recorder.request is not None
    assert recorder.request.method == method
    assert recorder.request.url.path == path
    assert dict(recorder.request.url.params) == params
    assert recorder.body == body
    expects_token = build(SyncApi("http://admin-api.local")).auth
    assert recorder.request.headers.get("authorization") == ("Bearer tok" if expects_token else None)


def test_typed_results():
    user, _ = call(lambda api: api.users.get(USER_ID), 200, NATURAL_USER | {"accounts": []})
    assert user.kind == "natural"

    users, _ = call(lambda api: api.users.filter(), 200, page(NATURAL_USER, ME_PAYLOAD))
    assert isinstance(users, Page)
    assert isinstance(users.data[0], NaturalUser)
    assert isinstance(users.data[1], OrganizationalUser)
    assert users.total == 2

    services, _ = call(lambda api: api.services.filter(), 200, page(SERVICE))
    assert services.data == [ServiceResponse.model_validate(SERVICE)]

    roles, _ = call(lambda api: api.service_roles.filter(), 200, page(ROLE))
    assert isinstance(roles.data[0], ServiceRolesResponse)

    permissions, _ = call(lambda api: api.permissions.filter(), 200, page(PERMISSION))
    assert isinstance(permissions.data[0], PermissionResponse)

    usr, _ = call(lambda api: api.user_service_roles.get(ID), 200, USER_SERVICE_ROLE)
    assert isinstance(usr, UserServiceRolesResponse)
    assert usr.scope is not None and usr.scope[0].type == "unit"

    orders, _ = call(lambda api: api.orders.list(), 200, [ORDER])
    assert isinstance(orders[0], OrderResponse)
    assert isinstance(orders[0].user, User)

    account, _ = call(lambda api: api.users.activate_account(ID), 200, STAFF_ACCOUNT)
    assert isinstance(account, StaffAccount)

    managed, _ = call(lambda api: api.users.get_managed_services(), 200, {"services": [SERVICE]})
    assert isinstance(managed, ManagedServices)
    assert managed.services[0].id == SERVICE_ID

    messengers, _ = call(
        lambda api: api.messengers.list(),
        200,
        [{"id": str(ID), "messenger_type": "tg", "messenger_user_id": "1", "linked_at": "2026-01-01T00:00:00"}],
    )
    assert isinstance(messengers[0], MessengerResponse)

    tree, _ = call(
        lambda api: api.units.list(),
        200,
        [UNIT | {"has_children": True, "children": [UNIT | {"has_children": False, "children": []}]}],
    )
    assert isinstance(tree[0], UnitTree)
    assert tree[0].children[0].title == "IT"

    flat, _ = call(lambda api: api.units.list_flat(), 200, [UNIT | {"has_children": False}])
    assert isinstance(flat[0], Unit)

    types, _ = call(lambda api: api.units.get_types(), 200, [{"id": str(TYPE_ID), "title": "faculty"}])
    assert types == [UnitType(id=TYPE_ID, title="faculty")]

    rule, _ = call(lambda api: api.assignment_rules.get(ID), 200, RULE)
    assert isinstance(rule, AssignmentRuleResponse)
    assert rule.expression.kind == "predicate"

    deleted, _ = call(lambda api: api.assignment_rules.delete(ID), 204, None)
    assert deleted is None


def test_public_auth_endpoints_do_not_require_token():
    challenge, recorder = call(
        lambda api: api.users.login_by_password("a@b.c", "secret"),
        200,
        {"pre_auth_token": "pre", "mfa_method": "email", "mfa_required": True},
        token=None,
    )
    assert isinstance(challenge, AuthChallengeResponse)
    assert recorder.body == {"type": "password", "email": "a@b.c", "raw_password": "secret"}
    assert "authorization" not in recorder.request.headers

    _, recorder = call(lambda api: api.users.login_by_email("a@b.c"), 200, challenge.model_dump(mode="json"), None)
    assert recorder.body == {"type": "email", "email": "a@b.c"}

    _, recorder = call(lambda api: api.users.login_by_mplk("l", "p"), 200, challenge.model_dump(mode="json"), None)
    assert recorder.body == {"type": "mplk", "login": "l", "raw_password": "p"}

    auth, recorder = call(lambda api: api.users.verify_auth_code("pre", "123456"), 200, AUTH_DATA, None)
    assert isinstance(auth, UserAuthData)
    assert recorder.request.url.path == "/api/v1/users/verification_auth_code"
    assert recorder.body == {"pre_auth_token": "pre", "code": "123456"}

    refreshed, recorder = call(lambda api: api.users.refresh(auth), 200, AUTH_DATA, None)
    assert refreshed == auth
    assert recorder.body == AUTH_DATA

    created, recorder = call(
        lambda api: api.users.sign_up(name="I", surname="S", patronymic="P", email="a@b.c", password="x"),
        201,
        {"id": str(USER_ID)},
        None,
    )
    assert created.id == str(USER_ID)
    assert recorder.body == {"name": "I", "surname": "S", "patronymic": "P", "email": "a@b.c", "raw_password": "x"}

    _, recorder = call(lambda api: api.assignment_rules.get_metadata(), 200, {}, None)
    assert "authorization" not in recorder.request.headers


def test_login_rejects_unknown_type():
    with SyncApi("http://admin-api.local") as api, pytest.raises(ValueError):
        api.users.login({"type": "magic"})


def test_async_resources():
    recorder = Recorder(200, page(SERVICE))

    async def main() -> Page[ServiceResponse]:
        async with AsyncApi("http://admin-api.local", token="tok", transport=httpx.MockTransport(recorder)) as api:
            return await api.send(api.services.filter(service_name="cabinet"))

    result = asyncio.run(main())
    assert result.data[0].name == "cabinet"


class FakeAdmin:
    """In-memory Admin API with LIKE-style service_name filtering, as the real backend does."""

    def __init__(self) -> None:
        other_id = UUID("12121212-1212-1212-1212-121212121212")
        self.services = [
            SERVICE,
            {**SERVICE, "id": str(other_id), "name": "cabinet-admin"},
        ]
        self.permissions: list[dict[str, Any]] = [
            {**PERMISSION, "title": "stale", "id": str(UUID(int=1))},
            {**PERMISSION, "title": "keep", "id": str(UUID(int=2))},
            {**PERMISSION, "service_id": str(other_id), "title": "foreign", "id": str(UUID(int=3))},
        ]
        self.calls: list[tuple[str, str]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls.append((request.method, request.url.path))
        body = json.loads(request.content) if request.content else {}
        pg, size = int(request.url.params.get("page", 1)), int(request.url.params.get("size", 10))
        if request.url.path == "/api/v1/services/filters":
            items = [s for s in self.services if body.get("service_name", "") in s["name"]]
            return httpx.Response(200, json=self._page(items, pg, size))
        if request.url.path == "/api/v1/permission/filters":
            names = {s["id"] for s in self.services if body.get("service_name", "") in s["name"]}
            items = [p for p in self.permissions if p["service_id"] in names]
            return httpx.Response(200, json=self._page(items, pg, size))
        if request.url.path == "/api/v1/permission" and request.method == "POST":
            created = {**body, "id": str(UUID(int=len(self.permissions) + 10))}
            self.permissions.append(created)
            return httpx.Response(200, json=created)
        if request.url.path.startswith("/api/v1/permission/") and request.method == "DELETE":
            permission_id = request.url.path.rsplit("/", 1)[1]
            self.permissions = [p for p in self.permissions if p["id"] != permission_id]
            return httpx.Response(200, json="success")
        return httpx.Response(404, json={"detail": "missing"})

    @staticmethod
    def _page(items: list[dict[str, Any]], pg: int, size: int) -> dict[str, Any]:
        return {"data": items[(pg - 1) * size : pg * size], "page": pg, "size": size, "total": len(items)}


def test_api_permission_catalog_full_sync_ignores_other_services():
    admin = FakeAdmin()
    with SyncApi("http://admin-api.local", token="tok", transport=httpx.MockTransport(admin)) as api:
        catalog = ApiPermissionCatalog(api, "cabinet")
        assert catalog.list_titles() == {"stale", "keep"}
        FullSync(catalog).apply({"keep": "Keep", "new": "New"})

    titles = {(p["service_id"], p["title"]) for p in admin.permissions}
    assert titles == {
        (str(SERVICE_ID), "keep"),
        (str(SERVICE_ID), "new"),
        ("12121212-1212-1212-1212-121212121212", "foreign"),
    }
    created = next(p for p in admin.permissions if p["title"] == "new")
    assert created["verbose_name"] == "New"


def test_async_api_permission_catalog_create_unexisted():
    admin = FakeAdmin()

    async def main() -> None:
        async with AsyncApi("http://admin-api.local", token="tok", transport=httpx.MockTransport(admin)) as api:
            await CreateUnexisted(AsyncApiPermissionCatalog(api, "cabinet")).aapply({"keep": "Keep", "fresh": ""})

    asyncio.run(main())
    titles = {p["title"] for p in admin.permissions}
    assert titles == {"stale", "keep", "foreign", "fresh"}
    assert next(p for p in admin.permissions if p["title"] == "fresh")["verbose_name"] == "fresh"


def test_api_permission_catalog_unknown_service():
    admin = FakeAdmin()
    with SyncApi("http://admin-api.local", token="tok", transport=httpx.MockTransport(admin)) as api:
        catalog = ApiPermissionCatalog(api, "missing")
        with pytest.raises(Exception, match="missing"):
            catalog.list_titles()
