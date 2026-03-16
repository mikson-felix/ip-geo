from typing import Protocol

from app.domain.entities import GeoInfo


class CacheRepository(Protocol):
    async def get(self, ip: str) -> GeoInfo | None: ...
    async def set(self, payload: GeoInfo) -> None: ...


class LocalGeoRepository(Protocol):
    def lookup(self, ip: str) -> GeoInfo | None: ...


class ExternalGeoProvider(Protocol):
    name: str

    async def lookup(self, ip: str) -> GeoInfo | None: ...
