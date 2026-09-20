# Исключения

Модуль: `admin_api.exceptions`. Базовый класс: `AuthException`.

| Исключение | Когда возникает | Flask / FastAPI |
|---|---|---|
| `TokenNotProvided` | нет токена во входящем запросе; либо `send` с `auth=True` при отсутствии токена на клиенте | 401, `{"detail": "..."}` |
| `InvalidTokenException` | Admin API ответил HTTP 401 | 401, `{"detail": "..."}` |
| `PermissionDenied` | нет требуемого permission либо scoped-валидатор вернул `False` | 403, `{"detail": "..."}` |
| `ApiError` | неуспешный HTTP-ответ Admin API, кроме 401 | не перехватывается |

Сообщение по умолчанию задаётся атрибутом `message` класса и может быть переопределено аргументом конструктора. Для 401 текст часто берётся из JSON-поля `detail` ответа Admin API.

## ApiError

Публичные поля:

| Поле | Тип | Содержимое |
|---|---|---|
| `status_code` | `int` | HTTP-статус ответа Admin API |
| `error_code` | `str` | поле `error_code` JSON, иначе пустая строка |
| `detail` | `dict \| list \| str` | поле `detail` или тело ответа |
| `errors` | `dict \| list \| str` | поле `errors`, иначе пустая строка |

Невалидный JSON в теле ошибки: в `detail` попадает текст ответа.

```python
from admin_api.exceptions import ApiError

try:
    api.send(api.users.get_me())
except ApiError as exc:
    exc.status_code
    exc.error_code
    exc.detail
```

`FailPolicy.DENY` при недоступности Admin API тоже приводит к `ApiError` (или к ошибке httpx). Интеграции их в 401/403 не превращают.

---

[Содержание](README.md) · [Авторизация](authorization.md) · [Конфигурация](configuration.md)
