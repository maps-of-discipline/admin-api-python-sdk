from __future__ import annotations

from uuid import UUID

import httpx
import pytest
from pydantic import ValidationError

from admin_api import SyncApi
from admin_api.api.units import UnitResponse, Units, UnitTreeResponse, UnitType

ROOT_ID = UUID(int=1)
CHILD_ID = UUID(int=2)
TYPE_ID = UUID(int=3)


def test_units_tree_flat_and_unit_types():
    tree = {
        "id": str(ROOT_ID),
        "title": "University",
        "type": {"id": str(TYPE_ID), "title": "university"},
        "parent_unit_id": None,
        "has_children": True,
        "children": [
            {
                "id": str(CHILD_ID),
                "title": "IT",
                "type": {"id": str(TYPE_ID), "title": "faculty"},
                "parent_unit_id": str(ROOT_ID),
                "has_children": False,
                "children": [],
            },
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/unit-types":
            return httpx.Response(200, json=[{"id": str(TYPE_ID), "title": "faculty"}])
        assert request.url.path == "/api/v1/units"
        if request.url.params["flat"] == "true":
            assert request.url.params["search"] == "IT"
            assert request.url.params.get_list("type_ids") == [str(TYPE_ID), str(CHILD_ID)]
            child = {key: value for key, value in tree["children"][0].items() if key != "children"}
            return httpx.Response(200, json=[child])
        assert request.url.params["max_depth"] == "2"
        assert request.url.params["root_id"] == str(ROOT_ID)
        return httpx.Response(200, json=[tree])

    with SyncApi("http://admin-api.local", token="token", transport=httpx.MockTransport(handler)) as api:
        roots = api.send(api.units.get_all(max_depth=2, root_id=ROOT_ID))
        flat = api.send(api.units.get_all(flat=True, search="IT", type_ids=[TYPE_ID, CHILD_ID]))
        types = api.send(api.unit_types.get_all())

    assert isinstance(roots[0], UnitTreeResponse)
    assert isinstance(roots[0].children[0], UnitTreeResponse)
    assert isinstance(flat[0], UnitResponse)
    assert types == [UnitType(id=TYPE_ID, title="faculty")]


def test_units_reject_search_outside_flat_mode():
    with pytest.raises(ValidationError, match="only supported for flat responses"):
        Units().get_all(search="IT")
