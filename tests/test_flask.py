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


def test_flask_owned_client_can_be_closed():
    integration = AdminApiFlask(base_url="http://admin-api.local", service_name="cabinet")
    app = Flask(__name__)
    integration.init_app(app)
    assert integration._root_api is not None
    integration.close()
    assert integration._root_api._http.is_closed


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

    @app.get("/alternatives")
    @require(("missing.perm", "user.read"))
    def alternatives(auth: AuthContext):
        return jsonify({"id": str(auth.user.id)})

    @app.get("/authenticated")
    @require(None)
    def authenticated(auth: AuthContext):
        return jsonify({"id": str(auth.user.id)})

    @app.get("/and-allowed")
    @require("user.read", "user.update")
    def and_allowed(auth: AuthContext):
        return jsonify({"id": str(auth.user.id)})

    @app.get("/and-denied")
    @require("user.read", "missing.perm")
    def and_denied(auth: AuthContext):
        return jsonify({"id": str(auth.user.id)})

    @app.get("/list-or")
    @require(["missing.perm", "user.read"])
    def list_or(auth: AuthContext):
        return jsonify({"id": str(auth.user.id)})

    @app.get("/set-or")
    @require({"missing.perm", "user.read"})
    def set_or(auth: AuthContext):
        return jsonify({"id": str(auth.user.id)})

    @app.get("/mixed")
    @require("user.update", ["missing.perm", "user.read"])
    def mixed(auth: AuthContext):
        return jsonify({"id": str(auth.user.id)})

    @app.get("/empty-or")
    @require([])
    def empty_or(auth: AuthContext):
        return jsonify({"id": str(auth.user.id)})

    with app.test_client() as client:
        missing = client.get("/me")
        denied = client.get("/forbidden", headers={"Authorization": "Bearer tok"})
        alternatives = client.get("/alternatives", headers={"Authorization": "Bearer tok"})
        authenticated = client.get("/authenticated", headers={"Authorization": "Bearer tok"})
        and_allowed = client.get("/and-allowed", headers={"Authorization": "Bearer tok"})
        and_denied = client.get("/and-denied", headers={"Authorization": "Bearer tok"})
        list_or = client.get("/list-or", headers={"Authorization": "Bearer tok"})
        set_or = client.get("/set-or", headers={"Authorization": "Bearer tok"})
        mixed = client.get("/mixed", headers={"Authorization": "Bearer tok"})
        empty_or = client.get("/empty-or", headers={"Authorization": "Bearer tok"})

    assert missing.status_code == 401
    assert denied.status_code == 403
    assert alternatives.status_code == 200
    assert authenticated.status_code == 200
    assert and_allowed.status_code == 200
    assert and_denied.status_code == 403
    assert list_or.status_code == 200
    assert set_or.status_code == 200
    assert mixed.status_code == 200
    assert empty_or.status_code == 403
