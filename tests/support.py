from __future__ import annotations

from uuid import UUID

import httpx

USER_ID = UUID("11111111-1111-1111-1111-111111111111")
UNIT_ID = UUID("22222222-2222-2222-2222-222222222222")
SCOPE_ID = UUID("33333333-3333-3333-3333-333333333333")
EMAIL_ID = UUID("44444444-4444-4444-4444-444444444444")
TYPE_ID = UUID("55555555-5555-5555-5555-555555555555")

ME_PAYLOAD = {
    "id": str(USER_ID),
    "kind": "organizational",
    "mfa_method": "none",
    "last_active_account_id": None,
    "last_login_at": None,
    "emails": [
        {
            "id": str(EMAIL_ID),
            "email": "org@example.com",
            "is_primary": True,
            "verified_at": None,
        },
    ],
    "fullname": "Org User",
    "display_name": "Org",
    "units": [
        {
            "id": str(UNIT_ID),
            "title": "IT",
            "type": {"id": str(TYPE_ID), "title": "faculty"},
        },
    ],
}

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


def admin_http_handler(http_request: httpx.Request) -> httpx.Response:
    if http_request.url.path == "/api/v1/users/me":
        return httpx.Response(200, json=ME_PAYLOAD)
    if http_request.url.path == "/api/v1/users/permissions":
        assert http_request.url.params["service_name"] == "cabinet"
        return httpx.Response(200, json=PERMISSIONS_PAYLOAD)
    if http_request.url.path == "/custom":
        return httpx.Response(200, json={"ok": True})
    return httpx.Response(404, json={"status_code": 404, "error_code": "not_found", "detail": "missing"})


def recording_handler(calls: list[str]):
    def handler(http_request: httpx.Request) -> httpx.Response:
        calls.append(http_request.url.path)
        return admin_http_handler(http_request)

    return handler
