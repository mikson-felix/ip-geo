from typing import Any

from aiolimiter import AsyncLimiter


class ProviderRateLimiter:
    def __init__(self, requests_per_minute: int) -> None:
        self._limiter = AsyncLimiter(max_rate=requests_per_minute, time_period=60)

    async def __aenter__(self) -> "ProviderRateLimiter":
        await self._limiter.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return await self._limiter.__aexit__(exc_type, exc, tb)
