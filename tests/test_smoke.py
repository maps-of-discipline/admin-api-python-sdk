import pytest


@pytest.mark.parametrize(
    "path",
    [
        "admin_api",
        "admin_api.auth",
        "admin_api.auth.manager",
        "admin_api.auth.context",
        "admin_api.integrations.flask",
        "admin_api.integrations.fastapi",
        "admin_api.api",
        "admin_api.api.users",
        "admin_api.api.mplk",
    ],
)
def test_import(path):
    module = __import__(path)
    assert module is not None
