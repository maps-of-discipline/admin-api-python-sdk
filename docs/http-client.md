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

Ресурсы: `api.users`, `api.mplk`.

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

### Другие ресурсы

`api.mplk` (`admin_api.api.mplk.Mplk`). Ответы типизированы как `Any`.

| Метод | HTTP |
|---|---|
| `get_groups(search=None)` | `GET /api/v1/mplk/groups` |
| `get_students(group, search=None)` | `GET /api/v1/mplk/students` |
| `get_schedule(group, is_session=False)` | `GET /api/v1/mplk/schedule` |
| `get_semester()` | `GET /api/v1/mplk/semester` |
| `get_session()` | `GET /api/v1/mplk/session` |
| `get_user_info()` | `GET /api/v1/mplk/user-info` |
| `get_staff(search=None, division=None, page=1, per_page=50)` | `GET /api/v1/mplk/staff` |
| `generic(data)` | `POST /api/v1/mplk/generic` |

```python
groups = api.send(api.mplk.get_groups(search="ИВТ"))
```

---

[← Назад](README.md) · [Расширение SDK](extending.md) · [Исключения](exceptions.md)
