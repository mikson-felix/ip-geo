from collections.abc import AsyncIterable

import httpx
from dishka import Provider, Scope, provide
from dishka.integrations.fastapi import FastapiProvider
from redis.asyncio import Redis

from app.application.use_cases import GeoLookupUseCase
from app.config import Settings
from app.domain.interfaces import ExternalGeoProvider
from app.infrastructure.cache import RedisGeoCache
from app.infrastructure.circuit_breaker import CircuitBreaker
from app.infrastructure.local_geoip import MaxMindGeoRepository
from app.infrastructure.providers import IPApiCoProvider, IPApiProvider
from app.infrastructure.rate_limit import ProviderRateLimiter
from app.infrastructure.retry import RetryPolicy


class AppProvider(Provider):
    @provide(scope=Scope.APP)
    def settings(self) -> Settings:
        from app.config import get_settings

        return get_settings()

    @provide(scope=Scope.APP)
    async def redis(self, settings: Settings) -> AsyncIterable[Redis]:  # type: ignore[type-arg]
        client = Redis.from_url(settings.redis_url, decode_responses=True)
        try:
            yield client
        finally:
            await client.close()

    @provide(scope=Scope.APP)
    def cache(self, redis: Redis, settings: Settings) -> RedisGeoCache:  # type: ignore[type-arg]
        return RedisGeoCache(redis=redis, ttl_seconds=settings.cache_ttl_seconds)

    @provide(scope=Scope.APP)
    def local_repo(self, settings: Settings) -> MaxMindGeoRepository:
        return MaxMindGeoRepository.from_path(str(settings.geoip_db_path))

    @provide(scope=Scope.APP)
    async def ipapi_client(self, settings: Settings) -> AsyncIterable[httpx.AsyncClient]:
        client = httpx.AsyncClient(
            base_url=settings.ipapi_base_url,
            timeout=settings.ipapi_timeout_seconds,
        )
        try:
            yield client
        finally:
            await client.aclose()

    @provide(scope=Scope.APP)
    async def ip_api_client(self, settings: Settings) -> AsyncIterable[httpx.AsyncClient]:
        client = httpx.AsyncClient(
            base_url=settings.ip_api_base_url,
            timeout=settings.ip_api_timeout_seconds,
        )
        try:
            yield client
        finally:
            await client.aclose()

    @provide(scope=Scope.APP)
    def ipapi_rate_limiter(self, settings: Settings) -> ProviderRateLimiter:
        return ProviderRateLimiter(settings.ipapi_rate_limit_per_minute)

    @provide(scope=Scope.APP)
    def ip_api_rate_limiter(self, settings: Settings) -> ProviderRateLimiter:
        return ProviderRateLimiter(settings.ip_api_rate_limit_per_minute)

    @provide(scope=Scope.APP)
    def ipapi_retry_policy(self, settings: Settings) -> RetryPolicy:
        return RetryPolicy(
            max_attempts=settings.ipapi_max_retries,
            backoff_base=settings.external_backoff_base_seconds,
            backoff_multiplier=settings.external_backoff_multiplier,
        )

    @provide(scope=Scope.APP)
    def ip_api_retry_policy(self, settings: Settings) -> RetryPolicy:
        return RetryPolicy(
            max_attempts=settings.ip_api_max_retries,
            backoff_base=settings.external_backoff_base_seconds,
            backoff_multiplier=settings.external_backoff_multiplier,
        )

    @provide(scope=Scope.APP)
    def ipapi_circuit_breaker(self, settings: Settings) -> CircuitBreaker:
        return CircuitBreaker(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_timeout_seconds=settings.circuit_breaker_recovery_timeout_seconds,
        )

    @provide(scope=Scope.APP)
    def ip_api_circuit_breaker(self, settings: Settings) -> CircuitBreaker:
        return CircuitBreaker(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            recovery_timeout_seconds=settings.circuit_breaker_recovery_timeout_seconds,
        )

    @provide(scope=Scope.APP)
    def ipapi_provider(
        self,
        ipapi_client: httpx.AsyncClient,
        ipapi_rate_limiter: ProviderRateLimiter,
        ipapi_retry_policy: RetryPolicy,
        ipapi_circuit_breaker: CircuitBreaker,
    ) -> IPApiCoProvider:
        return IPApiCoProvider(
            client=ipapi_client,
            rate_limiter=ipapi_rate_limiter,
            retry_policy=ipapi_retry_policy,
            circuit_breaker=ipapi_circuit_breaker,
        )

    @provide(scope=Scope.APP)
    def ip_api_provider(
        self,
        ip_api_client: httpx.AsyncClient,
        ip_api_rate_limiter: ProviderRateLimiter,
        ip_api_retry_policy: RetryPolicy,
        ip_api_circuit_breaker: CircuitBreaker,
    ) -> IPApiProvider:
        return IPApiProvider(
            client=ip_api_client,
            rate_limiter=ip_api_rate_limiter,
            retry_policy=ip_api_retry_policy,
            circuit_breaker=ip_api_circuit_breaker,
        )

    @provide(scope=Scope.REQUEST)
    def geo_lookup_use_case(
        self,
        cache: RedisGeoCache,
        local_repo: MaxMindGeoRepository,
        ipapi_provider: IPApiCoProvider,
        ip_api_provider: IPApiProvider,
    ) -> GeoLookupUseCase:
        providers: list[ExternalGeoProvider] = [ipapi_provider, ip_api_provider]
        return GeoLookupUseCase(
            cache=cache,
            local_repo=local_repo,
            providers=providers,
        )


def get_providers() -> tuple[Provider, ...]:
    return (
        AppProvider(),
        FastapiProvider(),
    )
