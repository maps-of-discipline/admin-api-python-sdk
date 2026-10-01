# FastAPI

[← Назад](README.md)

Интеграция: `admin_api.integrations.fastapi`. Требуется extra `fastapi`.

Используется асинхронный клиент `AsyncApi`.

Обработчики импортируют зависимости из пакета (`require`, `get_api`, `get_request_auth`). Экземпляр интеграции в модулях маршрутов импортировать не нужно: он читается из приложения после `init_app`.

## Инициализация

```python
from fastapi import FastAPI

from admin_api.api import AsyncApi
from admin_api.integrations.fastapi import AdminApiFastAPI

api = AsyncApi("https://admin.example", timeout=5.0)
admin = AdminApiFastAPI(api=api, service_name="cabinet")

app = FastAPI()
admin.init_app(app)
```

`init_app`:

- сохраняет интеграцию в состоянии приложения;
- регистрирует обработчики исключений;
- при старте приложения синхронизирует каталог прав.

Обработчики: `init_app(app, exception_handlers=False)`. Их можно повесить отдельно через `install_exception_handlers(app)`.

Без `init_app` зависимости поднимают `RuntimeError`.

`AdminApiFastAPI` наследует `AsyncAdminApiAuth`.

Параметры конструктора — в [конфигурации](configuration.md).

## Получение токена

По умолчанию `BearerTokenParser`: заголовок `Authorization`, схема `Bearer`.

Нет токена — `TokenNotProvided` (HTTP 401).

Свой парсер реализует `get_token(request) -> str | None`. `request` — Starlette/FastAPI `Request`.

```python
class CookieTokenParser:
    def get_token(self, request) -> str | None:
        return request.cookies.get("access_token")

admin = AdminApiFastAPI(
    api=api,
    service_name="cabinet",
    token_parser=CookieTokenParser(),
)
```

## Защита endpoint

```python
from fastapi import Depends, FastAPI

from admin_api.auth import AuthContext
from admin_api.integrations.fastapi import require


@app.get("/me")
async def me(auth: AuthContext = Depends(require("user.read"))):
    return {"id": str(auth.user.id)}
```

`require(*args)` возвращает async-callable. Каждый аргумент — строка, коллекция строк или `None`. Отдельные аргументы соединяются по И, элементы одной коллекции — по ИЛИ. Например, `require("user.read", {"user.update", "user.delete"})`. Функцию передают в `Depends`, а не вызывают как декоратор.

Пустой `require()` требует только валидный токен и успешную загрузку контекста.

Scoped-валидаторы: `AsyncPermissionBase` / `AsyncPermissionValidator` и `admin.add_permission(...)`. См. [авторизация](authorization.md#scoped-permissions).

## Dependency / injection

Публичные зависимости:

| Callable | Тип результата |
|---|---|
| `get_request_auth` | `RequestAuth` |
| `require("...")` | `AuthContext` |
| `get_api` | `AsyncApi` |

На одном запросе identity загружается один раз. Несколько `Depends` на одном обработчике переиспользуют один и тот же контекст и клиент.

```python
from typing import Annotated

from fastapi import Depends

from admin_api.api import AsyncApi
from admin_api.auth import AuthContext
from admin_api.integrations.fastapi import RequestAuth, get_api, get_request_auth, require

RequireUserRead = Annotated[AuthContext, Depends(require("user.read"))]


@app.get("/me")
async def me(
    auth: RequireUserRead,
    bound: AsyncApi = Depends(get_api),
    bundle: RequestAuth = Depends(get_request_auth),
):
    return {
        "id": str(auth.user.id),
        "same": str(bundle.context.user.id),
    }
```

`require()` не оборачивается в `Depends` внутри SDK. Её можно сочетать с другими FastAPI-зависимостями в том же обработчике.

Отдельной OpenAPI-схемы для permissions SDK не добавляет: FastAPI показывает `require` как обычную dependency.

## Доступ к пользователю и контексту авторизации

`AuthContext` после успешного `require` / `get_request_auth`:

- `auth.user` — пользователь Admin API;
- `auth.permissions` / `auth.has(...)` / `auth.scopes(...)`;
- `auth.extras` — результаты middleware.

`RequestAuth.api` и `get_api` — `AsyncApi` с токеном текущего запроса.

Локальный пользователь БД приложения:

```python
async def get_local_user(bundle: RequestAuth = Depends(get_request_auth)):
    ...
```

## Обработка ошибок

Ответ: JSON `{"detail": "<сообщение исключения>"}`.

| Исключение | HTTP |
|---|---|
| `TokenNotProvided` | 401 |
| `InvalidTokenException` | 401 |
| `PermissionDenied` | 403 |

`ApiError` не перехватывается.

---

[← Назад](README.md) · [Быстрый старт](quickstart.md) · [Авторизация](authorization.md) · [Flask](flask.md)
