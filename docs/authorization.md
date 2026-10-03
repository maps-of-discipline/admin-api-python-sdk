# Авторизация и permissions

[← Назад](README.md)

SDK отделяет **аутентификацию** (кто отправил запрос) от **авторизации** (разрешено ли действие).

## Последовательность

```text
HTTP request
  → JWT из заголовка Authorization (Bearer)
  → GET /api/v1/users/me
  → GET /api/v1/users/permissions?service_name=<service_name>
  → AuthContext (пользователь и permissions)
  → проверка permission и опциональных scoped-валидаторов
  → обработчик
```

Интеграции Flask и FastAPI выполняют эти шаги при обращении к защищённому endpoint. Без фреймворка тот же пайплайн доступен через `AdminApiAuth` / `AsyncAdminApiAuth`.

## Авторизация

Токен по умолчанию читается из заголовка `Authorization` в виде `Bearer <jwt>`. Парсер можно заменить; см. [Flask](flask.md#получение-токена) и [FastAPI](fastapi.md#получение-токена).

После успешной загрузки доступны:

- пользователь Admin API;
- словарь permissions этого пользователя для `service_name`;
- HTTP-клиент с токеном текущего запроса.

Локального пользователя вашей базы данных SDK не создаёт.

## Получение пользователя

Пользователь приходит из `GET /api/v1/users/me` и доступен как `AuthContext.user`.

Тип — union `FullNaturalUser | FullOrganizationalUser` (дискриминатор JSON-поля `kind`). Идентификатор: `auth.user.id`.

В обработчике Flask:

```python
@require("user.read")
def me(auth: AuthContext):
    return {"id": str(auth.user.id)}
```

В FastAPI:

```python
async def me(auth: AuthContext = Depends(require("user.read"))):
    return {"id": str(auth.user.id)}
```

Повторный запрос `get_me` из обработчика не обязателен: снимок уже лежит в контексте.

## Получение разрешений

Permissions запрашиваются для `service_name` интеграции: `GET /api/v1/users/permissions?service_name=...`.

Тип: `dict[str, list[Scope]]`.

- ключ — строка права, например `user.read`;
- значение — список областей действия; пустой список означает, что право есть без ограничения scope.

```python
auth.has("user.read")  # ключ есть в permissions
auth.scopes("program.manage")  # list[Scope], иначе []
```

`Scope` — union:

- `type="unit"` — поле `unit_id`;
- `type="unit_type"` — поле `unit_type_id`.

## Проверка разрешений

`require("user.read")` (Flask-декоратор или FastAPI-dependency):

1. Загружает пользователя и permissions, если это ещё не сделано для запроса.
2. Для каждого отдельного аргумента проверяет право или группу прав: право должно быть в `permissions` и, если для него зарегистрирован валидатор, пройти его проверку.
3. Все отдельные аргументы обязательны (**И**). Внутри коллекции достаточно одного прошедшего права (**ИЛИ**).
4. При успехе отдаёт `AuthContext` в обработчик.

```python
require("user.read")
require("user.read", "user.update")  # оба права обязательны
require(("user.read", "user.update"))  # достаточно любого из двух
require(["user.read", "user.update"])  # список: ИЛИ
require({"user.read", "user.update"})  # множество: ИЛИ
require("user.read", ("user.update", "user.delete"))  # user.read И (user.update ИЛИ user.delete)
require(None)  # только аутентификация
```

Аргументы принимают `str | Collection[str] | None`. Пустой `require()` также проверяет только наличие токена и успешную загрузку контекста. Пустая коллекция не содержит ни одного подходящего права и приводит к 403.

Незарегистрированное право проверяется только по наличию ключа в ответе Admin API.

## Scoped permissions

Валидатор добавляет проверку области действия поверх факта наличия права: например, permission действует только на подразделение из path.

Flask и sync-менеджер используют `PermissionValidator` и `PermissionBase`. FastAPI и async-менеджер — `AsyncPermissionValidator` и `AsyncPermissionBase`. Смешивать линейки нельзя.

`title` класса должен совпадать со строкой в `require(...)` и с ключом в Admin API. Атрибут `validator` обязателен.

```python
from admin_api.auth import AsyncPermissionBase, AsyncPermissionValidator, AuthContext


class ProgramInUnit(AsyncPermissionValidator):
    async def validate(self, auth: AuthContext, request: object | None = None) -> bool:
        program_id = getattr(request, "path_params", {}).get("program_id")
        return any(scope.type == "unit" and str(scope.unit_id) == program_id for scope in auth.scopes("program.manage"))


class ProgramManage(AsyncPermissionBase):
    title = "program.manage"
    verbose_name = "Управление программой"
    validator = ProgramInUnit
```

Регистрация до обработки запросов:

```python
admin.add_permission(ProgramManage)
```

Валидатор получает `AuthContext` и исходный объект request фреймворка (Flask `Request` или Starlette `Request`). Сессию БД SDK не передаёт.

Если валидатор вернул `False`, возникает `PermissionDenied` (в интеграциях — HTTP 403).

## Кэш

По умолчанию каждый запрос ходит в Admin API (`NoCache`).

`TtlCache` хранит пользователя и permissions на время TTL. Middleware и scoped-валидаторы выполняются на каждый запрос. Каждый запрос получает отдельную копию пользователя и permissions, поэтому их изменение не затрагивает кэш.

```python
from admin_api.auth import TtlCache

admin = AdminApiFlask(
    api=api,
    service_name="cabinet",
    cache=TtlCache(ttl_seconds=30),
)
```

Ключ кэша строится по хешу токена, не по сырому JWT. Просроченный снимок доступен ещё 300 секунд по умолчанию (`stale_ttl_seconds`) и затем удаляется при обращении. Размер кэша ограничен `maxsize`: при заполнении вытесняется запись, к которой дольше всего не обращались. Свой кэш реализуется протоколом `AuthCache`; см. [расширение SDK](extending.md#кэш).

## Недоступность Admin API

| `FailPolicy` | Поведение при ошибке загрузки |
|---|---|
| `DENY` (по умолчанию) | исключение распространяется дальше |
| `USE_STALE` | при ошибке HTTP-клиента или ответе 5xx используется предыдущий снимок в пределах `stale_ttl_seconds` |

Ответ **401** от Admin API всегда означает невалидный токен: снимок из кэша удаляется, возвращается `InvalidTokenException`. Другие ответы 4xx не включают резервное использование кэша.

Интеграции не преобразуют `ApiError` в HTTP-ответ. Без собственного обработчика это ошибка сервера (HTTP 500).

## Каталог прав

При старте приложения стратегия каталога может зарегистрировать локальные `title` из `add_permission` во внешнем каталоге Admin API.

| Стратегия | Поведение |
|---|---|
| `DoNothing` | по умолчанию, ничего не делает |
| `CreateUnexisted` | создаёт отсутствующие title |
| `FullSync` | создаёт отсутствующие и удаляет лишние |

`CreateUnexisted` и `FullSync` принимают объект с методами `list_titles()`, `create()`, `delete()` (`RemoteCatalog`). HTTP-ресурса каталога в клиенте нет: реализацию протокола задаёт приложение. `MemoryCatalog` — in-memory вариант для тестов.

Flask вызывает синхронизацию в `init_app`. FastAPI — при старте приложения.

Пока права не заведены в Admin API, `require("...")` завершится 403.

## Без фреймворка

```python
from admin_api import AdminApiAuth, SyncApi

api = SyncApi("https://admin.example", timeout=5.0)
auth = AdminApiAuth(api=api, service_name="cabinet")

ctx, bound = auth.load("user-jwt")
auth.assert_permissions(ctx, ("user.read",))
```

`check(required, token)` и `assert_permissions(context, required)` также принимают строку, коллекцию строк или `None`. Коллекция в этих методах проверяется по ИЛИ. При `None` проверка прав пропускается; `check` всё равно загружает контекст по токену.

Асинхронный вариант: `AsyncApi` и `AsyncAdminApiAuth`, методы `load` / `check` / `assert_permissions` — корутины.

## Обработка ошибок

| Ситуация | Исключение | Flask / FastAPI |
|---|---|---|
| Токен отсутствует | `TokenNotProvided` | 401 |
| Admin API ответил 401 | `InvalidTokenException` | 401 |
| Нет права или валидатор отклонил запрос | `PermissionDenied` | 403 |
| Другая ошибка Admin API | `ApiError` | не обрабатывается |

Подробнее: [исключения](exceptions.md).

---

[← Назад](README.md) · [Flask](flask.md) · [FastAPI](fastapi.md) · [Конфигурация](configuration.md)
