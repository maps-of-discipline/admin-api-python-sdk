from __future__ import annotations

import json
from uuid import UUID

import httpx

from admin_api import SyncApi
from admin_api.api.permissions import (
    PermissionCreate,
    PermissionGetByFiltersRequest,
    PermissionResponse,
    PermissionUpdate,
)

PERMISSION_ID = UUID(int=1)
SERVICE_ID = UUID(int=2)
PERMISSION_PAYLOAD = {
    "id": str(PERMISSION_ID),
    "service_id": str(SERVICE_ID),
    "title": "user.read",
    "verbose_name": "Чтение пользователей",
}


def test_permissions_crud_and_filters_use_singular_route():
    calls: list[tuple[str, str, dict[str, object] | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.read()) if request.content else None
        calls.append((request.method, request.url.path, body))
        if request.url.path.endswith("/filters"):
            assert dict(request.url.params) == {"page": "2", "size": "10", "sort_order": "ASC"}
            return httpx.Response(200, json={"data": [PERMISSION_PAYLOAD], "page": 2, "size": 10, "total": 1})
        if request.method == "DELETE":
            return httpx.Response(200, json="success")
        return httpx.Response(200, json=PERMISSION_PAYLOAD)

    with SyncApi("http://admin-api.local", token="token", transport=httpx.MockTransport(handler)) as api:
        page = api.send(
            api.permissions.get_by_filters(PermissionGetByFiltersRequest(service_name="cab"), page=2, sort_order="ASC"),
        )
        fetched = api.send(api.permissions.get_by_id(PERMISSION_ID))
        created = api.send(
            api.permissions.create(
                PermissionCreate(service_id=SERVICE_ID, title="user.read", verbose_name="Чтение пользователей"),
            ),
        )
        updated = api.send(
            api.permissions.update(
                PermissionUpdate(
                    id=PERMISSION_ID,
                    service_id=SERVICE_ID,
                    title="user.read",
                    verbose_name="Чтение пользователей",
                ),
            ),
        )
        deleted = api.send(api.permissions.delete(PERMISSION_ID))

    assert isinstance(page.data[0], PermissionResponse)
    assert fetched == created == updated
    assert deleted == "success"
    assert calls == [
        ("POST", "/api/v1/permission/filters", {"service_name": "cab"}),
        ("GET", f"/api/v1/permission/{PERMISSION_ID}", None),
        (
            "POST",
            "/api/v1/permission",
            {"service_id": str(SERVICE_ID), "title": "user.read", "verbose_name": "Чтение пользователей"},
        ),
        (
            "PATCH",
            "/api/v1/permission",
            {
                "service_id": str(SERVICE_ID),
                "title": "user.read",
                "verbose_name": "Чтение пользователей",
                "id": str(PERMISSION_ID),
            },
        ),
        ("DELETE", f"/api/v1/permission/{PERMISSION_ID}", None),
    ]
