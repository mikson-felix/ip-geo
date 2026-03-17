import pytest


@pytest.mark.asyncio
async def test_cache_set_and_get(cache, geo_payload) -> None:
    await cache.set(geo_payload)

    result = await cache.get("8.8.8.8")

    assert result is not None
    assert result.ip == geo_payload.ip
    assert result.country == geo_payload.country
    assert result.country_code == geo_payload.country_code
    assert result.city == geo_payload.city
    assert result.region == geo_payload.region
    assert result.latitude == geo_payload.latitude
    assert result.longitude == geo_payload.longitude
    assert result.source == geo_payload.source
    assert result.served_from_cache is False


@pytest.mark.asyncio
async def test_cache_returns_none_for_missing_key(cache) -> None:
    result = await cache.get("1.1.1.1")
    assert result is None
