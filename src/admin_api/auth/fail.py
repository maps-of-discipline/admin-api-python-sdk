from __future__ import annotations

from enum import StrEnum


class FailPolicy(StrEnum):
    DENY = "deny"
    USE_STALE = "use_stale"
