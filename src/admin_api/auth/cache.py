from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from threading import Lock
from typing import Protocol

from cachetools import LRUCache

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
    def __init__(self, ttl_seconds: float = 30, stale_ttl_seconds: float = 300, maxsize: int = 1024) -> None:
        self._ttl_seconds = ttl_seconds
        self._stale_ttl_seconds = stale_ttl_seconds
        self._store: LRUCache[str, _TtlEntry] = LRUCache(maxsize=maxsize)
        self._lock = Lock()

    def _read(self, token_hash: str, *, allow_stale: bool) -> AuthSnapshot | None:
        with self._lock:
            entry = self._store.get(token_hash)
            if entry is None:
                return None
            now = time.monotonic()
            if now >= entry.expires_at + self._stale_ttl_seconds:
                self._store.pop(token_hash, None)
                return None
            if not allow_stale and now >= entry.expires_at:
                return None
            return entry.snapshot

    def get(self, token_hash: str) -> AuthSnapshot | None:
        return self._read(token_hash, allow_stale=False)

    def get_stale(self, token_hash: str) -> AuthSnapshot | None:
        return self._read(token_hash, allow_stale=True)

    def set(self, token_hash: str, snapshot: AuthSnapshot) -> None:
        with self._lock:
            self._store[token_hash] = _TtlEntry(snapshot=snapshot, expires_at=time.monotonic() + self._ttl_seconds)

    def drop(self, token_hash: str) -> None:
        with self._lock:
            self._store.pop(token_hash, None)
