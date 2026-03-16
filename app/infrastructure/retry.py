import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx

from app.domain.exceptions import ExternalServiceError

T = TypeVar("T")


class RetryPolicy:
    def __init__(
        self,
        max_attempts: int,
        backoff_base: float,
        backoff_multiplier: float,
    ) -> None:
        self.max_attempts = max_attempts
        self.backoff_base = backoff_base
        self.backoff_multiplier = backoff_multiplier

    async def run(
        self,
        operation: Callable[[], Awaitable[T]],
        provider_name: str,
    ) -> T:
        delay = self.backoff_base
        last_exc: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                return await operation()
            except (
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.HTTPStatusError,
            ) as exc:
                last_exc = exc
                if attempt == self.max_attempts:
                    break
                await asyncio.sleep(delay)
                delay *= self.backoff_multiplier

        raise ExternalServiceError(
            f"Provider '{provider_name}' failed after {self.max_attempts} attempts"
        ) from last_exc
