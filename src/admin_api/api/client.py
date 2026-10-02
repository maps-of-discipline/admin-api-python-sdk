from __future__ import annotations

from typing import Any, Self, TypeVar, cast

import httpx

from admin_api.api.mplk.resource import Mplk
from admin_api.api.request import Operation
from admin_api.api.services.resource import Services
from admin_api.api.users.resource import Users
from admin_api.exceptions import ApiError, InvalidTokenException, TokenNotProvided

T = TypeVar("T")


class BaseApi:
    users: Users = Users()
    mplk: Mplk = Mplk()
    services: Services = Services()

    def __init__(
        self,
        base_url: str,
        *,
        token: str | None = None,
        timeout: float = 5.0,
        transport: httpx.BaseTransport | httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout
        self._transport = transport
        self._owns_client = True
        self._http = self._create_client()

    def _create_client(self) -> httpx.Client | httpx.AsyncClient:
        raise NotImplementedError

    def bind(self, token: str) -> Self:
        bound = object.__new__(type(self))
        bound.__dict__.update(self.__dict__)
        bound._token = token
        bound._owns_client = False
        return bound

    def _prepare(self, operation: Operation[T]) -> httpx.Request:
        request = operation.build()
        headers = httpx.Headers(request.headers)
        if operation.auth:
            if not self._token:
                raise TokenNotProvided
            headers["Authorization"] = f"Bearer {self._token}"
        return self._http.build_request(
            request.method,
            str(request.url),
            headers=headers,
            content=request.content,
            extensions=request.extensions,
        )

    def _read(self, operation: Operation[T], response: httpx.Response) -> T:
        self._raise_for_api_error(response)
        return operation.parse(response)

    @staticmethod
    def _raise_for_api_error(response: httpx.Response) -> None:
        if response.status_code == 401:
            raise InvalidTokenException(BaseApi._error_message(response))
        if response.is_success:
            return
        payload = BaseApi._error_payload(response)
        detail = payload.get("detail", "")
        message = detail if isinstance(detail, str) and detail else None
        raise ApiError(
            message,
            status_code=response.status_code,
            error_code=str(payload.get("error_code") or ""),
            detail=detail or "",
            errors=payload.get("errors") or "",
        )

    @staticmethod
    def _error_payload(response: httpx.Response) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError:
            return {"detail": response.text}
        if isinstance(data, dict):
            return data
        return {"detail": data}

    @staticmethod
    def _error_message(response: httpx.Response) -> str:
        detail = BaseApi._error_payload(response).get("detail")
        if isinstance(detail, str) and detail:
            return detail
        return InvalidTokenException.message


class SyncApi(BaseApi):
    _http: httpx.Client

    def _create_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            transport=cast(httpx.BaseTransport | None, self._transport),
        )

    def send(self, operation: Operation[T]) -> T:
        response = self._http.send(self._prepare(operation))
        try:
            return self._read(operation, response)
        finally:
            response.close()

    def close(self) -> None:
        if self._owns_client:
            self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncApi(BaseApi):
    _http: httpx.AsyncClient

    def _create_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            transport=cast(httpx.AsyncBaseTransport | None, self._transport),
        )

    def _reopen(self) -> None:
        if self._http.is_closed:
            self._http = self._create_client()

    async def send(self, operation: Operation[T]) -> T:
        response = await self._http.send(self._prepare(operation))
        try:
            return self._read(operation, response)
        finally:
            await response.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()
