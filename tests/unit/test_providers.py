import httpx
import pytest
import respx

from app.domain.exceptions import CircuitBreakerOpenError, ExternalServiceError
from app.infrastructure.circuit_breaker import CircuitBreaker
from app.infrastructure.providers import IPApiCoProvider, IPApiProvider
from app.infrastructure.rate_limit import ProviderRateLimiter
from app.infrastructure.retry import RetryPolicy


@pytest.mark.asyncio
async def test_ipapi_provider_retries_and_succeeds() -> None:
    async with httpx.AsyncClient(base_url="https://ipapi.co") as client:
        provider = IPApiCoProvider(
            client=client,
            rate_limiter=ProviderRateLimiter(100),
            retry_policy=RetryPolicy(
                max_attempts=3,
                backoff_base=0,
                backoff_multiplier=1,
            ),
            circuit_breaker=CircuitBreaker(
                failure_threshold=3,
                recovery_timeout_seconds=30,
            ),
        )

        with respx.mock(assert_all_called=True) as mock:
            mock.get("/8.8.8.8/json/").side_effect = [
                httpx.ConnectTimeout("timeout"),
                httpx.Response(
                    200,
                    json={
                        "country_name": "United States",
                        "country_code": "US",
                        "city": "Mountain View",
                        "region": "California",
                        "latitude": 37.386,
                        "longitude": -122.0838,
                    },
                ),
            ]

            result = await provider.lookup("8.8.8.8")

    assert result is not None
    assert result.source == "ipapi"
    assert result.latitude == 37.386
    assert result.longitude == -122.0838


@pytest.mark.asyncio
async def test_ipapi_provider_raises_after_exhausted_retries() -> None:
    async with httpx.AsyncClient(base_url="https://ipapi.co") as client:
        provider = IPApiCoProvider(
            client=client,
            rate_limiter=ProviderRateLimiter(100),
            retry_policy=RetryPolicy(
                max_attempts=2,
                backoff_base=0,
                backoff_multiplier=1,
            ),
            circuit_breaker=CircuitBreaker(
                failure_threshold=3,
                recovery_timeout_seconds=30,
            ),
        )

        with respx.mock(assert_all_called=True) as mock:
            mock.get("/8.8.8.8/json/").side_effect = httpx.ConnectTimeout("timeout")

            with pytest.raises(ExternalServiceError):
                await provider.lookup("8.8.8.8")


@pytest.mark.asyncio
async def test_ipapi_provider_returns_none_on_error_payload() -> None:
    async with httpx.AsyncClient(base_url="https://ipapi.co") as client:
        provider = IPApiCoProvider(
            client=client,
            rate_limiter=ProviderRateLimiter(100),
            retry_policy=RetryPolicy(
                max_attempts=1,
                backoff_base=0,
                backoff_multiplier=1,
            ),
            circuit_breaker=CircuitBreaker(
                failure_threshold=3,
                recovery_timeout_seconds=30,
            ),
        )

        with respx.mock(assert_all_called=True) as mock:
            mock.get("/8.8.8.8/json/").respond(
                200,
                json={"error": True, "reason": "invalid ip"},
            )

            result = await provider.lookup("8.8.8.8")

    assert result is None


@pytest.mark.asyncio
async def test_ip_api_provider_success() -> None:
    async with httpx.AsyncClient(base_url="http://ip-api.com") as client:
        provider = IPApiProvider(
            client=client,
            rate_limiter=ProviderRateLimiter(100),
            retry_policy=RetryPolicy(
                max_attempts=1,
                backoff_base=0,
                backoff_multiplier=1,
            ),
            circuit_breaker=CircuitBreaker(
                failure_threshold=3,
                recovery_timeout_seconds=30,
            ),
        )

        with respx.mock(assert_all_called=True) as mock:
            mock.get("/json/8.8.8.8").respond(
                200,
                json={
                    "status": "success",
                    "country": "United States",
                    "countryCode": "US",
                    "city": "Mountain View",
                    "regionName": "California",
                    "lat": 37.386,
                    "lon": -122.0838,
                },
            )

            result = await provider.lookup("8.8.8.8")

    assert result is not None
    assert result.source == "ip-api"


@pytest.mark.asyncio
async def test_ip_api_provider_returns_none_for_fail_status() -> None:
    async with httpx.AsyncClient(base_url="http://ip-api.com") as client:
        provider = IPApiProvider(
            client=client,
            rate_limiter=ProviderRateLimiter(100),
            retry_policy=RetryPolicy(
                max_attempts=1,
                backoff_base=0,
                backoff_multiplier=1,
            ),
            circuit_breaker=CircuitBreaker(
                failure_threshold=3,
                recovery_timeout_seconds=30,
            ),
        )

        with respx.mock(assert_all_called=True) as mock:
            mock.get("/json/8.8.8.8").respond(
                200,
                json={"status": "fail", "message": "private range"},
            )

            result = await provider.lookup("8.8.8.8")

    assert result is None


@pytest.mark.asyncio
async def test_provider_circuit_breaker_opens_after_failures() -> None:
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=30)

    async with httpx.AsyncClient(base_url="https://ipapi.co") as client:
        provider = IPApiCoProvider(
            client=client,
            rate_limiter=ProviderRateLimiter(100),
            retry_policy=RetryPolicy(
                max_attempts=1,
                backoff_base=0,
                backoff_multiplier=1,
            ),
            circuit_breaker=breaker,
        )

        with respx.mock(assert_all_called=True) as mock:
            mock.get("/8.8.8.8/json/").side_effect = httpx.ConnectTimeout("timeout")

            with pytest.raises(ExternalServiceError):
                await provider.lookup("8.8.8.8")

        with pytest.raises(CircuitBreakerOpenError):
            await provider.lookup("8.8.8.8")
