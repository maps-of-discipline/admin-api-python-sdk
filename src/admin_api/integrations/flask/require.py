from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, get_type_hints

from flask import request

from admin_api.api.client import SyncApi
from admin_api.auth.context import AuthContext
from admin_api.integrations.flask.request_auth import _integration, get_request_auth


def require(*permissions: str):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            bundle = get_request_auth()
            _integration().assert_permissions(bundle.context, permissions, request=request)
            _inject(f, kwargs, {AuthContext: bundle.context, SyncApi: bundle.api})
            return f(*args, **kwargs)

        return wrapper

    return decorator


def _inject(func: Any, kwargs: dict[str, Any], values: dict[type, object]) -> None:
    try:
        hints = get_type_hints(func)
    except (NameError, TypeError):
        hints = {
            name: parameter.annotation
            for name, parameter in inspect.signature(func).parameters.items()
            if parameter.annotation is not inspect.Parameter.empty
        }
    for name, hint in hints.items():
        if name in kwargs:
            continue
        value = values.get(hint)
        if value is not None:
            kwargs[name] = value
