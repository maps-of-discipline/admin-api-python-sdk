from __future__ import annotations

import json
from uuid import UUID

import httpx

from admin_api import SyncApi
from admin_api.api.service_roles import (
    ServiceRoleGetByFiltersRequest,
    ServiceRolesAssignPermission,
    ServiceRolesCreate,
    ServiceRolesResponse,
    ServiceRolesRevokePermission,
    ServiceRolesUpdate,
)

ROLE_ID = UUID(int=1)
SERVICE_ID = UUID(int=2)
PERMISSION_ID = UUID(int=3)
ROLE_PAYLOAD = {
    "id": str(ROLE_ID),
    "service_id": str(SERVICE_ID),
    "role": "operator",
    "verbose_name": "Оператор",
    "permanent": False,
}


def test_service_roles_crud_and_permissions():
    calls: list[tuple[str, str, dict[str, object] | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.read()) if request.content else None
        calls.append((request.method, request.url.path, body))
        if request.url.path.endswith("/filters"):
            return httpx.Response(200, json={"data": [ROLE_PAYLOAD], "page": 1, "size": 10, "total": 1})
        if request.url.path.endswith("/permissions"):
            return httpx.Response(
                200,
                json={"data": [{"permission_id": str(PERMISSION_ID), "service_roles_id": str(ROLE_ID)}]},
            )
        if request.method == "PATCH":
            return httpx.Response(200, json=None)
        if request.method == "DELETE" or request.url.path.endswith(("assign-permission", "revoke-permission")):
            return httpx.Response(200, json="success")
        return httpx.Response(200, json=ROLE_PAYLOAD)

    with SyncApi("http://admin-api.local", token="token", transport=httpx.MockTransport(handler)) as api:
        page = api.send(api.service_roles.get_by_filters(ServiceRoleGetByFiltersRequest(service_name="cab")))
        fetched = api.send(api.service_roles.get_by_id(ROLE_ID))
        created = api.send(api.service_roles.create(ServiceRolesCreate(service_id=SERVICE_ID, role="operator")))
        updated = api.send(
            api.service_roles.update(ServiceRolesUpdate(id=ROLE_ID, service_id=SERVICE_ID, role="operator")),
        )
        permissions = api.send(api.service_roles.get_permissions(ROLE_ID))
        assigned = api.send(
            api.service_roles.assign_permission(
                ServiceRolesAssignPermission(permission_id=PERMISSION_ID, service_role_id=ROLE_ID),
            ),
        )
        revoked = api.send(
            api.service_roles.revoke_permission(
                ServiceRolesRevokePermission(permission_id=PERMISSION_ID, service_role_id=ROLE_ID),
            ),
        )
        deleted = api.send(api.service_roles.delete(ROLE_ID))

    assert isinstance(page.data[0], ServiceRolesResponse)
    assert fetched == created == page.data[0]
    assert updated is None
    assert permissions.data[0].service_role_id == ROLE_ID
    assert assigned == revoked == deleted == "success"
    assert calls == [
        ("POST", "/api/v1/service-roles/filters", {"service_name": "cab"}),
        ("GET", f"/api/v1/service-roles/{ROLE_ID}", None),
        (
            "POST",
            "/api/v1/service-roles",
            {"service_id": str(SERVICE_ID), "role": "operator", "verbose_name": None},
        ),
        (
            "PATCH",
            "/api/v1/service-roles",
            {"service_id": str(SERVICE_ID), "role": "operator", "verbose_name": None, "id": str(ROLE_ID)},
        ),
        ("GET", f"/api/v1/service-roles/{ROLE_ID}/permissions", None),
        (
            "POST",
            "/api/v1/service-roles/assign-permission",
            {"permission_id": str(PERMISSION_ID), "service_role_id": str(ROLE_ID)},
        ),
        (
            "POST",
            "/api/v1/service-roles/revoke-permission",
            {"permission_id": str(PERMISSION_ID), "service_role_id": str(ROLE_ID)},
        ),
        ("DELETE", f"/api/v1/service-roles/{ROLE_ID}", None),
    ]
