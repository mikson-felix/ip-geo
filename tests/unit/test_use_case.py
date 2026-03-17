import pytest

from app.application.use_cases import GeoLookupUseCase
from app.domain.exceptions import ExternalServiceError, GeoNotFoundError


@pytest.mark.asyncio
async def test_returns_cached_value(cache, geo_payload) -> None:
    await cache.set(geo_payload)

    local_repo = type("LocalRepo", (), {"lookup": lambda self, ip: None})()
    use_case = GeoLookupUseCase(cache=cache, local_repo=local_repo, providers=[])

    result = await use_case.execute("8.8.8.8")

    assert result.ip == "8.8.8.8"
    assert result.source == "maxmind"
    assert result.served_from_cache is True


@pytest.mark.asyncio
async def test_returns_local_value_and_caches(cache, geo_payload) -> None:
    class LocalRepo:
        def __init__(self) -> None:
            self.calls = 0

        def lookup(self, ip: str):
            self.calls += 1
            return geo_payload

    local_repo = LocalRepo()
    use_case = GeoLookupUseCase(cache=cache, local_repo=local_repo, providers=[])

    result = await use_case.execute("8.8.8.8")

    assert result.source == "maxmind"
    cached = await cache.get("8.8.8.8")
    assert cached is not None
    assert cached.country == "United States"
    assert local_repo.calls == 1


@pytest.mark.asyncio
async def test_uses_external_provider_when_local_misses(cache, geo_payload) -> None:
    class LocalRepo:
        def lookup(self, ip: str):
            return None

    provider_payload = geo_payload.model_copy(update={"source": "ipapi"})

    class Provider:
        name = "ipapi"

        async def lookup(self, ip: str):
            return provider_payload

    use_case = GeoLookupUseCase(
        cache=cache,
        local_repo=LocalRepo(),
        providers=[Provider()],
    )

    result = await use_case.execute("8.8.8.8")

    assert result.source == "ipapi"
    cached = await cache.get("8.8.8.8")
    assert cached is not None
    assert cached.source == "ipapi"


@pytest.mark.asyncio
async def test_tries_next_provider_on_external_service_error(cache, geo_payload) -> None:
    class LocalRepo:
        def lookup(self, ip: str):
            return None

    class BadProvider:
        name = "bad"

        async def lookup(self, ip: str):
            raise ExternalServiceError("boom")

    class GoodProvider:
        name = "good"

        async def lookup(self, ip: str):
            return geo_payload.model_copy(update={"source": "ip-api"})

    use_case = GeoLookupUseCase(
        cache=cache,
        local_repo=LocalRepo(),
        providers=[BadProvider(), GoodProvider()],
    )

    result = await use_case.execute("8.8.8.8")

    assert result.source == "ip-api"


@pytest.mark.asyncio
async def test_raises_not_found_when_all_sources_fail(cache) -> None:
    class LocalRepo:
        def lookup(self, ip: str):
            return None

    class BadProvider:
        name = "bad"

        async def lookup(self, ip: str):
            raise ExternalServiceError("boom")

    use_case = GeoLookupUseCase(
        cache=cache,
        local_repo=LocalRepo(),
        providers=[BadProvider()],
    )

    with pytest.raises(GeoNotFoundError):
        await use_case.execute("8.8.8.8")


@pytest.mark.asyncio
async def test_provider_returns_none_and_then_not_found(cache) -> None:
    class LocalRepo:
        def lookup(self, ip: str):
            return None

    class EmptyProvider:
        name = "empty"

        async def lookup(self, ip: str):
            return None

    use_case = GeoLookupUseCase(
        cache=cache,
        local_repo=LocalRepo(),
        providers=[EmptyProvider()],
    )

    with pytest.raises(GeoNotFoundError):
        await use_case.execute("8.8.8.8")
