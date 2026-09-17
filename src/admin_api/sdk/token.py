from __future__ import annotations

import base64
import binascii
import json
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError

from admin_api.exceptions import InvalidTokenException


class TokenPayload(BaseModel):
    """Claims of an admin_api access token."""

    user_id: UUID
    role: str
    service_name: str | None = None
    permissions: list[str] = Field(default_factory=list)
    iat: int | None = None
    expires_at: datetime | None = None


def decode_token_payload(token: str) -> TokenPayload:
    """Decode an admin_api access token payload without verifying its signature.

    The signature is intentionally not verified here, since the token is validated by admin_api
    itself - the very same token is sent to ``GET /users/me`` and forwarded to admin_api
    afterwards, so its claims can be trusted only because admin_api accepted the token.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise InvalidTokenException("JWT Token is invalid")

    encoded_payload = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        decoded_payload = base64.urlsafe_b64decode(encoded_payload)
        data = json.loads(decoded_payload)
    except (binascii.Error, ValueError, UnicodeDecodeError) as exc:
        raise InvalidTokenException("JWT Token is invalid") from exc

    if not isinstance(data, dict):
        raise InvalidTokenException("JWT Token is invalid")

    try:
        return TokenPayload.model_validate(data)
    except ValidationError as exc:
        raise InvalidTokenException("JWT Token is invalid") from exc
