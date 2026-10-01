# Конфигурация

[← Назад](README.md)

## HTTP-клиент

`SyncApi` и `AsyncApi`:

| Параметр | Тип | По умолчанию | Назначение |
|---|---|---|---|
| `base_url` | `str` | обязательный | базовый URL Admin API |
| `token` | `str \| None` | `None` | JWT |
| `timeout` | `float` | `5.0` | таймаут запроса, секунды |
| `transport` | транспорт httpx или `None` | `None` | свой транспорт HTTP |

## Интеграции и менеджеры

`AdminApiFlask`, `AdminApiFastAPI`, `AdminApiAuth`, `AsyncAdminApiAuth`.

| Параметр | Тип | По умолчанию | Назначение |
|---|---|---|---|
| `api` | `SyncApi` или `AsyncApi` | `None` | готовый клиент |
| `base_url` | `str \| None` | `None` | создать клиент, если `api` не передан |
| `timeout_ms` | `int` | `300` | таймаут создаваемого клиента в миллисекундах (`timeout_ms / 1000` секунд) |
| `service_name` | `str \| None` | `None` | имя сервиса для `get_permissions`; обязателен при загрузке контекста |
| `cache` | `AuthCache \| None` | `NoCache` | кэш снимка пользователя и permissions |
| `fail_policy` | `FailPolicy` | `FailPolicy.DENY` | поведение при ошибке загрузки контекста |
| `catalog` | `CatalogStrategy \| None` | `DoNothing` | синхронизация каталога прав при старте |
| `token_parser` | `TokenParser \| None` | `BearerTokenParser()` | только у Flask/FastAPI-интеграций |

Рекомендуется передавать `api=SyncApi(..., timeout=5.0)` / `AsyncApi(..., timeout=5.0)`. При создании клиента через `base_url` таймаут по умолчанию равен 0,3 с.

Нет ни `api`, ни `base_url` — загрузка контекста завершается ошибкой.

`init_app(app, *, exception_handlers=True)` — регистрация в приложении и (по умолчанию) обработчики 401/403.

Если клиент создан через `base_url`, им владеет менеджер: `AdminApiAuth` / `AdminApiFlask` закрывают его методом `close()`, `AsyncAdminApiAuth` / `AdminApiFastAPI` — методом `await aclose()`. FastAPI-интеграция сама вызывает `aclose()` при завершении lifespan. Flask-приложение должно вызвать `close()` при остановке процесса. Переданный через `api=` клиент закрывает код, который его создал.

## BearerTokenParser

| Параметр | По умолчанию | Назначение |
|---|---|---|
| `header` | `"Authorization"` | имя HTTP-заголовка |
| `scheme` | `"Bearer"` | схема (сравнение без учёта регистра) |

## TtlCache

| Параметр | По умолчанию | Назначение |
|---|---|---|
| `ttl_seconds` | `30` | время жизни снимка, секунды |
| `stale_ttl_seconds` | `300` | максимальное время использования снимка после истечения TTL, секунды |
| `maxsize` | `1024` | максимальное число снимков в памяти; при заполнении вытесняется запись, к которой дольше всего не обращались |

Просроченная запись удаляется при обращении к ней. Число записей ограничено `maxsize`.

## FailPolicy

| Значение | Смысл |
|---|---|
| `FailPolicy.DENY` | ошибка загрузки не подавляется |
| `FailPolicy.USE_STALE` | при ошибке HTTP-клиента или ответе Admin API 5xx отдать снимок, если его срок `stale_ttl_seconds` не истёк |

Подробности: [авторизация](authorization.md).

---

[← Назад](README.md) · [HTTP-клиент](http-client.md) · [API Reference](api-reference.md)
