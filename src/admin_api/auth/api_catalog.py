from __future__ import annotations

from uuid import UUID

from admin_api.api.client import AsyncApi, SyncApi
from admin_api.api.dto import PermissionResponse, ServiceResponse
from admin_api.exceptions import ApiError

_PAGE_SIZE = 100


class ApiPermissionCatalog:
    """RemoteCatalog backed by Admin API permissions of one service."""

    def __init__(self, api: SyncApi, service_name: str) -> None:
        self._api = api
        self._service_name = service_name
        self._service_id: UUID | None = None

    def list_titles(self) -> set[str]:
        return {permission.title for permission in self._permissions()}

    def create(self, title: str, verbose_name: str | None = None) -> None:
        self._api.send(
            self._api.permissions.create(
                service_id=self._resolve_service_id(),
                title=title,
                verbose_name=verbose_name or title,
            ),
        )

    def delete(self, title: str) -> None:
        for permission in self._permissions():
            if permission.title == title:
                self._api.send(self._api.permissions.delete(permission.id))

    def _permissions(self) -> list[PermissionResponse]:
        service_id = self._resolve_service_id()
        result: list[PermissionResponse] = []
        page = 1
        while True:
            chunk = self._api.send(
                self._api.permissions.filter(service_name=self._service_name, page=page, size=_PAGE_SIZE),
            )
            result.extend(chunk.data)
            if not chunk.data or len(result) >= chunk.total:
                return [permission for permission in result if permission.service_id == service_id]
            page += 1

    def _resolve_service_id(self) -> UUID:
        if self._service_id is None:
            page = 1
            while self._service_id is None:
                chunk = self._api.send(
                    self._api.services.filter(service_name=self._service_name, page=page, size=_PAGE_SIZE),
                )
                self._service_id = _find_service_id(chunk.data, self._service_name)
                if self._service_id is None and (not chunk.data or page * _PAGE_SIZE >= chunk.total):
                    raise _service_not_found(self._service_name)
                page += 1
        return self._service_id


class AsyncApiPermissionCatalog:
    """AsyncRemoteCatalog backed by Admin API permissions of one service."""

    def __init__(self, api: AsyncApi, service_name: str) -> None:
        self._api = api
        self._service_name = service_name
        self._service_id: UUID | None = None

    async def list_titles(self) -> set[str]:
        return {permission.title for permission in await self._permissions()}

    async def create(self, title: str, verbose_name: str | None = None) -> None:
        await self._api.send(
            self._api.permissions.create(
                service_id=await self._resolve_service_id(),
                title=title,
                verbose_name=verbose_name or title,
            ),
        )

    async def delete(self, title: str) -> None:
        for permission in await self._permissions():
            if permission.title == title:
                await self._api.send(self._api.permissions.delete(permission.id))

    async def _permissions(self) -> list[PermissionResponse]:
        service_id = await self._resolve_service_id()
        result: list[PermissionResponse] = []
        page = 1
        while True:
            chunk = await self._api.send(
                self._api.permissions.filter(service_name=self._service_name, page=page, size=_PAGE_SIZE),
            )
            result.extend(chunk.data)
            if not chunk.data or len(result) >= chunk.total:
                return [permission for permission in result if permission.service_id == service_id]
            page += 1

    async def _resolve_service_id(self) -> UUID:
        if self._service_id is None:
            page = 1
            while self._service_id is None:
                chunk = await self._api.send(
                    self._api.services.filter(service_name=self._service_name, page=page, size=_PAGE_SIZE),
                )
                self._service_id = _find_service_id(chunk.data, self._service_name)
                if self._service_id is None and (not chunk.data or page * _PAGE_SIZE >= chunk.total):
                    raise _service_not_found(self._service_name)
                page += 1
        return self._service_id


def _find_service_id(services: list[ServiceResponse], service_name: str) -> UUID | None:
    for service in services:
        if service.name == service_name and service.id is not None:
            return service.id
    return None


def _service_not_found(service_name: str) -> ApiError:
    return ApiError(f"Service {service_name!r} not found", status_code=404, error_code="service_not_found")
