from __future__ import annotations

import httpx
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from admin_api.api.client import AsyncApi
from admin_api.auth.cache import TtlCache
from admin_api.auth.context import AuthContext
from admin_api.auth.hooks import AsyncPermissionBase, AsyncPermissionValidator
from admin_api.integrations.fastapi import AdminApiFastAPI, RequestAuth, get_api, get_request_auth, require
from tests.support import UNIT_ID, USER_ID, admin_http_handler, recording_handler


def _build_app(api: AsyncApi, *, cache=None) -> FastAPI:
    integration = AdminApiFastAPI(api=api, service_name="cabinet", cache=cache)
    app = FastAPI()
    integration.init_app(app)

    @app.get("/me")
    async def me(
        auth: AuthContext = Depends(require("user.read")),
        bound: AsyncApi = Depends(get_api),
        bundle: RequestAuth = Depends(get_request_auth),
    ):
        return {
            "id": str(auth.user.id),
            "bundle_id": str(bundle.context.user.id),
            "token": bound._token,
        }

    @app.get("/forbidden")
    async def forbidden(auth: AuthContext = Depends(require("missing.perm"))):
        return {"id": str(auth.user.id)}

    @app.get("/alternatives")
    async def alternatives(auth: AuthContext = Depends(require(("missing.perm", "user.read")))):
        return {"id": str(auth.user.id)}

    @app.get("/authenticated")
    async def authenticated(auth: AuthContext = Depends(require(None))):
        return {"id": str(auth.user.id)}

    @app.get("/and-allowed")
    async def and_allowed(auth: AuthContext = Depends(require("user.read", "user.update"))):
        return {"id": str(auth.user.id)}

    @app.get("/and-denied")
    async def and_denied(auth: AuthContext = Depends(require("user.read", "missing.perm"))):
        return {"id": str(auth.user.id)}

    @app.get("/list-or")
    async def list_or(auth: AuthContext = Depends(require(["missing.perm", "user.read"]))):
        return {"id": str(auth.user.id)}

    @app.get("/set-or")
    async def set_or(auth: AuthContext = Depends(require({"missing.perm", "user.read"}))):
        return {"id": str(auth.user.id)}

    @app.get("/mixed")
    async def mixed(auth: AuthContext = Depends(require("user.update", ["missing.perm", "user.read"]))):
        return {"id": str(auth.user.id)}

    @app.get("/empty-or")
    async def empty_or(auth: AuthContext = Depends(require([]))):
        return {"id": str(auth.user.id)}

    return app


def test_fastapi_require_and_shared_identity():
    api = AsyncApi("http://admin-api.local", transport=httpx.MockTransport(admin_http_handler))
    with TestClient(_build_app(api)) as client:
        response = client.get("/me", headers={"Authorization": "Bearer tok"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(USER_ID)
    assert payload["bundle_id"] == str(USER_ID)
    assert payload["token"] == "tok"


def test_fastapi_missing_token():
    api = AsyncApi("http://admin-api.local", transport=httpx.MockTransport(admin_http_handler))
    with TestClient(_build_app(api)) as client:
        response = client.get("/me")
    assert response.status_code == 401


def test_fastapi_permission_denied():
    api = AsyncApi("http://admin-api.local", transport=httpx.MockTransport(admin_http_handler))
    with TestClient(_build_app(api)) as client:
        response = client.get("/forbidden", headers={"Authorization": "Bearer tok"})
    assert response.status_code == 403


def test_fastapi_permission_argument_forms():
    api = AsyncApi("http://admin-api.local", transport=httpx.MockTransport(admin_http_handler))
    with TestClient(_build_app(api)) as client:
        alternatives = client.get("/alternatives", headers={"Authorization": "Bearer tok"})
        authenticated = client.get("/authenticated", headers={"Authorization": "Bearer tok"})
        and_allowed = client.get("/and-allowed", headers={"Authorization": "Bearer tok"})
        and_denied = client.get("/and-denied", headers={"Authorization": "Bearer tok"})
        list_or = client.get("/list-or", headers={"Authorization": "Bearer tok"})
        set_or = client.get("/set-or", headers={"Authorization": "Bearer tok"})
        mixed = client.get("/mixed", headers={"Authorization": "Bearer tok"})
        empty_or = client.get("/empty-or", headers={"Authorization": "Bearer tok"})
    assert alternatives.status_code == 200
    assert authenticated.status_code == 200
    assert and_allowed.status_code == 200
    assert and_denied.status_code == 403
    assert list_or.status_code == 200
    assert set_or.status_code == 200
    assert mixed.status_code == 200
    assert empty_or.status_code == 403


def test_fastapi_cache_reuses_snapshot_between_requests():
    calls: list[str] = []
    api = AsyncApi("http://admin-api.local", transport=httpx.MockTransport(recording_handler(calls)))
    with TestClient(_build_app(api, cache=TtlCache(ttl_seconds=60))) as client:
        first = client.get("/me", headers={"Authorization": "Bearer tok"})
        second = client.get("/me", headers={"Authorization": "Bearer tok"})
    assert first.status_code == 200
    assert second.status_code == 200
    assert calls.count("/api/v1/users/me") == 1
    assert calls.count("/api/v1/users/permissions") == 1


class _ProgramInUnit(AsyncPermissionValidator):
    async def validate(self, auth: AuthContext, request: object | None = None) -> bool:
        path_params = getattr(request, "path_params", {})
        program_id = path_params.get("program_id")
        return program_id == str(UNIT_ID) and any(
            scope.type == "unit" and scope.unit_id == UNIT_ID for scope in auth.scopes("user.update")
        )


class ProgramManage(AsyncPermissionBase):
    title = "user.update"
    validator = _ProgramInUnit


def test_fastapi_scoped_permission_uses_request():
    api = AsyncApi("http://admin-api.local", transport=httpx.MockTransport(admin_http_handler))
    integration = AdminApiFastAPI(api=api, service_name="cabinet")
    integration.add_permission(ProgramManage)
    app = FastAPI()
    integration.init_app(app)

    @app.get("/programs/{program_id}")
    async def update_program(
        program_id: str,
        auth: AuthContext = Depends(require("user.update")),
    ):
        return {"id": str(auth.user.id), "program_id": program_id}

    with TestClient(app) as client:
        allowed = client.get(f"/programs/{UNIT_ID}", headers={"Authorization": "Bearer tok"})
        denied = client.get("/programs/other", headers={"Authorization": "Bearer tok"})

    assert allowed.status_code == 200
    assert denied.status_code == 403
