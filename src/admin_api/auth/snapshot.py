from __future__ import annotations

import httpx

from admin_api.auth.cache import AuthCache, AuthSnapshot, token_hash
from admin_api.auth.fail import FailPolicy
from admin_api.exceptions import ApiError, InvalidTokenException


class SnapshotStore:
    def __init__(self, cache: AuthCache, fail_policy: FailPolicy) -> None:
        self._cache = cache
        self._fail_policy = fail_policy

    def get(self, token: str) -> AuthSnapshot | None:
        return self._cache.get(token_hash(token))

    def set(self, token: str, snapshot: AuthSnapshot) -> None:
        self._cache.set(token_hash(token), snapshot)

    def recover(self, token: str, error: Exception) -> AuthSnapshot:
        key = token_hash(token)
        if isinstance(error, InvalidTokenException):
            self._cache.drop(key)
            raise error
        recoverable = isinstance(error, httpx.HTTPError) or (isinstance(error, ApiError) and error.status_code >= 500)
        if recoverable and self._fail_policy is FailPolicy.USE_STALE:
            stale = self._cache.get_stale(key)
            if stale is not None:
                return stale
        raise error
