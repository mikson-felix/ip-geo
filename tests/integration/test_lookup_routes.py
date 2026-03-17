import pytest

from app.application.use_cases import GeoLookupUseCase
from app.domain.exceptions import ExternalServiceError


@pytest.mark.asyncio
async def test_lookup_returns_422_for_invalid_ip(app_factory, client_factory, cache) -> None:
    local_repo = type("LocalRepo", (), {"lookup": lambda self, ip: None})()
    use_case = GeoLookupUseCase(cache=cache, local_repo=local_repo, providers=[])

    app = app_factory(use_case)
    client = await client_factory(app)

    response = await client.get("/lookup/", params={"ip": "not-an-ip"})

    assert response.status_code == 422
    assert response.json() == {
        "code": "invalid_ip",
        "message": "Invalid IP address",
    }


@pytest.mark.asyncio
async def test_lookup_returns_404_when_not_found(app_factory, client_factory, cache) -> None:
    local_repo = type("LocalRepo", (), {"lookup": lambda self, ip: None})()
    use_case = GeoLookupUseCase(cache=cache, local_repo=local_repo, providers=[])

    app = app_factory(use_case)
    client = await client_factory(app)

    response = await client.get("/lookup/", params={"ip": "8.8.8.8"})

    assert response.status_code == 404
    assert response.json() == {
        "code": "geo_not_found",
        "message": "Geolocation not found for ip=8.8.8.8",
    }


@pytest.mark.asyncio
async def test_lookup_returns_local_result_with_formatted_coordinates(
    app_factory,
    client_factory,
    cache,
    geo_payload,
) -> None:
    class LocalRepo:
        def lookup(self, ip: str):
            return geo_payload

    use_case = GeoLookupUseCase(cache=cache, local_repo=LocalRepo(), providers=[])

    app = app_factory(use_case)
    client = await client_factory(app)

    response = await client.get("/lookup/", params={"ip": "8.8.8.8"})

    assert response.status_code == 200
    body = response.json()

    assert body["ip"] == "8.8.8.8"
    assert body["country"] == "United States"
    assert body["country_code"] == "US"
    assert body["city"] == "Mountain View"
    assert body["region"] == "California"
    assert body["source"] == "maxmind"
    assert body["served_from_cache"] is False
    assert body["latitude"] == 37.386
    assert body["longitude"] == -122.0838
    assert body["latitude_formatted"] == "37.386000"
    assert body["longitude_formatted"] == "-122.083800"


@pytest.mark.asyncio
async def test_lookup_returns_cache_on_second_request(
    app_factory,
    client_factory,
    cache,
    geo_payload,
) -> None:
    class LocalRepo:
        def __init__(self) -> None:
            self.calls = 0

        def lookup(self, ip: str):
            self.calls += 1
            return geo_payload

    local_repo = LocalRepo()
    use_case = GeoLookupUseCase(cache=cache, local_repo=local_repo, providers=[])

    app = app_factory(use_case)
    client = await client_factory(app)

    first = await client.get("/lookup/", params={"ip": "8.8.8.8"})
    second = await client.get("/lookup/", params={"ip": "8.8.8.8"})

    assert first.status_code == 200
    assert second.status_code == 200

    first_body = first.json()
    second_body = second.json()

    assert first_body["source"] == "maxmind"
    assert first_body["served_from_cache"] is False
    assert second_body["source"] == "maxmind"
    assert second_body["served_from_cache"] is True
    assert local_repo.calls == 1


@pytest.mark.asyncio
async def test_lookup_returns_500_for_unhandled_exception(
    app_factory,
    client_factory,
    cache,
) -> None:
    class BrokenUseCase:
        async def execute(self, ip: str):
            raise RuntimeError("unexpected failure")

    app = app_factory(BrokenUseCase())
    client = await client_factory(app)

    response = await client.get("/lookup/", params={"ip": "8.8.8.8"})

    assert response.status_code == 500
    assert response.json() == {
        "code": "internal_server_error",
        "message": "Internal server error",
    }


@pytest.mark.asyncio
async def test_lookup_returns_502_for_external_service_error(
    app_factory,
    client_factory,
    cache,
) -> None:
    class ExplodingUseCase:
        async def execute(self, ip: str):
            raise ExternalServiceError("Provider 'ipapi' failed after 3 attempts")

    app = app_factory(ExplodingUseCase())
    client = await client_factory(app)

    response = await client.get("/lookup/", params={"ip": "8.8.8.8"})

    assert response.status_code == 502
    assert response.json() == {
        "code": "external_service_error",
        "message": "Provider 'ipapi' failed after 3 attempts",
    }
