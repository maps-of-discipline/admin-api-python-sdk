from __future__ import annotations

from typing import Any, Protocol


class TokenParser(Protocol):
    def get_token(self, request: Any) -> str | None: ...


class BearerTokenParser:
    def __init__(self, header: str = "Authorization", scheme: str = "Bearer") -> None:
        self.header = header
        self.scheme = scheme

    def get_token(self, request: Any) -> str | None:
        headers = getattr(request, "headers", None)
        if headers is None:
            return None
        raw = headers.get(self.header) or headers.get(self.header.lower())
        if not raw:
            return None
        prefix = f"{self.scheme} "
        if raw.lower().startswith(prefix.lower()):
            token = raw[len(prefix) :].strip()
            return token or None
        return None
