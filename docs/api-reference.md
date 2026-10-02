# API Reference

[← Назад](README.md)

Краткий перечень публичного API. Поведение — в тематических разделах.

## `admin_api`

| Имя | Описание |
|---|---|
| `SyncApi` | синхронный HTTP-клиент |
| `AsyncApi` | асинхронный HTTP-клиент |
| `Operation` | дескриптор запроса |
| `AuthContext` | пользователь, permissions, `extras` |
| `AdminApiAuth` | sync-менеджер авторизации |
| `AsyncAdminApiAuth` | async-менеджер авторизации |

## `admin_api.auth`

| Имя | Описание |
|---|---|
| `AuthContext` | `user`, `permissions`, `extras`; методы `has()`, `scopes()` |
| `AdminApiAuth` | `load`, `check`, `assert_permissions`, `add_permission`, `set_middlewares`, `sync_catalog`, `close` |
| `AsyncAdminApiAuth` | те же операции в async-варианте, закрытие клиента через `aclose` |
| `PermissionBase` / `PermissionValidator` | scoped-проверка (sync) |
| `AsyncPermissionBase` / `AsyncPermissionValidator` | scoped-проверка (async) |
| `PermissionVerifier` / `AsyncPermissionVerifier` | реестр прав; sync-менеджер также принимает verifier через `add_permission_verifier` |
| `Middleware` / `AsyncMiddleware` | тип middleware |
| `BearerTokenParser` / `TokenParser` | извлечение JWT |
| `NoCache` / `TtlCache` / `AuthCache` / `AuthSnapshot` / `token_hash` | кэш снимка |
| `FailPolicy` | `DENY`, `USE_STALE` |
| `DoNothing` / `CreateUnexisted` / `FullSync` / `CatalogStrategy` / `RemoteCatalog` / `MemoryCatalog` | каталог прав |

`AdminApiAuth.check(required, token, request=None)` загружает контекст и проверяет права. `required` принимает `Collection[str] | str | None`; коллекция проверяется по ИЛИ. В `require` отдельные аргументы соединяются по И. `load(token)` возвращает `(AuthContext, клиент)` без проверки permission.

У `AsyncAdminApiAuth` нет `add_permission_verifier`.

## `admin_api.integrations.flask`

| Имя | Описание |
|---|---|
| `AdminApiFlask` | extension, наследник `AdminApiAuth` |
| `require` | декоратор защиты route |
| `get_request_auth` | `RequestAuth` текущего запроса |
| `RequestAuth` | `context`, `api` |
| `current_auth` / `current_api` | прокси к контексту и клиенту |
| `FLASK_EXTENSION_NAME` | ключ в `app.extensions` (`"admin_api"`) |

## `admin_api.integrations.fastapi`

| Имя | Описание |
|---|---|
| `AdminApiFastAPI` | extension, наследник `AsyncAdminApiAuth` |
| `require` | фабрика FastAPI-dependency |
| `get_request_auth` | dependency, `RequestAuth` |
| `get_api` | dependency, bound `AsyncApi` |
| `RequestAuth` | `context`, `api` |
| `install_exception_handlers` | 401/403 |
| `STATE_KEY` | атрибут `app.state` (`"admin_api"`) |

`require` во Flask и FastAPI — разные объекты с одинаковым именем.

## `admin_api.api.users`

`Users`, модели пользователя и аккаунтов, `UserGetByFiltersRequest`, `UsersPaginatedResponse`, `Scope`, `UserPermissions`.

## `admin_api.api.mplk`

`Mplk` и модели ответов `MPLKGetGroupsResponse`, `MPLKGetStudentsResponse`, `MPLKGetScheduleResponse`, `MPLKGetSemesterResponse`, `MPLKGetSessionResponse`, `MPLKGetUserInfoResponse`, `MPLKGetStaffResponse`.

## `admin_api.api.services`

`Services`, `ServiceCreate`, `ServiceUpdate`, `ServiceIconUpdate`, `ServiceColorUpdate`, `ServiceGetByFiltersRequest`, `ServiceResponse`, `ServicesPaginatedResponse`.

## Остальные ресурсы Admin API

| Ресурс | Классы и схемы |
|---|---|
| `admin_api.api.service_roles` | `ServiceRoles`, запросы и ответы ролей сервиса, назначения permissions |
| `admin_api.api.units` | `Units`, `UnitGet`, `UnitResponse`, `UnitTreeResponse`, `UnitType`, `ShortUnit` |
| `admin_api.api.unit_types` | `UnitTypes`, `UnitType` |
| `admin_api.api.user_service_roles` | `UserServiceRoles`, запросы и ответы назначений, `ScopeItem` |
| `admin_api.api.permissions` | `Permissions`, запросы и ответы permissions |

## `admin_api.exceptions`

`AuthException`, `TokenNotProvided`, `InvalidTokenException`, `PermissionDenied`, `ApiError`.

## `AuthContext`

```python
auth.user            # FullUser
auth.permissions     # dict[str, list[Scope]]
auth.extras          # dict
auth.has("user.read")
auth.scopes("program.manage")
```

---

[← Назад](README.md) · [Конфигурация](configuration.md) · [Исключения](exceptions.md)
