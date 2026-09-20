from __future__ import annotations

import httpx
from flask import Flask, jsonify

from admin_api.api.client import SyncApi
from admin_api.auth.context import AuthContext
from admin_api.integrations.flask import AdminApiFlask, current_auth, get_request_auth, require
from tests.support import USER_ID, admin_http_handler


def test_flask_require_injects_context_and_api():
    api = SyncApi("http://admin-api.local", transport=httpx.MockTransport(admin_http_handler))
    integration = AdminApiFlask(api=api, service_name="cabinet")
    app = Flask(__name__)
    integration.init_app(app)

    @app.get("/me")
    @require("user.read")
    def me(auth: AuthContext, bound: SyncApi):
        local = get_request_auth().context
        return jsonify(
            {
                "id": str(auth.user.id),
                "local": str(local.user.id),
                "proxy": str(current_auth.user.id),
                "bound": bound._token,
            },
        )

    with app.test_client() as client:
        response = client.get("/me", headers={"Authorization": "Bearer tok"})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["id"] == str(USER_ID)
    assert payload["local"] == str(USER_ID)
    assert payload["proxy"] == str(USER_ID)
    assert payload["bound"] == "tok"


def test_flask_missing_token_and_forbidden():
    api = SyncApi("http://admin-api.local", transport=httpx.MockTransport(admin_http_handler))
    integration = AdminApiFlask(api=api, service_name="cabinet")
    app = Flask(__name__)
    integration.init_app(app)

    @app.get("/me")
    @require("user.read")
    def me(auth: AuthContext):
        return jsonify({"id": str(auth.user.id)})

    @app.get("/forbidden")
    @require("missing.perm")
    def forbidden(auth: AuthContext):
        return jsonify({"id": str(auth.user.id)})

    with app.test_client() as client:
        missing = client.get("/me")
        denied = client.get("/forbidden", headers={"Authorization": "Bearer tok"})

    assert missing.status_code == 401
    assert denied.status_code == 403
