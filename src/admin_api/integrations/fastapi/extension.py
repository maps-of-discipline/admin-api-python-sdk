from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from admin_api.api.client import AsyncApi
from admin_api.auth.cache import AuthCache
from admin_api.auth.catalog import CatalogStrategy
from admin_api.auth.fail import FailPolicy
from admin_api.auth.manager import AsyncAdminApiAuth
from admin_api.auth.token import BearerTokenParser, TokenParser
from admin_api.exceptions import TokenNotProvided
from admin_api.integrations.fastapi.handlers import install_exception_handlers

STATE_KEY = "admin_api"


class AdminApiFastAPI(AsyncAdminApiAuth):
    def __init__(
        self,
        token_parser: TokenParser | None = None,
        api: AsyncApi | None = None,
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

    def init_app(self, app: FastAPI, *, exception_handlers: bool = True) -> None:
        setattr(app.state, STATE_KEY, self)
        if exception_handlers:
            install_exception_handlers(app)

        previous = app.router.lifespan_context

        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncIterator[None]:
            try:
                if self._owns_root_api and self._root_api is not None:
                    self._root_api._reopen()
                await self.sync_catalog()
                async with previous(app):
                    yield
            finally:
                await self.aclose()

        app.router.lifespan_context = lifespan

    def parse_token(self, request: Request) -> str:
        token = self.token_parser.get_token(request)
        if not token:
            raise TokenNotProvided
        return token
