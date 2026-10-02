from __future__ import annotations

import json
from uuid import UUID

import httpx

from admin_api import SyncApi
from admin_api.api.user_service_roles import (
    UnitScopeItem,
    UnitTypeScopeItem,
    UserServiceRolesCreate,
    UserServiceRolesResponse,
    UserServiceRolesUpdate,
)

ASSIGNMENT_ID = UUID(int=1)
USER_ID = UUID(int=2)
ROLE_ID = UUID(int=3)
UNIT_ID = UUID(int=4)
UNIT_TYPE_ID = UUID(int=5)
SCOPE_ID = UUID(int=6)


def test_user_service_roles_crud_with_scopes():
    calls: list[tuple[str, str, dict[str, object] | None]] = []
    response = {
        "id": str(ASSIGNMENT_ID),
        "user_id": str(USER_ID),
        "service_roles_id": str(ROLE_ID),
        "scope": [
            {"id": str(SCOPE_ID), "type": "unit", "unit_id": str(UNIT_ID)},
            {"id": str(SCOPE_ID), "type": "unit_type", "unit_type_id": str(UNIT_TYPE_ID)},
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.read()) if request.content else None
        calls.append((request.method, request.url.path, body))
        if request.method == "DELETE":
            return httpx.Response(200, json="success")
        return httpx.Response(200, json=response)

    with SyncApi("http://admin-api.local", token="token", transport=httpx.MockTransport(handler)) as api:
        created = api.send(
            api.user_service_roles.create(
                UserServiceRolesCreate(
                    service_roles_id=ROLE_ID,
                    user_id=USER_ID,
                    scope=[UnitScopeItem(unit_id=UNIT_ID), UnitTypeScopeItem(unit_type_id=UNIT_TYPE_ID)],
                ),
            ),
        )
        fetched = api.send(api.user_service_roles.get_by_id(ASSIGNMENT_ID))
        updated = api.send(
            api.user_service_roles.update(
                UserServiceRolesUpdate(id=ASSIGNMENT_ID, user_id=USER_ID, service_roles_id=ROLE_ID, scope=None),
            ),
        )
        deleted = api.send(api.user_service_roles.delete(ASSIGNMENT_ID))

    assert isinstance(created, UserServiceRolesResponse)
    assert created == fetched == updated
    assert created.scope[0].type == "unit"
    assert created.scope[1].type == "unit_type"
    assert deleted == "success"
    assert calls == [
        (
            "POST",
            "/api/v1/user_service_roles",
            {
                "service_roles_id": str(ROLE_ID),
                "user_id": str(USER_ID),
                "scope": [
                    {"type": "unit", "unit_id": str(UNIT_ID)},
                    {"type": "unit_type", "unit_type_id": str(UNIT_TYPE_ID)},
                ],
            },
        ),
        ("GET", f"/api/v1/user_service_roles/{ASSIGNMENT_ID}", None),
        (
            "PATCH",
            "/api/v1/user_service_roles",
            {"id": str(ASSIGNMENT_ID), "user_id": str(USER_ID), "service_roles_id": str(ROLE_ID), "scope": None},
        ),
        ("DELETE", f"/api/v1/user_service_roles/{ASSIGNMENT_ID}", None),
    ]
