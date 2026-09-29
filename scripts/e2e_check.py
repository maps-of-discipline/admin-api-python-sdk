"""End-to-end check of the SDK against a running Admin API.

Creates a throwaway user, service, roles, permissions, orders and rules, calls every SDK method and
removes what it created. Run it only against a local or test instance:

    ADMIN_API_URL=http://127.0.0.1:8001 ADMIN_API_BOT_TOKEN=... uv run python scripts/e2e_check.py
"""

import asyncio
import os
import sys
import traceback
import uuid

from admin_api import AdminApiAuth, AsyncApi, SyncApi
from admin_api.auth import ApiPermissionCatalog, AsyncApiPermissionCatalog, CreateUnexisted, FullSync
from admin_api.exceptions import ApiError

BASE = os.environ.get("ADMIN_API_URL", "http://127.0.0.1:8001")
BOT_TOKEN = os.environ.get("ADMIN_API_BOT_TOKEN", "local-bot-token")
results: list[tuple[str, str, str]] = []


def step(name, fn, expect_error: int | None = None):
    try:
        value = fn()
        if expect_error is not None:
            results.append((name, "FAIL", f"expected HTTP {expect_error}, got {value!r}"[:160]))
            return None
        results.append((name, "OK", repr(value)[:110]))
        return value
    except ApiError as error:
        if expect_error is not None and error.status_code == expect_error:
            results.append((name, "OK", f"expected ApiError {error.status_code}: {error}"[:110]))
            return None
        results.append((name, "FAIL", f"ApiError {error.status_code} {error.error_code} {error.detail!r}"[:200]))
    except Exception as error:  # noqa: BLE001
        results.append((name, "FAIL", f"{type(error).__name__}: {error}"[:300]))
        traceback.print_exc()
    return None


suffix = uuid.uuid4().hex[:8]
email = f"sdk-{suffix}@example.test"
service_name = f"sdk-e2e-{suffix}"

with SyncApi(BASE, timeout=30) as anon:
    step(
        "users.sign_up",
        lambda: anon.send(
            anon.users.sign_up(name="Ivan", surname="Petrov", patronymic="S", email=email, password="Passw0rd!"),
        ),
    )
    challenge = step("users.login_by_password", lambda: anon.send(anon.users.login_by_password(email, "Passw0rd!")))
    step(
        "users.login_by_email (no email credential -> 404)",
        lambda: anon.send(anon.users.login_by_email(email)),
        expect_error=404,
    )
    auth = step(
        "users.verify_auth_code",
        lambda: anon.send(anon.users.verify_auth_code(challenge.pre_auth_token, None)),
    )
    auth = step("users.refresh", lambda: anon.send(anon.users.refresh(auth))) or auth
    step("assignment_rules.get_metadata (no token)", lambda: sorted(anon.send(anon.assignment_rules.get_metadata())))
    step(
        "users.login_by_password wrong password",
        lambda: anon.send(anon.users.login_by_password(email, "wrong")),
        expect_error=400,
    )

    api = anon.bind(auth.access_token)
    me = step("users.get_me", lambda: api.send(api.users.get_me()))
    user_id = me.id
    step("users.get", lambda: api.send(api.users.get(user_id)))
    step("users.filter", lambda: api.send(api.users.filter(email=email)))
    step("users.get_accounts", lambda: api.send(api.users.get_accounts()))

    service = step("services.create", lambda: api.send(api.services.create(name=service_name, verbose_name="E2E")))
    sid = service.id
    step("services.get", lambda: api.send(api.services.get(sid)))
    step("services.filter", lambda: api.send(api.services.filter(service_name=service_name)))
    step("services.update", lambda: api.send(api.services.update(sid, name=service_name, verbose_name="E2E 2")))
    step("services.update_icon", lambda: api.send(api.services.update_icon(sid, "mdi-account")))
    step("services.update_color", lambda: api.send(api.services.update_color(sid, "#112233")))

    role = step("service_roles.create", lambda: api.send(api.service_roles.create(role="admin", service_id=sid)))
    rid = role.id
    step("service_roles.get", lambda: api.send(api.service_roles.get(rid)))
    step("service_roles.filter", lambda: api.send(api.service_roles.filter(service_name=service_name)))
    step(
        "service_roles.update",
        lambda: api.send(api.service_roles.update(rid, role="admin", service_id=sid, verbose_name="Admins")),
    )

    perm = step(
        "permissions.create",
        lambda: api.send(api.permissions.create(service_id=sid, title="user.read", verbose_name="Read users")),
    )
    pid = perm.id
    step("permissions.get", lambda: api.send(api.permissions.get(pid)))
    step("permissions.filter", lambda: api.send(api.permissions.filter(service_name=service_name)))
    step(
        "permissions.update",
        lambda: api.send(api.permissions.update(pid, service_id=sid, title="user.read", verbose_name="Read")),
    )
    step("service_roles.assign_permission", lambda: api.send(api.service_roles.assign_permission(rid, pid)))
    step("service_roles.get_permissions", lambda: api.send(api.service_roles.get_permissions(rid)))
    tmp = api.send(api.permissions.create(service_id=sid, title="tmp.perm", verbose_name="tmp"))
    step("service_roles.assign_permission(tmp)", lambda: api.send(api.service_roles.assign_permission(rid, tmp.id)))
    step("service_roles.revoke_permission", lambda: api.send(api.service_roles.revoke_permission(rid, tmp.id)))
    step("permissions.delete", lambda: api.send(api.permissions.delete(tmp.id)))

    unit_types = step("units.get_types", lambda: api.send(api.units.get_types()))
    tree = step("units.list", lambda: api.send(api.units.list(max_depth=2)))
    flat = step("units.list_flat", lambda: api.send(api.units.list_flat(max_depth=1)))
    unit_id = flat[0].id if flat else None
    if unit_types:
        step("units.list_flat(type_ids)", lambda: len(api.send(api.units.list_flat(type_ids=[unit_types[0].id]))))

    scope = [{"type": "unit", "unit_id": str(unit_id)}] if unit_id else None
    usr = step(
        "user_service_roles.create",
        lambda: api.send(api.user_service_roles.create(user_id=user_id, service_roles_id=rid, scope=scope)),
    )
    usr_id = usr.id
    step("user_service_roles.get", lambda: api.send(api.user_service_roles.get(usr_id)))
    step(
        "user_service_roles.update",
        lambda: api.send(api.user_service_roles.update(usr_id, user_id=user_id, service_roles_id=rid, scope=scope)),
    )
    step("users.get_permissions", lambda: api.send(api.users.get_permissions(service_name)))
    step("users.get_roles_from_service", lambda: api.send(api.users.get_roles_from_service(user_id, service_name)))

    step("users.assign_service", lambda: api.send(api.users.assign_service(user_id, sid)))
    step("users.get_managed_services", lambda: [s.name for s in api.send(api.users.get_managed_services()).services])
    step("users.revoke_service", lambda: api.send(api.users.revoke_service(user_id, sid)))

    order = step(
        "orders.create",
        lambda: api.send(api.orders.create(target_role="staff", comment="e2e", user_id=user_id, service_id=sid)),
    )
    oid = order.id if order else None
    step("orders.get", lambda: api.send(api.orders.get(oid)))
    step("orders.list", lambda: len(api.send(api.orders.list(service_id=sid))))
    step(
        "orders.update",
        lambda: api.send(
            api.orders.update(oid, target_role="admin", comment="e2e upd", user_id=user_id, service_id=sid),
        ),
    )
    step("orders.approve(False)", lambda: api.send(api.orders.approve(oid, approve=False)))
    step("orders.delete (approve removed it -> 404)", lambda: api.send(api.orders.delete(oid)), expect_error=404)

    rule = step(
        "assignment_rules.create",
        lambda: api.send(
            api.assignment_rules.create(
                title="E2E rule",
                service_role_id=rid,
                expression={
                    "kind": "predicate",
                    "field": "account_type",
                    "predicate": {"operator": "equal", "value": "stud"},
                },
            ),
        ),
    )
    rule_id = rule.id if rule else None
    step("assignment_rules.get", lambda: api.send(api.assignment_rules.get(rule_id)))
    step("assignment_rules.list", lambda: len(api.send(api.assignment_rules.list(service_role_id=rid))))
    step("assignment_rules.update", lambda: api.send(api.assignment_rules.update(rule_id, enabled=False)))
    step("assignment_rules.delete", lambda: api.send(api.assignment_rules.delete(rule_id)))

    step("messengers.list", lambda: api.send(api.messengers.list()))
    step(
        "messengers.link (bad id_token -> 422)",
        lambda: api.send(api.messengers.link("telegram", "bad")),
        expect_error=422,
    )
    bot = SyncApi(BASE, token=BOT_TOKEN)
    step(
        "messengers.get_user (bot token, unknown -> 404)",
        lambda: bot.send(bot.messengers.get_user("telegram", "1")),
        expect_error=404,
    )
    bot.close()

    # AdminApiAuth end-to-end + permission catalog
    auth_manager = AdminApiAuth(api=anon, service_name=service_name)
    ctx = step("AdminApiAuth.check(user.read)", lambda: auth_manager.check(("user.read",), auth.access_token))
    catalog = ApiPermissionCatalog(api, service_name)
    step("ApiPermissionCatalog.list_titles", lambda: catalog.list_titles())
    step(
        "CreateUnexisted(ApiPermissionCatalog)",
        lambda: CreateUnexisted(catalog).apply({"user.read": "Read", "user.update": "Update"}),
    )
    step("FullSync(ApiPermissionCatalog)", lambda: FullSync(catalog).apply({"user.update": "Update", "x.y": "XY"}))
    step("catalog after FullSync", lambda: sorted(catalog.list_titles()))


async def async_part(token: str) -> None:
    async with AsyncApi(BASE, token=token, timeout=30) as aapi:
        results.append(("async users.get_me", "OK", type(await aapi.send(aapi.users.get_me())).__name__))
        page = await aapi.send(aapi.services.filter(service_name=service_name))
        results.append(("async services.filter", "OK", f"total={page.total}"))
        await CreateUnexisted(AsyncApiPermissionCatalog(aapi, service_name)).aapply({"async.perm": "Async"})
        titles = await AsyncApiPermissionCatalog(aapi, service_name).list_titles()
        results.append(
            (
                "async CreateUnexisted(AsyncApiPermissionCatalog)",
                "OK" if "async.perm" in titles else "FAIL",
                str(sorted(titles)),
            ),
        )


try:
    asyncio.run(async_part(auth.access_token))
except Exception as error:  # noqa: BLE001
    results.append(("async part", "FAIL", repr(error)[:200]))

with SyncApi(BASE, token=auth.access_token, timeout=30) as api:
    step("user_service_roles.delete", lambda: api.send(api.user_service_roles.delete(usr_id)))
    step(
        "permissions.delete (FullSync removed it -> 404)",
        lambda: api.send(api.permissions.delete(pid)),
        expect_error=404,
    )
    step("service_roles.delete", lambda: api.send(api.service_roles.delete(rid)))
    step("services.delete", lambda: api.send(api.services.delete(sid)))
    step("users.logout", lambda: api.send(api.users.logout(auth.refresh_token)))


def _delete_other(api: SyncApi):
    other = api.send(
        api.users.sign_up(
            name="Tmp",
            surname="User",
            patronymic="X",
            email=f"tmp-{suffix}@example.test",
            password="Passw0rd!",
        ),
    )
    bound = api.bind(auth.access_token)
    bound.send(bound.users.delete(other.id))
    return bound.send(bound.users.get(other.id))


with SyncApi(BASE, timeout=30) as api:
    step("users.delete then get -> 404", lambda: _delete_other(api), expect_error=404)


print()
width = max(len(r[0]) for r in results)
for name, status, info in results:
    print(f"{status:4} {name:<{width}}  {info}")
failed = sum(r[1] == "FAIL" for r in results)
print(f"\n{len(results) - failed} OK / {failed} FAIL")
sys.exit(1 if failed else 0)
