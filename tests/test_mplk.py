from __future__ import annotations

import httpx

from admin_api import SyncApi
from admin_api.api.mplk import (
    MPLKGetGroupsResponse,
    MPLKGetScheduleResponse,
    MPLKGetStaffResponse,
    MPLKGetStudentsResponse,
)


def test_mplk_group_student_and_schedule_operations():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer token"
        if request.url.path == "/api/v1/mplk/groups":
            assert request.url.params["search"] == "ИВТ"
            return httpx.Response(200, json={"groups": ["ИВТ-1"]})
        if request.url.path == "/api/v1/mplk/students":
            assert request.url.params["group"] == "ИВТ-1"
            assert request.url.params["search"] == "Анна"
            return httpx.Response(200, json={"students": [{"name": "Анна"}]})
        assert request.url.path == "/api/v1/mplk/schedule"
        assert request.url.params["group"] == "ИВТ-1"
        assert request.url.params["is_session"] == "true"
        return httpx.Response(200, json={"schedule": {"days": []}})

    with SyncApi("http://admin-api.local", token="token", transport=httpx.MockTransport(handler)) as api:
        groups = api.send(api.mplk.get_groups(search="ИВТ"))
        students = api.send(api.mplk.get_students("ИВТ-1", search="Анна"))
        schedule = api.send(api.mplk.get_schedule("ИВТ-1", is_session=True))

    assert isinstance(groups, MPLKGetGroupsResponse)
    assert groups.groups == ["ИВТ-1"]
    assert isinstance(students, MPLKGetStudentsResponse)
    assert students.students == [{"name": "Анна"}]
    assert isinstance(schedule, MPLKGetScheduleResponse)
    assert schedule.schedule == {"days": []}


def test_mplk_staff_query_and_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/mplk/staff"
        assert dict(request.url.params) == {
            "search": "Анна",
            "division": "ИТ",
            "page": "2",
            "per_page": "25",
        }
        return httpx.Response(200, json={"staff": {"data": [], "total": 0}})

    with SyncApi("http://admin-api.local", token="token", transport=httpx.MockTransport(handler)) as api:
        result = api.send(api.mplk.get_staff(search="Анна", division="ИТ", page=2, per_page=25))

    assert isinstance(result, MPLKGetStaffResponse)
    assert result.staff == {"data": [], "total": 0}


def test_mplk_semester_session_and_user_info_responses():
    bodies = {
        "/api/v1/mplk/semester": {"semester": {"number": 1}},
        "/api/v1/mplk/session": {"session": {"exams": []}},
        "/api/v1/mplk/user-info": {"user": {"user": {"id": 42}}},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=bodies[request.url.path])

    with SyncApi("http://admin-api.local", token="token", transport=httpx.MockTransport(handler)) as api:
        semester = api.send(api.mplk.get_semester())
        session = api.send(api.mplk.get_session())
        user_info = api.send(api.mplk.get_user_info())

    assert semester.semester == {"number": 1}
    assert session.session == {"exams": []}
    assert user_info.user == {"user": {"id": 42}}
