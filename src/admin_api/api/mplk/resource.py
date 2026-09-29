from __future__ import annotations

from typing import Any

from pydantic import TypeAdapter

from admin_api.api.request import Operation


class Mplk:
    def get_groups(self, search: str | None = None) -> Operation[Any]:
        return Operation(
            "GET",
            "/api/v1/mplk/groups",
            adapter=TypeAdapter(Any),
            params={"search": search},
        )

    def get_students(self, group: str, search: str | None = None) -> Operation[Any]:
        return Operation(
            "GET",
            "/api/v1/mplk/students",
            adapter=TypeAdapter(Any),
            params={"group": group, "search": search},
        )

    def get_schedule(self, group: str, is_session: bool = False) -> Operation[Any]:
        return Operation(
            "GET",
            "/api/v1/mplk/schedule",
            adapter=TypeAdapter(Any),
            params={"group": group, "is_session": is_session},
        )

    def get_semester(self) -> Operation[Any]:
        return Operation("GET", "/api/v1/mplk/semester", adapter=TypeAdapter(Any))

    def get_session(self) -> Operation[Any]:
        return Operation("GET", "/api/v1/mplk/session", adapter=TypeAdapter(Any))

    def get_user_info(self) -> Operation[Any]:
        return Operation("GET", "/api/v1/mplk/user-info", adapter=TypeAdapter(Any))

    def get_staff(
        self,
        search: str | None = None,
        division: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Operation[Any]:
        return Operation(
            "GET",
            "/api/v1/mplk/staff",
            adapter=TypeAdapter(Any),
            params={
                "search": search,
                "division": division,
                "page": page,
                "per_page": per_page,
            },
        )

    def generic(
        self,
        url: str,
        method: str = "GET",
        *,
        headers: dict[str, str] | None = None,
        query: dict[str, Any] | None = None,
        body: Any = None,
    ) -> Operation[Any]:
        return Operation(
            "POST",
            "/api/v1/mplk/generic",
            adapter=TypeAdapter(Any),
            json={
                "body": {
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "query": query,
                    "body": body,
                },
            },
        )
