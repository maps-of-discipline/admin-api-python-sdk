from __future__ import annotations

from flask import Flask, Request

from admin_api.api.client import SyncApi
from admin_api.auth.cache import AuthCache
from admin_api.auth.catalog import CatalogStrategy
from admin_api.auth.fail import FailPolicy
from admin_api.auth.manager import AdminApiAuth
from admin_api.auth.token import BearerTokenParser, TokenParser
from admin_api.exceptions import InvalidTokenException, PermissionDenied, TokenNotProvided

FLASK_EXTENSION_NAME = "admin_api"


class AdminApiFlask(AdminApiAuth):
    def __init__(
        self,
        token_parser: TokenParser | None = None,
        api: SyncApi | None = None,
        *,
        base_url: str | None = None,
        timeout_ms: int = 300,
        service_name: str | None = None,
        cache: AuthCache | None = None,
        fail_policy: FailPolicy = FailPolicy.DENY,
        catalog: CatalogStrategy | None = None,
    ) -> None:
        super().__init__(
            api,
            base_url=base_url,
            timeout_ms=timeout_ms,
            service_name=service_name,
            cache=cache,
            fail_policy=fail_policy,
            catalog=catalog,
        )
        self.token_parser: TokenParser = token_parser or BearerTokenParser()

    def init_app(self, app: Flask, *, exception_handlers: bool = True) -> None:
        app.extensions[FLASK_EXTENSION_NAME] = self
        self.sync_catalog()
        if exception_handlers:
            _install_exception_handlers(app)

    def parse_token(self, request: Request) -> str:
        token = self.token_parser.get_token(request)
        if not token:
            raise TokenNotProvided
        return token


def _install_exception_handlers(app: Flask) -> None:
    @app.errorhandler(TokenNotProvided)
    def token_not_provided(exc: TokenNotProvided):
        return {"detail": str(exc)}, 401

    @app.errorhandler(InvalidTokenException)
    def invalid_token(exc: InvalidTokenException):
        return {"detail": str(exc)}, 401

    @app.errorhandler(PermissionDenied)
    def permission_denied(exc: PermissionDenied):
        return {"detail": str(exc)}, 403
