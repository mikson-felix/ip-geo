import structlog

from app.domain.entities import GeoInfo
from app.domain.exceptions import ExternalServiceError, GeoNotFoundError
from app.domain.interfaces import CacheRepository, ExternalGeoProvider, LocalGeoRepository

logger = structlog.get_logger(__name__)


class GeoLookupUseCase:
    def __init__(
        self,
        cache: CacheRepository,
        local_repo: LocalGeoRepository,
        providers: list[ExternalGeoProvider],
    ) -> None:
        self.cache = cache
        self.local_repo = local_repo
        self.providers = providers

    async def execute(self, ip: str) -> GeoInfo:
        cached = await self.cache.get(ip)
        if cached is not None:
            cached.served_from_cache = True
            logger.info("geo_lookup_cache_hit", ip=ip)
            return cached

        logger.info("geo_lookup_cache_miss", ip=ip)

        local_result = self.local_repo.lookup(ip)
        if local_result is not None:
            await self.cache.set(local_result)
            logger.info("geo_lookup_local_hit", ip=ip, source=local_result.source)
            return local_result

        logger.info("geo_lookup_local_miss", ip=ip)

        for provider in self.providers:
            try:
                result = await provider.lookup(ip)
            except ExternalServiceError:
                logger.warning("geo_lookup_provider_failed", ip=ip, provider=provider.name)
                continue

            if result is not None:
                await self.cache.set(result)
                logger.info("geo_lookup_provider_hit", ip=ip, provider=provider.name)
                return result

            logger.info("geo_lookup_provider_miss", ip=ip, provider=provider.name)

        logger.warning("geo_lookup_not_found", ip=ip)
        raise GeoNotFoundError(f"Geolocation not found for ip={ip}")
