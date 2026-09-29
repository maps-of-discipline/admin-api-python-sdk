from __future__ import annotations

from pydantic import TypeAdapter

from admin_api.api.common import dump
from admin_api.api.dto import (
    MessengerLinkRequest,
    MessengerResponse,
    MessengerUnlinkResponse,
    User,
)
from admin_api.api.request import Operation


class Messengers:
    def list(self) -> Operation[list[MessengerResponse]]:
        return Operation("GET", "/api/v1/messengers", adapter=TypeAdapter(list[MessengerResponse]))

    def link(self, messenger_type: str, id_token: str) -> Operation[MessengerResponse]:
        body = MessengerLinkRequest(messenger_type=messenger_type, id_token=id_token)
        return Operation(
            "POST",
            "/api/v1/messengers/link",
            adapter=TypeAdapter(MessengerResponse),
            json=dump(body),
        )

    def unlink(self, messenger_type: str) -> Operation[MessengerUnlinkResponse]:
        return Operation(
            "DELETE",
            "/api/v1/messengers/{messenger_type}",
            adapter=TypeAdapter(MessengerUnlinkResponse),
            path_params={"messenger_type": messenger_type},
        )

    def get_user(self, messenger_type: str, messenger_user_id: str) -> Operation[User]:
        """Requires the messenger bot token instead of a user JWT."""
        return Operation(
            "GET",
            "/api/v1/messengers/user/{messenger_type}/{messenger_user_id}",
            adapter=TypeAdapter(User),
            path_params={"messenger_type": messenger_type, "messenger_user_id": messenger_user_id},
        )
