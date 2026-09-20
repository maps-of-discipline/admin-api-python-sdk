# Расширение SDK

Способы закрыть пробелы в покрытии Admin API и встроить логику сервиса. Внутреннее устройство пакета здесь не описывается.

## Добавление собственных операций

`Operation` описывает метод, URL и разбор ответа. Клиент исполняет её через `send` / `await send`.

```python
from pydantic import TypeAdapter

from admin_api import Operation, SyncApi

list_items = Operation(
    "GET",
    "/api/v1/items/{item_id}",
    adapter=TypeAdapter(dict),
    path_params={"item_id": "42"},
    params={"lang": "ru"},
)

with SyncApi("https://admin.example", token="jwt") as api:
    api.send(list_items)
```

`TypeAdapter` задаёт тип JSON-ответа: модель Pydantic, `dict`, union и другие типы, которые умеет Pydantic.

Запрос без JWT: `auth=False`.

## Добавление собственных ресурсов

Ресурс — класс, методы которого возвращают `Operation`. Его подключают как атрибут сабкласса клиента.

```python
from pydantic import TypeAdapter

from admin_api import Operation, SyncApi
from admin_api.api.users import Users


class ExtraUsers(Users):
    def ping(self) -> Operation[dict[str, bool]]:
        return Operation("GET", "/custom", adapter=TypeAdapter(dict[str, bool]))


class CabinetApi(SyncApi):
    users = ExtraUsers()
```

Для FastAPI наследуйте `AsyncApi` вместо `SyncApi`. Методы ресурса те же: различие только в `send` / `await send`.

## Наследование клиента

Сабкласс сохраняется при `bind()`: интеграция отдаёт клиент того же класса с токеном запроса.

```python
from admin_api.api import SyncApi
from admin_api.integrations.flask import AdminApiFlask, require

root = CabinetApi("https://admin.example", timeout=5.0)
admin = AdminApiFlask(api=root, service_name="cabinet")


@app.get("/ping")
@require("user.read")
def ping(bound: SyncApi):
    return bound.send(bound.users.ping())
```

Flask подставляет клиент в аргумент с аннотацией `SyncApi` (не в аннотацию сабкласса). Фактический тип объекта — `CabinetApi`.

## Парсер токена

Объект с методом `get_token(request) -> str | None`. `None` превращается в `TokenNotProvided`.

Передаётся в `token_parser=` у `AdminApiFlask` / `AdminApiFastAPI`. См. [Flask](flask.md#получение-токена).

## Scoped-валидаторы и middleware

Права с областью действия: `PermissionBase` + `PermissionValidator` (Flask) или async-пары (FastAPI). Регистрация: `add_permission`.

`set_middlewares([...])` задаёт список функций `AuthContext -> dict | None` (async — корутины). Ненулевой словарь попадает в `auth.extras` под именем функции. Middleware выполняется после загрузки пользователя, до проверки permissions, на каждый запрос.

Подробности и примеры: [авторизация](authorization.md#scoped-permissions).

## Кэш

Протокол `AuthCache`: `get`, `get_stale`, `set`, `drop`. Ключ — строка `token_hash(token)` (SHA-256). Значение — `AuthSnapshot` (пользователь и permissions).

Встроенные реализации: `NoCache`, `TtlCache`. Свой кэш (например Redis) передаётся в `cache=` интеграций. Методы протокола синхронные.

## Каталог прав

`CreateUnexisted` и `FullSync` вызывают `RemoteCatalog`: `list_titles`, `create`, `delete`. Реализацию HTTP к Admin API приложение задаёт само. `MemoryCatalog` подходит для тестов.

---

[Содержание](README.md) · [HTTP-клиент](http-client.md) · [API Reference](api-reference.md)
