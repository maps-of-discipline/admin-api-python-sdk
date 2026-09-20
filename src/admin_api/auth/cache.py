from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Protocol

from admin_api.api.users.schemas import FullUser, UserPermissions


@dataclass(frozen=True)
class AuthSnapshot:
    user: FullUser
    permissions: UserPermissions


class AuthCache(Protocol):
    def get(self, token_hash: str) -> AuthSnapshot | None: ...

    def get_stale(self, token_hash: str) -> AuthSnapshot | None: ...

    def set(self, token_hash: str, snapshot: AuthSnapshot) -> None: ...

    def drop(self, token_hash: str) -> None: ...


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class NoCache:
    def get(self, token_hash: str) -> AuthSnapshot | None:
        return None

    def get_stale(self, token_hash: str) -> AuthSnapshot | None:
        return None

    def set(self, token_hash: str, snapshot: AuthSnapshot) -> None:
        return None

    def drop(self, token_hash: str) -> None:
        return None


@dataclass
class _TtlEntry:
    snapshot: AuthSnapshot
    expires_at: float


class TtlCache:
    def __init__(self, ttl_seconds: float = 30) -> None:
        self._ttl_seconds = ttl_seconds
        self._store: dict[str, _TtlEntry] = {}

    def get(self, token_hash: str) -> AuthSnapshot | None:
        entry = self._store.get(token_hash)
        if entry is None or entry.expires_at <= time.monotonic():
            return None
        return entry.snapshot

    def get_stale(self, token_hash: str) -> AuthSnapshot | None:
        entry = self._store.get(token_hash)
        if entry is None:
            return None
        return entry.snapshot

    def set(self, token_hash: str, snapshot: AuthSnapshot) -> None:
        self._store[token_hash] = _TtlEntry(
            snapshot=snapshot,
            expires_at=time.monotonic() + self._ttl_seconds,
        )

    def drop(self, token_hash: str) -> None:
        self._store.pop(token_hash, None)
