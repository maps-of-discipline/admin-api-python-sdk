# Быстрый старт

[← Назад](README.md)

Минимальные примеры защиты endpoint. Подробности — в [Flask](flask.md) и [FastAPI](fastapi.md).

Передавайте готовый HTTP-клиент с явным `timeout`. Параметр `base_url` у интеграции создаёт клиент с таймаутом 0,3 с — для сетевых вызовов этого недостаточно.

`service_name` должен совпадать с именем сервиса в Admin API: от него зависят permissions.

## Flask

```bash
pip install "admin-api-python-sdk[flask] @ git+https://github.com/maps-of-discipline/admin-api-python-sdk.git"
```

```python
from flask import Flask, jsonify

from admin_api.api import SyncApi
from admin_api.auth import AuthContext
from admin_api.integrations.flask import AdminApiFlask, require

api = SyncApi("https://admin.example", timeout=5.0)
admin = AdminApiFlask(api=api, service_name="cabinet")

app = Flask(__name__)
admin.init_app(app)


@app.get("/me")
@require("user.read")
def me(auth: AuthContext):
    return jsonify({"id": str(auth.user.id)})
```

Запрос без заголовка `Authorization: Bearer <token>` возвращает **401**. Если у пользователя нет permission `user.read` — **403**.

## FastAPI

```bash
pip install "admin-api-python-sdk[fastapi] @ git+https://github.com/maps-of-discipline/admin-api-python-sdk.git"
```

```python
from fastapi import Depends, FastAPI

from admin_api.api import AsyncApi
from admin_api.auth import AuthContext
from admin_api.integrations.fastapi import AdminApiFastAPI, require

api = AsyncApi("https://admin.example", timeout=5.0)
admin = AdminApiFastAPI(api=api, service_name="cabinet")

app = FastAPI()
admin.init_app(app)


@app.get("/me")
async def me(auth: AuthContext = Depends(require("user.read"))):
    return {"id": str(auth.user.id)}
```

`require()` возвращает dependency. Её нужно обернуть в `Depends` самостоятельно.

Обработчики импортируют `require` из пакета, а не экземпляр `admin`. Интеграция должна быть зарегистрирована через `init_app`.

---

[← Назад](README.md) · [Авторизация](authorization.md) · [Flask](flask.md) · [FastAPI](fastapi.md)
