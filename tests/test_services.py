from __future__ import annotations

import json
from uuid import UUID

import httpx
import pytest
from pydantic import ValidationError

from admin_api import SyncApi
from admin_api.api.services import (
    ServiceColorUpdate,
    ServiceCreate,
    ServiceGetByFiltersRequest,
    ServiceIconUpdate,
    ServiceResponse,
    ServiceUpdate,
)

SERVICE_ID = UUID("11111111-1111-1111-1111-111111111111")
SERVICE_PAYLOAD = {
    "id": str(SERVICE_ID),
    "name": "cabinet",
    "verbose_name": "Кабинет",
    "icon": "mdi-home",
    "color": "#AABBCC",
}


def test_services_get_by_filters_and_get_by_id():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer token"
        if request.url.path == "/api/v1/services/filters":
            assert request.method == "POST"
            assert dict(request.url.params) == {"page": "2", "size": "10", "sort_order": "ASC"}
            assert json.loads(request.read()) == {"service_name": "cab"}
            return httpx.Response(200, json={"data": [SERVICE_PAYLOAD], "page": 2, "size": 10, "total": 11})
        assert request.method == "GET"
        assert request.url.path == f"/api/v1/services/{SERVICE_ID}"
        return httpx.Response(200, json=SERVICE_PAYLOAD)

    with SyncApi("http://admin-api.local", token="token", transport=httpx.MockTransport(handler)) as api:
        page = api.send(
            api.services.get_by_filters(ServiceGetByFiltersRequest(service_name="cab"), page=2, sort_order="ASC"),
        )
        service = api.send(api.services.get_by_id(SERVICE_ID))

    assert page.total == 11
    assert isinstance(page.data[0], ServiceResponse)
    assert service == page.data[0]


def test_services_create_update_branding_and_delete():
    requests: list[tuple[str, str, dict[str, object] | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.read()) if request.content else None
        requests.append((request.method, request.url.path, body))
        if request.method == "DELETE":
            return httpx.Response(200, json="success")
        return httpx.Response(200 if request.method == "PATCH" else 201, json=SERVICE_PAYLOAD)

    with SyncApi("http://admin-api.local", token="token", transport=httpx.MockTransport(handler)) as api:
        created = api.send(api.services.create(ServiceCreate(name="cabinet", icon=" mdi-home ", color=" #aabbcc ")))
        updated = api.send(api.services.update(ServiceUpdate(id=SERVICE_ID, name="cabinet", verbose_name=None)))
        api.send(api.services.update_icon(ServiceIconUpdate(id=SERVICE_ID, icon="mdi-home")))
        api.send(api.services.update_color(ServiceColorUpdate(id=SERVICE_ID, color="#aabbcc")))
        deleted = api.send(api.services.delete(SERVICE_ID))

    assert isinstance(created, ServiceResponse)
    assert updated.id == SERVICE_ID
    assert deleted == "success"
    assert requests == [
        (
            "POST",
            "/api/v1/services",
            {"name": "cabinet", "verbose_name": None, "icon": "mdi-home", "color": "#AABBCC"},
        ),
        (
            "PATCH",
            "/api/v1/services",
            {"id": str(SERVICE_ID), "name": "cabinet", "verbose_name": None},
        ),
        ("PATCH", "/api/v1/services/branding/icon", {"id": str(SERVICE_ID), "icon": "mdi-home"}),
        ("PATCH", "/api/v1/services/branding/color", {"id": str(SERVICE_ID), "color": "#AABBCC"}),
        ("DELETE", f"/api/v1/services/{SERVICE_ID}", None),
    ]


def test_services_reject_invalid_branding():
    with pytest.raises(ValidationError):
        ServiceColorUpdate(id=SERVICE_ID, color="red")
