# Flask

[← Назад](README.md)

Интеграция: `admin_api.integrations.flask`. Требуется extra `flask`.

Используется синхронный клиент `SyncApi`.

## Инициализация

```python
from flask import Flask

from admin_api.api import SyncApi
from admin_api.integrations.flask import AdminApiFlask

api = SyncApi("https://admin.example", timeout=5.0)
admin = AdminApiFlask(api=api, service_name="cabinet")

app = Flask(__name__)
admin.init_app(app)
```

`init_app`:

- регистрирует интеграцию в приложении;
- синхронизирует каталог прав;
- устанавливает обработчики `TokenNotProvided`, `InvalidTokenException`, `PermissionDenied`.

Обработчики можно отключить: `init_app(app, exception_handlers=False)`.

Параметры конструктора — в [конфигурации](configuration.md).

`AdminApiFlask` наследует `AdminApiAuth`: доступны `add_permission`, `set_middlewares`, `load`, `check` и остальные методы менеджера.

## Получение токена

По умолчанию `BearerTokenParser`: заголовок `Authorization`, схема `Bearer`.

Отсутствие заголовка, пустое значение или схема, отличная от заданной, приводят к `TokenNotProvided` (HTTP 401).

Свой парсер — объект с методом `get_token(request) -> str | None`:

```python
class CookieTokenParser:
    def get_token(self, request) -> str | None:
        return request.cookies.get("access_token")

admin = AdminApiFlask(
    api=api,
    service_name="cabinet",
    token_parser=CookieTokenParser(),
)
```

`request` — Flask `Request`.

## Защита endpoint

```python
from flask import jsonify

from admin_api.api import SyncApi
from admin_api.auth import AuthContext
from admin_api.integrations.flask import require


@app.get("/me")
@require("user.read")
def me(auth: AuthContext, bound: SyncApi):
    return jsonify({"id": str(auth.user.id)})
```

Декоратор `@require(...)`:

1. загружает контекст и клиент с токеном запроса;
2. проверяет permissions;
3. подставляет в аргументы обработчика значения по аннотациям типов `AuthContext` и `SyncApi`.

Каждый аргумент принимает строку, коллекцию строк или `None`. Отдельные аргументы соединяются по И, элементы коллекции — по ИЛИ: `@require("user.read", {"user.update", "user.delete"})`. Значение `None` проверяет только аутентификацию.

Модель проверки: [авторизация](authorization.md#проверка-разрешений).

## Доступ к пользователю и контексту авторизации

После `@require` (или первого вызова `get_request_auth()`) в пределах запроса:

| Способ | Результат |
|---|---|
| аргумент с аннотацией `AuthContext` | `auth.user`, `auth.permissions`, `auth.extras` |
| аргумент с аннотацией `SyncApi` | клиент с токеном текущего пользователя |
| `get_request_auth()` | `RequestAuth(context, api)` |
| `current_auth` | прокси к `AuthContext` |
| `current_api` | прокси к bound-клиенту |

```python
from admin_api.integrations.flask import current_auth, current_api, get_request_auth, require


@app.get("/me")
@require("user.read")
def me():
    bundle = get_request_auth()
    return {
        "id": str(current_auth.user.id),
        "same": str(bundle.context.user.id),
    }
```

`current_auth` и `current_api` сами инициируют загрузку контекста. Без токена это HTTP 401.

Локальный пользователь приложения — отдельная функция поверх `get_request_auth()`, не часть SDK.

## Обработка ошибок

При `exception_handlers=True` (значение по умолчанию) тело ответа: `{"detail": "<сообщение исключения>"}`.

| Исключение | HTTP |
|---|---|
| `TokenNotProvided` | 401 |
| `InvalidTokenException` | 401 |
| `PermissionDenied` | 403 |

`ApiError` интеграция не обрабатывает.

---

[← Назад](README.md) · [Быстрый старт](quickstart.md) · [Авторизация](authorization.md) · [FastAPI](fastapi.md)
