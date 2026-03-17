from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any

import fakeredis.aioredis
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.exception_handlers import register_exception_handlers
from app.api.healthcheck import router as healthcheck_router
from app.api.schemas import GeoLookupResponse
from app.api.v1.routes import router as v1_router
from app.application.use_cases import GeoLookupUseCase
from app.config import Settings
from app.domain.entities import GeoInfo
from app.infrastructure.cache import RedisGeoCache


@pytest.fixture
def geo_payload() -> GeoInfo:
    return GeoInfo(
        ip="8.8.8.8",
        country="United States",
        country_code="US",
        city="Mountain View",
        region="California",
        latitude=37.386,
        longitude=-122.0838,
        source="maxmind",
        served_from_cache=False,
    )


@pytest.fixture
async def redis_client() -> AsyncIterator[Any]:
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.flushall()
    await client.aclose()


@pytest.fixture
async def cache(redis_client: Any) -> RedisGeoCache:
    return RedisGeoCache(redis=redis_client, ttl_seconds=900)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        app_name="geoip-service-test",
        debug=False,
        redis_url="redis://localhost:6379/0",
        cache_ttl_seconds=900,
        geoip_db_path=tmp_path / "GeoLite2-City.mmdb",
        ipapi_base_url="https://ipapi.co",
        ipapi_timeout_seconds=3.0,
        ipapi_rate_limit_per_minute=30,
        ipapi_max_retries=3,
        ip_api_base_url="http://ip-api.com",
        ip_api_timeout_seconds=3.0,
        ip_api_rate_limit_per_minute=40,
        ip_api_max_retries=3,
        external_backoff_base_seconds=0.2,
        external_backoff_multiplier=2.0,
        circuit_breaker_failure_threshold=3,
        circuit_breaker_recovery_timeout_seconds=30.0,
        log_level="INFO",
        log_json=True,
    )


@pytest.fixture
def app_factory() -> Callable[[GeoLookupUseCase], FastAPI]:
    def factory(use_case: Any) -> FastAPI:
        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(v1_router, prefix="/api/v1")
        app.include_router(healthcheck_router)

        app.router.routes = [route for route in app.router.routes if route.path != "/lookup/"]

        @app.get("/lookup/", response_model=GeoLookupResponse)
        async def lookup(ip: str) -> GeoLookupResponse:
            from app.common.ip import normalize_ip

            normalized_ip = normalize_ip(ip)
            result = await use_case.execute(normalized_ip)
            return GeoLookupResponse.from_entity(result)

        return app

    return factory


@pytest.fixture
async def client_factory() -> AsyncIterator[Callable[[FastAPI], AsyncClient]]:
    clients: list[AsyncClient] = []

    async def factory(app: FastAPI) -> AsyncClient:
        client = AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        )
        clients.append(client)
        return client

    yield factory

    for client in clients:
        await client.aclose()
