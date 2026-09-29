# HTTP-клиент

[← Назад](README.md)

Низкоуровневый API Admin API без проверки прав. Интеграции Flask и FastAPI используют его внутри; напрямую он нужен для вызовов вне обработчика, кастомных эндпоинтов и расширения клиента.

## SyncApi

Синхронный клиент на `httpx.Client`. Для Flask и скриптов.

```python
from admin_api import SyncApi

with SyncApi("https://admin.example", token="jwt", timeout=5.0) as api:
    user = api.send(api.users.get_me())
```

| Параметр | Тип | По умолчанию | Назначение |
|---|---|---|---|
| `base_url` | `str` | — | базовый URL Admin API |
| `token` | `str \| None` | `None` | JWT для запросов с `auth=True` |
| `timeout` | `float` | `5.0` | таймаут HTTP в секундах |
| `transport` | транспорт httpx или `None` | `None` | подмена транспорта (тесты, свой HTTP) |

Ресурсы: `api.users`, `api.services`, `api.service_roles`, `api.permissions`, `api.user_service_roles`, `api.orders`, `api.messengers`, `api.units`, `api.assignment_rules`, `api.mplk`. Полный список методов — в разделе [Ресурсы Admin API](#ресурсы-admin-api).

Методы: `send(operation)`, `bind(token)`, `close()`. Поддерживается context manager (`with`).

## AsyncApi

Асинхронный клиент на `httpx.AsyncClient`. Для FastAPI.

```python
from admin_api import AsyncApi

async with AsyncApi("https://admin.example", token="jwt", timeout=5.0) as api:
    user = await api.send(api.users.get_me())
```

Сигнатура конструктора совпадает с `SyncApi`. Методы: `await send(operation)`, `bind(token)`, `await aclose()`. Поддерживается `async with`.

Набор ресурсов тот же. Описание запроса (`Users.get_me()` и другие) общее; различается только способ отправки.

## Operation

Дескриптор HTTP-запроса и способа разобрать JSON-ответ. Сеть не выполняет. Обычному приложению на Flask/FastAPI создавать `Operation` не требуется.

```python
from pydantic import TypeAdapter

from admin_api import Operation, SyncApi

op = Operation(
    "GET",
    "/api/v1/users/me",
    adapter=TypeAdapter(dict),
    auth=True,
)
with SyncApi("https://admin.example", token="jwt") as api:
    payload = api.send(op)
```

| Параметр | По умолчанию | Назначение |
|---|---|---|
| `method` | — | HTTP-метод |
| `url` | — | путь; подставляется `path_params` через `str.format` |
| `adapter` | — | `pydantic.TypeAdapter` для тела ответа |
| `auth` | `True` | требовать токен на клиенте |
| `params` | `None` | query; значения `None` отбрасываются |
| `json` | `None` | JSON-тело |
| `headers` | `None` | дополнительные заголовки |
| `path_params` | `None` | подстановка в URL |

`adapter` нужен и для моделей Pydantic, и для union/словарей (`FullUser`, `UserPermissions`).

При `auth=True` и отсутствии токена на клиенте `send` поднимает `TokenNotProvided`.

## bind()

Создаёт новый экземпляр того же класса с другим токеном. Исходный клиент не меняется. HTTP-соединение переиспользуется.

Нужен, когда корневой клиент живёт всё время работы приложения, а токен — у входящего запроса.

```python
root = SyncApi("https://admin.example", timeout=5.0)
alice = root.bind("alice-jwt")
user = alice.send(alice.users.get_me())
```

Сабкласс сохраняется: `CabinetApi.bind(...)` возвращает `CabinetApi`.

Закрывать нужно корневой клиент, созданный приложением. Копия после `bind` соединение не закрывает.

Интеграции вызывают `bind` сами и отдают bound-клиент в обработчик.

## Кастомные запросы

Эндпоинт, которого нет в SDK:

```python
from pydantic import TypeAdapter

from admin_api import Operation, SyncApi

ping = Operation("GET", "/custom", adapter=TypeAdapter(dict[str, bool]))

with SyncApi("https://admin.example", token="jwt") as api:
    result = api.send(ping)
```

Для FastAPI — `await api.send(ping)` на `AsyncApi`.

## Ошибки HTTP

| Ответ Admin API | Исключение |
|---|---|
| 401 | `InvalidTokenException` |
| другой неуспешный статус | `ApiError` |

У `ApiError` есть `status_code`, `error_code`, `detail`, `errors`. Сообщение исключения берётся из JSON-поля `detail`, если это строка.

## Ресурсы Admin API

Методы ресурсов только строят `Operation`; отправка — `api.send(...)` / `await api.send(...)`. Идентификаторы принимаются как `UUID` или строка. Токен нужен всем методам, кроме помеченных «без токена». Модели ответов — из `admin_api.api.dto` (генерируются из OpenAPI), если не указано иное.

Тело запроса собирается через соответствующую DTO, поэтому неверные значения (например, неизвестная роль) отклоняются до отправки (`pydantic.ValidationError`). Поля со значением `None` в тело не попадают — сервер подставляет свои значения по умолчанию.

### Пагинация

Методы `filter(...)` возвращают `Page[T]` (`admin_api.api.Page`): `data`, `page`, `size`, `total`. Общие параметры: `page=1`, `size=10` (сервер допускает 1–100), `sort_by=None`, `sort_order=SortOrder.DESC`.

```python
page = api.send(api.services.filter(service_name="cab", size=50))
for service in page.data:
    print(service.name)
```

Фильтр `service_name` на сервере подстрочный (`LIKE %value%`).

### Users — `api.users`

| Метод | HTTP | Результат |
|---|---|---|
| `get_me()` | `GET /api/v1/users/me` | `FullUser` |
| `get_permissions(service_name)` | `GET /api/v1/users/permissions` | `UserPermissions` |
| `get(id)` | `GET /api/v1/users/{id}` | `FullUser` |
| `delete(id)` | `DELETE /api/v1/users/{id}` | `str` |
| `filter(email=, service_name=, service_role=, role=, can_manage_services=, page=, size=, sort_by=, sort_order=)` | `POST /api/v1/users/filters` | `Page[UserEntity]` |
| `get_roles_from_service(id, service_name)` | `POST /api/v1/users/{id}/get_roles_from_service` | `UserGetRolesFromServiceResp` |
| `get_accounts()` | `GET /api/v1/users/accounts` | `UserAccountsResponse` |
| `activate_account(account_id)` | `PATCH /api/v1/users/accounts/{account_id}/activate` | `Account` |
| `get_managed_services()` | `POST /api/v1/users/managed-services` | `ManagedServices` |
| `assign_service(user_id, service_id)` | `POST /api/v1/users/assign-service` | `None` |
| `revoke_service(user_id, service_id)` | `POST /api/v1/users/revoke-service` | `None` |
| `link_mplk(login, password)` | `POST /api/v1/users/link-mplk` | `UserAuthData` |
| `logout(refresh_token)` | `POST /api/v1/users/logout` | `str` |
| `login(credentials)` — без токена | `POST /api/v1/users/login` | `AuthChallengeResponse` |
| `login_by_password(email, password)` — без токена | то же, `type="password"` | `AuthChallengeResponse` |
| `login_by_email(email)` — без токена | то же, `type="email"` | `AuthChallengeResponse` |
| `login_by_mplk(login, password)` — без токена | то же, `type="mplk"` | `AuthChallengeResponse` |
| `verify_auth_code(pre_auth_token, code=None)` — без токена | `POST /api/v1/users/verification_auth_code` | `UserAuthData` |
| `refresh(auth_data)` — без токена | `POST /api/v1/users/refresh` | `UserAuthData` |
| `sign_up(name=, surname=, patronymic=, email=, password=)` — без токена | `POST /api/v1/users/sign-up` | `UserCreateResponse` |

Схемы из `admin_api.api.users`:

- `FullUser` — `FullNaturalUser | FullOrganizationalUser` (поле `kind`);
- `UserEntity` — `NaturalUser | OrganizationalUser`: элемент списка пользователей, без аккаунтов и подразделений;
- `UserPermissions` — `dict[str, list[Scope]]`; `Scope` — `UnitScopeResponse` (`type="unit"`) или `UnitTypeScopeResponse` (`type="unit_type"`);
- `Account` — `StaffAccount | StudentAccount` (поле `account_type`);
- `ManagedServices` — `services: list[ManagedService]`;
- `LoginCredentials` — `EmailLogin | PasswordLogin | MplkLogin` (поле `type`).

Вход с подтверждением кодом:

```python
with SyncApi("https://admin.example") as api:
    challenge = api.send(api.users.login_by_password("user@example.com", "secret"))
    code = input("Код из письма: ") if challenge.mfa_required else None
    auth = api.send(api.users.verify_auth_code(challenge.pre_auth_token, code))
    me = api.bind(auth.access_token).send(api.users.get_me())
```

### Services — `api.services`

| Метод | HTTP | Результат |
|---|---|---|
| `get(id)` | `GET /api/v1/services/{id}` | `ServiceResponse` |
| `filter(service_name=, page=, size=, sort_by=, sort_order=)` | `POST /api/v1/services/filters` | `Page[ServiceResponse]` |
| `create(name=, verbose_name=, icon=, color=)` | `POST /api/v1/services` | `ServiceResponse` |
| `update(id, name=, verbose_name=)` | `PATCH /api/v1/services` | `ServiceResponse` |
| `update_icon(id, icon)` | `PATCH /api/v1/services/branding/icon` | `ServiceResponse` |
| `update_color(id, color)` | `PATCH /api/v1/services/branding/color` | `ServiceResponse` |
| `delete(id)` | `DELETE /api/v1/services/{id}` | `str` |

### Service roles — `api.service_roles`

| Метод | HTTP | Результат |
|---|---|---|
| `get(id)` | `GET /api/v1/service-roles/{id}` | `ServiceRolesResponse` |
| `filter(service_name=, page=, size=, sort_by=, sort_order=)` | `POST /api/v1/service-roles/filters` | `Page[ServiceRolesResponse]` |
| `create(role=, service_id=, verbose_name=)` | `POST /api/v1/service-roles` | `ServiceRolesResponse` |
| `update(id, role=, service_id=, verbose_name=)` | `PATCH /api/v1/service-roles` | `ServiceRolesResponse \| None` ¹ |
| `delete(id)` | `DELETE /api/v1/service-roles/{id}` | `str` |
| `get_permissions(id)` | `GET /api/v1/service-roles/{id}/permissions` | `ServiceRolesPermissionsResponse` |
| `assign_permission(service_role_id, permission_id)` | `POST /api/v1/service-roles/assign-permission` | `str` |
| `revoke_permission(service_role_id, permission_id)` | `POST /api/v1/service-roles/revoke-permission` | `str` |

¹ Сейчас Admin API отвечает на этот `PATCH` пустым телом (`null`), хотя в OpenAPI заявлена модель; SDK вернёт `None`, а после исправления сервера — модель.

`role` — `Role` или строка: `student`, `staff`, `admin`, `super_admin`, `faculty_admin`, `department_admin`.

### Permissions — `api.permissions`

| Метод | HTTP | Результат |
|---|---|---|
| `get(id)` | `GET /api/v1/permission/{id}` | `PermissionResponse` |
| `filter(service_name=, page=, size=, sort_by=, sort_order=)` | `POST /api/v1/permission/filters` | `Page[PermissionResponse]` |
| `create(service_id=, title=, verbose_name=)` | `POST /api/v1/permission` | `PermissionResponse` |
| `update(id, service_id=, title=, verbose_name=)` | `PATCH /api/v1/permission` | `PermissionResponse` |
| `delete(id)` | `DELETE /api/v1/permission/{id}` | `str` |

### User service roles — `api.user_service_roles`

Назначение роли сервиса пользователю с областью действия (`scope`).

| Метод | HTTP | Результат |
|---|---|---|
| `get(id)` | `GET /api/v1/user_service_roles/{id}` | `UserServiceRolesResponse` |
| `create(user_id=, service_roles_id=, scope=None)` | `POST /api/v1/user_service_roles` | `UserServiceRolesResponse` |
| `update(id, user_id=, service_roles_id=, scope=None)` | `PATCH /api/v1/user_service_roles` | `UserServiceRolesResponse` |
| `delete(id)` | `DELETE /api/v1/user_service_roles/{id}` | `str` |

`scope` — список `UnitScopeItem` / `UnitTypeScopeItem` или словарей `{"type": "unit", "unit_id": ...}` / `{"type": "unit_type", "unit_type_id": ...}`.

### Orders — `api.orders`

| Метод | HTTP | Результат |
|---|---|---|
| `get(id)` | `GET /api/v1/orders/{id}` | `OrderResponse` |
| `list(limit=50, offset=0, service_id=None)` | `POST /api/v1/orders/list` | `list[OrderResponse]` |
| `create(target_role=, comment=, user_id=, service_id=)` | `POST /api/v1/orders` | `OrderResponse` |
| `update(id, target_role=, comment=, user_id=, service_id=)` | `PATCH /api/v1/orders` | `OrderResponse \| None` ¹ |
| `approve(id, approve=True)` | `POST /api/v1/orders/approve` | `None` |
| `delete(id)` | `DELETE /api/v1/orders/{id}` | `str` |

`approve` удаляет заявку в любом случае; при `approve=True` пользователю выдаётся роль `target_role` сервиса. ¹ — см. примечание к `service_roles.update`.

### Messengers — `api.messengers`

| Метод | HTTP | Результат |
|---|---|---|
| `list()` | `GET /api/v1/messengers` | `list[MessengerResponse]` |
| `link(messenger_type, id_token)` | `POST /api/v1/messengers/link` | `MessengerResponse` |
| `unlink(messenger_type)` | `DELETE /api/v1/messengers/{messenger_type}` | `MessengerUnlinkResponse` |
| `get_user(messenger_type, messenger_user_id)` | `GET /api/v1/messengers/user/{messenger_type}/{messenger_user_id}` | `User` |

`get_user` авторизуется токеном бота (`MESSENGER_BOT_TOKEN` Admin API), а не JWT пользователя: `SyncApi(..., token=bot_token)`.

### Units — `api.units`

| Метод | HTTP | Результат |
|---|---|---|
| `list(root_id=, search=, type_ids=, max_depth=)` | `GET /api/v1/units?flat=false` | `list[UnitTree]` |
| `list_flat(root_id=, search=, type_ids=, max_depth=)` | `GET /api/v1/units?flat=true` | `list[Unit]` |
| `get_types()` | `GET /api/v1/unit-types` | `list[UnitType]` |

`Unit` и `UnitTree` — из `admin_api.api.units`. `search` на сервере не короче 2 символов.

### Assignment rules — `api.assignment_rules`

Правила автоматической выдачи ролей.

| Метод | HTTP | Результат |
|---|---|---|
| `get(id)` | `GET /api/v1/assignment-rules/{id}` | `AssignmentRuleResponse` |
| `list(limit=50, offset=0, service_role_id=None)` | `GET /api/v1/assignment-rules` | `list[AssignmentRuleResponse]` |
| `get_metadata()` — без токена | `GET /api/v1/assignment-rules/metadata` | `dict[str, Any]` |
| `create(title=, service_role_id=, expression=, enabled=True, scope_template="unscoped")` | `POST /api/v1/assignment-rules` | `AssignmentRuleResponse` |
| `update(id, title=, service_role_id=, expression=, enabled=, scope_template=)` | `PATCH /api/v1/assignment-rules/{id}` | `AssignmentRuleResponse` |
| `delete(id)` | `DELETE /api/v1/assignment-rules/{id}` | `None` |

`expression` — модель выражения из `admin_api.api.dto` или словарь:

```python
rule = api.send(
    api.assignment_rules.create(
        title="Студенты 221-321",
        service_role_id=role.id,
        expression={
            "kind": "predicate",
            "field": "group",
            "predicate": {"operator": "equal", "value": "221-321"},
        },
    ),
)
```

Доступные поля выражений возвращает `get_metadata()`.

### MPLK — `api.mplk`

Ответы типизированы как `Any` (прокси к API личного кабинета).

| Метод | HTTP |
|---|---|
| `get_groups(search=None)` | `GET /api/v1/mplk/groups` |
| `get_students(group, search=None)` | `GET /api/v1/mplk/students` |
| `get_schedule(group, is_session=False)` | `GET /api/v1/mplk/schedule` |
| `get_semester()` | `GET /api/v1/mplk/semester` |
| `get_session()` | `GET /api/v1/mplk/session` |
| `get_user_info()` | `GET /api/v1/mplk/user-info` |
| `get_staff(search=None, division=None, page=1, per_page=50)` | `GET /api/v1/mplk/staff` |
| `generic(url, method="GET", headers=None, query=None, body=None)` | `POST /api/v1/mplk/generic` |

```python
groups = api.send(api.mplk.get_groups(search="ИВТ"))
data = api.send(api.mplk.generic("/api/some/endpoint", query={"page": 1}))
```

`generic` сам оборачивает параметры в `{"body": {...}}`, как ожидает Admin API.

---

[← Назад](README.md) · [Расширение SDK](extending.md) · [Исключения](exceptions.md)
