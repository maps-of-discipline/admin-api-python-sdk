import inspect
from functools import wraps
from typing import get_origin, get_type_hints

from flask import current_app, request

from admin_api.integrations.flask import FLASK_EXTENSION_NAME, AdminApiFlask
from admin_api.sdk.auth_context import AuthContext


def _is_auth_context(annotation: object) -> bool:
    return annotation is AuthContext or get_origin(annotation) is AuthContext


def _find_auth_context_parameter(f) -> str | None:
    """Name of the view parameter to inject AuthContext into, if any.

    Annotations are resolved with ``get_type_hints`` so that postponed annotations
    (``from __future__ import annotations``) and ``AuthContext[SyncApi]`` work too.
    """
    try:
        resolved = get_type_hints(f)
    except (NameError, TypeError):
        resolved = {}

    for name, param in inspect.signature(f).parameters.items():
        if _is_auth_context(resolved.get(name, param.annotation)):
            return name
    return None


def require(*required: str):
    """Authentication decorator for route handlers.

    Args:
        *required: Variable length argument of permissions.

    This decorator validates the user's authentication token and checks if the user
    has the required permissions to access the endpoint. It also automatically injects
    the AuthContext object into the decorated function's parameters if there is
    a parameter annotated with the AuthContext type.
    """

    def decorator(f):
        context_parameter = _find_auth_context_parameter(f)

        @wraps(f)
        def decorated(*args, **kwargs):
            auth_manager: AdminApiFlask = current_app.extensions[FLASK_EXTENSION_NAME]

            token = auth_manager.parse_token(request)
            auth_context = auth_manager.check(required, token)

            if context_parameter is not None:
                kwargs[context_parameter] = auth_context

            return f(*args, **kwargs)

        return decorated

    return decorator
