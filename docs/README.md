# Admin API Python SDK

Клиент Admin API и проверка прав доступа для сервисов на Flask и FastAPI.

SDK извлекает JWT из входящего HTTP-запроса, запрашивает у Admin API текущего пользователя и его permissions, проверяет требуемые права и передаёт в обработчик контекст авторизации и HTTP-клиент с токеном пользователя.

Требования: Python 3.11 или новее.

## Документация

- [Быстрый старт](quickstart.md)
- [Авторизация и permissions](authorization.md)
- [Flask](flask.md)
- [FastAPI](fastapi.md)
- [HTTP-клиент](http-client.md)
- [Исключения](exceptions.md)
- [Конфигурация](configuration.md)
- [Расширение SDK](extending.md)
- [API Reference](api-reference.md)

## Установка

Пакет: `admin-api-python-sdk`. Импорт: `admin_api`.

Ядро (HTTP-клиент без Flask/FastAPI):

```bash
pip install admin-api-python-sdk
```

Интеграции подключаются extras:

```bash
pip install "admin-api-python-sdk[flask]"
pip install "admin-api-python-sdk[fastapi]"
```

Зависимости ядра: `httpx`, `pydantic`. Extra `flask` устанавливает Flask, extra `fastapi` — FastAPI.

## Состав

| Модуль | Назначение |
|---|---|
| `admin_api.api` | HTTP-клиент Admin API |
| `admin_api.auth` | загрузка пользователя и permissions, проверка прав |
| `admin_api.integrations.flask` | декоратор `require`, extension |
| `admin_api.integrations.fastapi` | `Depends`, extension |

Flask-приложение использует `SyncApi` и `AdminApiFlask`. FastAPI-приложение — `AsyncApi` и `AdminApiFastAPI`.
