from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class MPLKGetGroupsResponse(BaseModel):
    groups: Any


class MPLKGetStudentsResponse(BaseModel):
    students: Any


class MPLKGetScheduleResponse(BaseModel):
    schedule: dict[str, Any]


class MPLKGetSemesterResponse(BaseModel):
    semester: dict[str, Any]


class MPLKGetSessionResponse(BaseModel):
    session: dict[str, Any]


class MPLKGetUserInfoResponse(BaseModel):
    user: dict[str, Any]


class MPLKGetStaffResponse(BaseModel):
    staff: Any
