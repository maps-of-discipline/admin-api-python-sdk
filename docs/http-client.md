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

Ресурсы: `api.users`, `api.mplk`, `api.services`, `api.service_roles`, `api.units`, `api.unit_types`, `api.user_service_roles`, `api.permissions`.

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
| `url` | — | путь; значения `path_params` кодируются как сегменты URL и подставляются в шаблон |
| `adapter` | — | `pydantic.TypeAdapter` для тела ответа |
| `auth` | `True` | требовать токен на клиенте |
| `params` | `None` | query; значения `None` отбрасываются |
| `json` | `None` | JSON-тело |
| `headers` | `None` | дополнительные заголовки |
| `path_params` | `None` | значения сегментов пути; `/` и `?` не меняют структуру URL |

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

### Users

`admin_api.api.users.Users`, доступен как `api.users`. Все методы требуют токен.

| Метод | HTTP | Результат |
|---|---|---|
| `get_me()` | `GET /api/v1/users/me` | `FullUser` |
| `get_by_id(user_id)` | `GET /api/v1/users/{id}` | `FullUser` |
| `get_by_filters(filters, page=1, size=10, sort_by=None, sort_order="DESC")` | `POST /api/v1/users/filters` | `UsersPaginatedResponse` |
| `get_permissions(service_name)` | `GET /api/v1/users/permissions` | `UserPermissions` |

```python
user = api.send(api.users.get_me())
permissions = api.send(api.users.get_permissions("cabinet"))
user_by_id = api.send(api.users.get_by_id(user.id))
```

`FullUser` — `FullNaturalUser | FullOrganizationalUser` (поле `kind`).
`UserPermissions` — `dict[str, list[Scope]]`.
`Scope` — `UnitScopeResponse` (`type="unit"`, `unit_id`) или `UnitTypeScopeResponse` (`type="unit_type"`, `unit_type_id`).

Модели пользователя и permissions определены вручную в `admin_api.api.users.schemas`.
Для поиска передайте `UserGetByFiltersRequest`, например `UserGetByFiltersRequest(email="user@example.com")`.
Сейчас сервер применяет только фильтр `email`; остальные поля запроса и параметры сортировки принимаются, но не участвуют в поиске и сортировке.

### Services

`api.services` (`admin_api.api.services.Services`). Все операции требуют токен.

| Метод | HTTP | Результат |
|---|---|---|
| `get_by_filters(filters=None, page=1, size=10, sort_by=None, sort_order="DESC")` | `POST /api/v1/services/filters` | `ServicesPaginatedResponse` |
| `get_by_id(service_id)` | `GET /api/v1/services/{id}` | `ServiceResponse` |
| `create(service)` | `POST /api/v1/services` | `ServiceResponse` |
| `update(service)` | `PATCH /api/v1/services` | `ServiceResponse` |
| `update_icon(service)` | `PATCH /api/v1/services/branding/icon` | `ServiceResponse` |
| `update_color(service)` | `PATCH /api/v1/services/branding/color` | `ServiceResponse` |
| `delete(service_id)` | `DELETE /api/v1/services/{id}` | `"success"` |

```python
from admin_api.api.services import ServiceCreate, ServiceGetByFiltersRequest

services = api.send(api.services.get_by_filters(ServiceGetByFiltersRequest(service_name="cab")))
created = api.send(api.services.create(ServiceCreate(name="cabinet")))
```

Схемы запроса проверяют и нормализуют иконку и цвет так же, как Admin API. Для очистки `verbose_name` при обновлении передайте `None`.

### Service roles

`api.service_roles` использует путь `/api/v1/service-roles` и схемы из `admin_api.api.service_roles`.

| Метод | HTTP | Результат |
|---|---|---|
| `get_by_filters(filters=None, page=1, size=10, sort_by=None, sort_order="DESC")` | `POST /filters` | `ServiceRolesPaginatedResponse` |
| `get_by_id(service_role_id)` | `GET /{id}` | `ServiceRolesResponse` |
| `create(role)` | `POST /` | `ServiceRolesResponse` |
| `update(role)` | `PATCH /` | `None` |
| `delete(service_role_id)` | `DELETE /{id}` | `"success"` |
| `get_permissions(service_role_id)` | `GET /{id}/permissions` | `ServiceRolesPermissionsResponse` |
| `assign_permission(assignment)` | `POST /assign-permission` | `"success"` |
| `revoke_permission(assignment)` | `POST /revoke-permission` | `"success"` |

`ServiceRolesCreate` и `ServiceRolesUpdate` допускают `service_id=None` по схеме Admin API, но серверу для этих операций нужен существующий сервис. `update` возвращает JSON `null`.

### Units и unit types

`api.units.get_all(flat=False, max_depth=None, root_id=None, search=None, type_ids=None)` вызывает `GET /api/v1/units` и возвращает список `UnitTreeResponse` или `UnitResponse`. Поиск и `type_ids` доступны только при `flat=True`. `api.unit_types.get_all()` вызывает `GET /api/v1/unit-types` и возвращает `list[UnitType]`. Схемы доступны в `admin_api.api.units` и `admin_api.api.unit_types`.

### User service roles

`api.user_service_roles` использует путь `/api/v1/user_service_roles`.

| Метод | HTTP | Результат |
|---|---|---|
| `get_by_id(assignment_id)` | `GET /{id}` | `UserServiceRolesResponse` |
| `create(assignment)` | `POST /` | `UserServiceRolesResponse` |
| `update(assignment)` | `PATCH /` | `UserServiceRolesResponse` |
| `delete(assignment_id)` | `DELETE /{id}` | `"success"` |

В `UserServiceRolesCreate` и `UserServiceRolesUpdate` передавайте scope через `UnitScopeItem` или `UnitTypeScopeItem`. В ответе элементы scope имеют собственный `id`. При `update` значение `scope=None` сохраняет существующий scope, а пустой список очищает его. При создании серверу нужны `user_id` и `service_roles_id`, хотя исходная схема допускает `None`.

### Permissions

`api.permissions` использует путь `/api/v1/permission` в единственном числе и схемы из `admin_api.api.permissions`.

| Метод | HTTP | Результат |
|---|---|---|
| `get_by_filters(filters=None, page=1, size=10, sort_by=None, sort_order="DESC")` | `POST /filters` | `PermissionPaginatedResponse` |
| `get_by_id(permission_id)` | `GET /{id}` | `PermissionResponse` |
| `create(permission)` | `POST /` | `PermissionResponse` |
| `update(permission)` | `PATCH /` | `PermissionResponse` |
| `delete(permission_id)` | `DELETE /{id}` | `"success"` |

### MPLK

`api.mplk` (`admin_api.api.mplk.Mplk`). Методы чтения возвращают модели с полями ответа Admin API.
Вложенные данные приходят из внешнего МПЛК и сохраняют исходную структуру.

| Метод | HTTP | Результат |
|---|---|---|
| `get_groups(search=None)` | `GET /api/v1/mplk/groups` | `MPLKGetGroupsResponse` |
| `get_students(group, search=None)` | `GET /api/v1/mplk/students` | `MPLKGetStudentsResponse` |
| `get_schedule(group, is_session=False)` | `GET /api/v1/mplk/schedule` | `MPLKGetScheduleResponse` |
| `get_semester()` | `GET /api/v1/mplk/semester` | `MPLKGetSemesterResponse` |
| `get_session()` | `GET /api/v1/mplk/session` | `MPLKGetSessionResponse` |
| `get_user_info()` | `GET /api/v1/mplk/user-info` | `MPLKGetUserInfoResponse` |
| `get_staff(search=None, division=None, page=1, per_page=50)` | `GET /api/v1/mplk/staff` | `MPLKGetStaffResponse` |
| `generic(data)` | `POST /api/v1/mplk/generic` | произвольный JSON-ответ МПЛК |

```python
groups = api.send(api.mplk.get_groups(search="ИВТ"))
print(groups.groups)
```

Для `generic` передавайте тело в формате `{"body": {"method": "GET", "url": "..."}}`.

---

[← Назад](README.md) · [Расширение SDK](extending.md) · [Исключения](exceptions.md)
