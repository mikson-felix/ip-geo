from abc import ABC, abstractmethod

import httpx
import structlog

from app.domain.entities import GeoInfo
from app.infrastructure.circuit_breaker import CircuitBreaker
from app.infrastructure.rate_limit import ProviderRateLimiter
from app.infrastructure.retry import RetryPolicy

logger = structlog.get_logger(__name__)


class BaseExternalProvider(ABC):
    name: str

    def __init__(
        self,
        client: httpx.AsyncClient,
        rate_limiter: ProviderRateLimiter,
        retry_policy: RetryPolicy,
        circuit_breaker: CircuitBreaker,
    ) -> None:
        self._client = client
        self._rate_limiter = rate_limiter
        self._retry_policy = retry_policy
        self._circuit_breaker = circuit_breaker

    async def lookup(self, ip: str) -> GeoInfo | None:
        self._circuit_breaker.before_call()

        async def operation() -> GeoInfo | None:
            async with self._rate_limiter:
                logger.info(
                    "provider_request",
                    provider=self.name,
                    ip=ip,
                    circuit_state=self._circuit_breaker.state.value,
                )
                return await self._perform_lookup(ip)

        try:
            result = await self._retry_policy.run(operation, provider_name=self.name)
        except Exception:
            self._circuit_breaker.on_failure()
            logger.warning(
                "provider_failed",
                provider=self.name,
                ip=ip,
                circuit_state=self._circuit_breaker.state.value,
            )
            raise

        self._circuit_breaker.on_success()
        return result

    @abstractmethod
    async def _perform_lookup(self, ip: str) -> GeoInfo | None:
        raise NotImplementedError


class IPApiCoProvider(BaseExternalProvider):
    name = "ipapi"

    async def _perform_lookup(self, ip: str) -> GeoInfo | None:
        response = await self._client.get(f"/{ip}/json/")
        response.raise_for_status()
        data = response.json()

        if data.get("error"):
            return None

        return GeoInfo(
            ip=ip,
            country=data.get("country_name"),
            country_code=data.get("country_code"),
            city=data.get("city"),
            region=data.get("region"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            source=self.name,
        )


class IPApiProvider(BaseExternalProvider):
    name = "ip-api"

    async def _perform_lookup(self, ip: str) -> GeoInfo | None:
        response = await self._client.get(f"/json/{ip}")
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "success":
            return None

        return GeoInfo(
            ip=ip,
            country=data.get("country"),
            country_code=data.get("countryCode"),
            city=data.get("city"),
            region=data.get("regionName"),
            latitude=data.get("lat"),
            longitude=data.get("lon"),
            source=self.name,
        )
