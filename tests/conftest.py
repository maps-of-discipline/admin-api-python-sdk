from __future__ import annotations

import base64
import json
from uuid import UUID

USER_ID = UUID("11111111-1111-1111-1111-111111111111")

ME_PAYLOAD = {
    "id": str(USER_ID),
    "external_id": "220003",
    "role": "student",
    "external_role": "stud",
    "type_": "UserType.lk",
    "name": "Иван",
    "surname": "Иванов",
    "patronymic": "Иванович",
    "email": "i.i.ivanov@example.com",
    "faculty": "Факультет информационных технологий",
    "login": "i.i.ivanov",
    "last_login": "2026-05-15T22:44:45.059758Z",
    "created_at": "2026-05-15T22:44:45.059764Z",
    "sex": "Male",
    "study_status": "Учится",
    "degree_level": "Магистратура",
    "study_group": "254-352",
    "specialization": "Системы управления информационной безопасностью",
    "finance": "Бюджетная",
    "form": "Очная",
    "enter_year": "2025/2026",
    "course": "2",
    "department_code": "2025-3445",
    "photo_url": "",
}

CLAIMS = {
    "user_id": str(USER_ID),
    "role": "student",
    "service_name": "cabinet",
    "permissions": ["user.approved", "canViewCabinet"],
    "iat": 1789635876,
    "expires_at": "2026-09-17T12:04:36.423449",
}


def make_token(claims: dict) -> str:
    def encode(data: dict) -> str:
        raw = json.dumps(data).encode()
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    return f"{encode({'alg': 'HS256', 'typ': 'JWT'})}.{encode(claims)}.signature"


TOKEN = make_token(CLAIMS)
FOREIGN_SERVICE_TOKEN = make_token({**CLAIMS, "service_name": "kd_maps"})
