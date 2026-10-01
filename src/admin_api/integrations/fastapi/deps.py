from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass

from fastapi import Depends, Request

from admin_api.api.client import AsyncApi
from admin_api.auth.context import AuthContext
from admin_api.integrations.fastapi.extension import STATE_KEY, AdminApiFastAPI

REQUEST_AUTH_KEY = "admin_api_request_auth"


@dataclass
class RequestAuth:
    context: AuthContext
    api: AsyncApi


def _integration(request: Request) -> AdminApiFastAPI:
    integration = getattr(request.app.state, STATE_KEY, None)
    if not isinstance(integration, AdminApiFastAPI):
        raise RuntimeError("AdminApiFastAPI is not initialized. Call init_app(app).")
    return integration


async def get_request_auth(request: Request) -> RequestAuth:
    cached = getattr(request.state, REQUEST_AUTH_KEY, None)
    if isinstance(cached, RequestAuth):
        return cached
    integration = _integration(request)
    token = integration.parse_token(request)
    context, api = await integration.load(token)
    bundle = RequestAuth(context=context, api=api)
    setattr(request.state, REQUEST_AUTH_KEY, bundle)
    return bundle


async def get_api(bundle: RequestAuth = Depends(get_request_auth)) -> AsyncApi:
    return bundle.api


def require(*required: Collection[str] | str | None):
    async def dependency(
        request: Request,
        bundle: RequestAuth = Depends(get_request_auth),
    ) -> AuthContext:
        for group in required:
            await _integration(request).assert_permissions(
                bundle.context,
                group,
                request=request,
            )
        return bundle.context

    return dependency
