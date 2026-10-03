from __future__ import annotations

import abc
from collections.abc import Awaitable, Callable, Collection
from typing import TypeAlias

from admin_api.auth.context import AuthContext

Middleware: TypeAlias = Callable[[AuthContext], dict | None]
AsyncMiddleware: TypeAlias = Callable[[AuthContext], Awaitable[dict | None]]


class PermissionValidator(abc.ABC):
    def __init__(self, permission_cls: type[PermissionBase]) -> None:
        self.permission = permission_cls

    @abc.abstractmethod
    def validate(self, auth: AuthContext, request: object | None = None) -> bool:
        raise NotImplementedError


class AsyncPermissionValidator(abc.ABC):
    def __init__(self, permission_cls: type[AsyncPermissionBase]) -> None:
        self.permission = permission_cls

    @abc.abstractmethod
    async def validate(self, auth: AuthContext, request: object | None = None) -> bool:
        raise NotImplementedError


class PermissionBase(abc.ABC):
    title: str
    verbose_name: str | None = None
    validators: Collection[type[PermissionValidator]]

    @classmethod
    def check(cls, auth: AuthContext, request: object | None = None) -> bool:
        for validator in cls.validators:
            if not validator(cls).validate(auth, request=request):
                return False
        return True


class AsyncPermissionBase(abc.ABC):
    title: str
    verbose_name: str | None = None
    validators: Collection[type[AsyncPermissionValidator]]

    @classmethod
    async def check(cls, auth: AuthContext, request: object | None = None) -> bool:
        for validator in cls.validators:
            if not await validator(cls).validate(auth, request=request):
                return False
        return True


class PermissionVerifier:
    def __init__(self) -> None:
        self._permissions: dict[str, type[PermissionBase]] = {}

    def add_permission(self, permission: type[PermissionBase]) -> None:
        self._permissions[permission.title] = permission

    def catalog(self) -> dict[str, str]:
        return {
            permission.title: permission.verbose_name or permission.title for permission in self._permissions.values()
        }

    def validate(
        self,
        auth: AuthContext,
        required: Collection[str] | str,
        request: object | None = None,
    ) -> bool:
        if isinstance(required, str):
            required = (required,)
        for title in required:
            if title not in auth.permissions:
                continue
            permission = self._permissions.get(title)
            if permission is None or permission.check(auth, request=request):
                return True
        return False


class AsyncPermissionVerifier:
    def __init__(self) -> None:
        self._permissions: dict[str, type[AsyncPermissionBase]] = {}

    def add_permission(self, permission: type[AsyncPermissionBase]) -> None:
        self._permissions[permission.title] = permission

    def catalog(self) -> dict[str, str]:
        return {
            permission.title: permission.verbose_name or permission.title for permission in self._permissions.values()
        }

    async def validate(
        self,
        auth: AuthContext,
        required: Collection[str] | str,
        request: object | None = None,
    ) -> bool:
        if isinstance(required, str):
            required = (required,)
        for title in required:
            if title not in auth.permissions:
                continue
            permission = self._permissions.get(title)
            if permission is None or await permission.check(auth, request=request):
                return True
        return False


def apply_middleware_result(context: AuthContext, middleware: object, result: dict | None) -> None:
    if not result:
        return
    name = getattr(middleware, "__name__", middleware.__class__.__name__)
    context.extras[name] = result
