# admin-api-python-sdk

Клиент Admin API и проверка прав для Flask и FastAPI.

Документация: [docs/README.md](docs/README.md).

```bash
pip install "admin-api-python-sdk[fastapi] @ git+https://github.com/maps-of-discipline/admin-api-python-sdk.git"
pip install "admin-api-python-sdk[flask] @ git+https://github.com/maps-of-discipline/admin-api-python-sdk.git"
```

Проверка против запущенного Admin API (только локальный или тестовый стенд — скрипт создаёт и удаляет данные):

```bash
ADMIN_API_URL=http://127.0.0.1:8001 uv run python scripts/e2e_check.py
```
