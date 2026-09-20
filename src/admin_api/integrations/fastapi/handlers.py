from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from admin_api.exceptions import InvalidTokenException, PermissionDenied, TokenNotProvided


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(TokenNotProvided)
    async def token_not_provided(_request, exc: TokenNotProvided) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=401)

    @app.exception_handler(InvalidTokenException)
    async def invalid_token(_request, exc: InvalidTokenException) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=401)

    @app.exception_handler(PermissionDenied)
    async def permission_denied(_request, exc: PermissionDenied) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=403)
