from __future__ import annotations

from dataclasses import dataclass

from flask import current_app, g, request

from admin_api.api.client import SyncApi
from admin_api.auth.context import AuthContext
from admin_api.integrations.flask.extension import FLASK_EXTENSION_NAME, AdminApiFlask

G_KEY = "admin_api_request_auth"


@dataclass
class RequestAuth:
    context: AuthContext
    api: SyncApi


def _integration() -> AdminApiFlask:
    integration = current_app.extensions.get(FLASK_EXTENSION_NAME)
    if not isinstance(integration, AdminApiFlask):
        raise RuntimeError("AdminApiFlask is not initialized. Call init_app(app).")
    return integration


def get_request_auth() -> RequestAuth:
    bundle = g.get(G_KEY)
    if isinstance(bundle, RequestAuth):
        return bundle
    integration = _integration()
    token = integration.parse_token(request)
    context, api = integration.load(token)
    bundle = RequestAuth(context=context, api=api)
    setattr(g, G_KEY, bundle)
    return bundle
