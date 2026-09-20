from __future__ import annotations

import abc
from collections.abc import Mapping
from typing import Protocol


class RemoteCatalog(Protocol):
    def list_titles(self) -> set[str]: ...

    def create(self, title: str, verbose_name: str | None = None) -> None: ...

    def delete(self, title: str) -> None: ...


class CatalogStrategy(abc.ABC):
    @abc.abstractmethod
    def apply(self, local: Mapping[str, str]) -> None:
        raise NotImplementedError

    async def aapply(self, local: Mapping[str, str]) -> None:
        self.apply(local)


class DoNothing(CatalogStrategy):
    def apply(self, local: Mapping[str, str]) -> None:
        return None


class MemoryCatalog:
    def __init__(self, titles: set[str] | None = None) -> None:
        self.titles: set[str] = set(titles or ())

    def list_titles(self) -> set[str]:
        return set(self.titles)

    def create(self, title: str, verbose_name: str | None = None) -> None:
        self.titles.add(title)

    def delete(self, title: str) -> None:
        self.titles.discard(title)


class CreateUnexisted(CatalogStrategy):
    def __init__(self, catalog: RemoteCatalog) -> None:
        self._catalog = catalog

    def apply(self, local: Mapping[str, str]) -> None:
        remote = self._catalog.list_titles()
        for title, verbose_name in local.items():
            if title not in remote:
                self._catalog.create(title, verbose_name)


class FullSync(CatalogStrategy):
    def __init__(self, catalog: RemoteCatalog) -> None:
        self._catalog = catalog

    def apply(self, local: Mapping[str, str]) -> None:
        remote = self._catalog.list_titles()
        for title, verbose_name in local.items():
            if title not in remote:
                self._catalog.create(title, verbose_name)
        for title in remote - set(local):
            self._catalog.delete(title)
