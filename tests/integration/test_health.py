import pytest

from app.application.use_cases import GeoLookupUseCase


@pytest.mark.asyncio
async def test_health_endpoint(app_factory, client_factory, cache) -> None:
    local_repo = type("LocalRepo", (), {"lookup": lambda self, ip: None})()
    use_case = GeoLookupUseCase(cache=cache, local_repo=local_repo, providers=[])

    app = app_factory(use_case)
    client = await client_factory(app)

    response = await client.get("/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
