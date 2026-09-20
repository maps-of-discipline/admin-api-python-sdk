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

Пакет не публикуется на PyPI. Ставить нужно из Git:

```bash
pip install "admin-api-python-sdk @ git+https://github.com/maps-of-discipline/admin-api-python-sdk.git"
```

Интеграции — extras в той же ссылке:

```bash
pip install "admin-api-python-sdk[flask] @ git+https://github.com/maps-of-discipline/admin-api-python-sdk.git"
pip install "admin-api-python-sdk[fastapi] @ git+https://github.com/maps-of-discipline/admin-api-python-sdk.git"
```

В `pyproject.toml`:

```toml
dependencies = [
  "admin-api-python-sdk[fastapi] @ git+https://github.com/maps-of-discipline/admin-api-python-sdk.git",
]
```

Импорт: `admin_api`. Зависимости ядра: `httpx`, `pydantic`. Extra `flask` устанавливает Flask, extra `fastapi` — FastAPI.

Коммит или тег: `git+https://github.com/maps-of-discipline/admin-api-python-sdk.git@<ref>`.

## Состав

| Модуль | Назначение |
|---|---|
| `admin_api.api` | HTTP-клиент Admin API |
| `admin_api.auth` | загрузка пользователя и permissions, проверка прав |
| `admin_api.integrations.flask` | декоратор `require`, extension |
| `admin_api.integrations.fastapi` | `Depends`, extension |

Flask-приложение использует `SyncApi` и `AdminApiFlask`. FastAPI-приложение — `AsyncApi` и `AdminApiFastAPI`.
