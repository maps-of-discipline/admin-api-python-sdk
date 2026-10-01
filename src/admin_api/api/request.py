from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Generic, TypeVar
from urllib.parse import quote

import httpx
from pydantic import TypeAdapter

T = TypeVar("T")


def _encode_path_segment(value: Any) -> str:
    segment = quote(str(value), safe="")
    if segment in (".", ".."):
        return segment.replace(".", "%2E")
    return segment


class Operation(Generic[T]):
    def __init__(
        self,
        method: str,
        url: str,
        *,
        adapter: TypeAdapter[T],
        auth: bool = True,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        headers: Mapping[str, str] | None = None,
        path_params: Mapping[str, Any] | None = None,
    ) -> None:
        self._method = method
        self._url = url
        self._adapter = adapter
        self.auth = auth
        self._params = params
        self._json = json
        self._headers = headers
        self._path_params = path_params

    def build(self) -> httpx.Request:
        url = self._url
        if self._path_params:
            encoded = {key: _encode_path_segment(value) for key, value in self._path_params.items()}
            url = url.format(**encoded)
        params = None
        if self._params:
            params = {key: value for key, value in self._params.items() if value is not None}
        return httpx.Request(
            self._method,
            url,
            params=params,
            json=self._json,
            headers=self._headers,
        )

    def parse(self, response: httpx.Response) -> T:
        if not response.content:
            return self._adapter.validate_python(None)
        return self._adapter.validate_python(response.json())
