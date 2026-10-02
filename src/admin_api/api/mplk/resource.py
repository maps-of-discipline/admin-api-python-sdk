from __future__ import annotations

from typing import Any

from pydantic import TypeAdapter

from admin_api.api.mplk.schemas import (
    MPLKGetGroupsResponse,
    MPLKGetScheduleResponse,
    MPLKGetSemesterResponse,
    MPLKGetSessionResponse,
    MPLKGetStaffResponse,
    MPLKGetStudentsResponse,
    MPLKGetUserInfoResponse,
)
from admin_api.api.request import Operation


class Mplk:
    def get_groups(self, search: str | None = None) -> Operation[MPLKGetGroupsResponse]:
        return Operation(
            "GET",
            "/api/v1/mplk/groups",
            adapter=TypeAdapter(MPLKGetGroupsResponse),
            params={"search": search},
        )

    def get_students(self, group: str, search: str | None = None) -> Operation[MPLKGetStudentsResponse]:
        return Operation(
            "GET",
            "/api/v1/mplk/students",
            adapter=TypeAdapter(MPLKGetStudentsResponse),
            params={"group": group, "search": search},
        )

    def get_schedule(self, group: str, is_session: bool = False) -> Operation[MPLKGetScheduleResponse]:
        return Operation(
            "GET",
            "/api/v1/mplk/schedule",
            adapter=TypeAdapter(MPLKGetScheduleResponse),
            params={"group": group, "is_session": is_session},
        )

    def get_semester(self) -> Operation[MPLKGetSemesterResponse]:
        return Operation("GET", "/api/v1/mplk/semester", adapter=TypeAdapter(MPLKGetSemesterResponse))

    def get_session(self) -> Operation[MPLKGetSessionResponse]:
        return Operation("GET", "/api/v1/mplk/session", adapter=TypeAdapter(MPLKGetSessionResponse))

    def get_user_info(self) -> Operation[MPLKGetUserInfoResponse]:
        return Operation("GET", "/api/v1/mplk/user-info", adapter=TypeAdapter(MPLKGetUserInfoResponse))

    def get_staff(
        self,
        search: str | None = None,
        division: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Operation[MPLKGetStaffResponse]:
        return Operation(
            "GET",
            "/api/v1/mplk/staff",
            adapter=TypeAdapter(MPLKGetStaffResponse),
            params={
                "search": search,
                "division": division,
                "page": page,
                "per_page": per_page,
            },
        )

    def generic(self, data: dict[str, Any]) -> Operation[Any]:
        return Operation(
            "POST",
            "/api/v1/mplk/generic",
            adapter=TypeAdapter(Any),
            json=data,
        )
