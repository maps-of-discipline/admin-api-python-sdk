from __future__ import annotations

import httpx
import pytest
from flask import Flask, jsonify

from admin_api.api.client import SyncApi
from admin_api.exceptions import PermissionDenied, TokenNotProvided
from admin_api.integrations.flask import AdminApiFlask
from admin_api.integrations.flask.decorators import require
from admin_api.integrations.flask.token_parser import TokenParserBase
from admin_api.sdk.auth_context import AuthContext
from tests.conftest import ME_PAYLOAD, TOKEN


class BearerParser(TokenParserBase):
    def get_token(self, request):
        header = request.headers.get("Authorization", "")
        return header.removeprefix("Bearer ").strip() or None


def _build_app() -> tuple[Flask, dict[str, int]]:
    calls = {"me": 0, "middleware": 0}

    def handler(http_request: httpx.Request) -> httpx.Response:
        if http_request.url.path == "/api/v1/users/me":
            calls["me"] += 1
            return httpx.Response(200, json=ME_PAYLOAD)
        return httpx.Response(404, json={"status_code": 404, "detail": "missing"})

    def mirror_user(auth_context: AuthContext) -> dict:
        calls["middleware"] += 1
        return {"user": "mirrored"}

    app = Flask(__name__)
    app.config["PROPAGATE_EXCEPTIONS"] = True

    api = SyncApi("http://admin-api.local", transport=httpx.MockTransport(handler))
    auth = AdminApiFlask(BearerParser(), api=api, service_name="cabinet")
    auth.set_middlewares([mirror_user])
    auth.init_app(app)

    @app.get("/guarded")
    @require("user.approved")
    @require("canViewCabinet")
    def guarded(auth_context: AuthContext):
        return jsonify(
            {
                "permissions": sorted(auth_context.permissions),
                "middleware_result": auth_context.middleware_result,
            },
        )

    @app.get("/admin-only")
    @require("user.isAdmin")
    def admin_only(auth_context: AuthContext):
        return jsonify({"ok": True})

    return app, calls


def test_require_injects_context_and_runs_once_per_request():
    app, calls = _build_app()
    client = app.test_client()

    response = client.get("/guarded", headers={"Authorization": f"Bearer {TOKEN}"})

    assert response.status_code == 200
    body = response.get_json()
    assert body["permissions"] == ["canViewCabinet", "user.approved"]
    assert body["middleware_result"] == {"mirror_user": {"user": "mirrored"}}
    assert calls == {"me": 1, "middleware": 1}


def test_require_denies_missing_permission():
    app, _ = _build_app()
    client = app.test_client()

    with pytest.raises(PermissionDenied):
        client.get("/admin-only", headers={"Authorization": f"Bearer {TOKEN}"})


def test_require_requires_token():
    app, _ = _build_app()
    client = app.test_client()

    with pytest.raises(TokenNotProvided):
        client.get("/guarded")
