import pytest

from app.bootstrap import run_startup_checks
from app.domain.exceptions import StartupCheckError


class DummyRedis:
    def __init__(self, should_ping: bool = True) -> None:
        self._should_ping = should_ping
        self.closed = False

    async def ping(self) -> bool:
        return self._should_ping

    async def aclose(self) -> None:
        self.closed = True


class DummySettings:
    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url


@pytest.mark.asyncio
async def test_startup_checks_pass_when_redis_ping_is_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_redis = DummyRedis(should_ping=True)

    monkeypatch.setattr(
        "app.bootstrap.Redis.from_url",
        lambda *args, **kwargs: dummy_redis,
    )

    await run_startup_checks(DummySettings(redis_url="redis://localhost:6379/0"))

    assert dummy_redis.closed is True


@pytest.mark.asyncio
async def test_startup_checks_fail_when_redis_ping_is_not_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dummy_redis = DummyRedis(should_ping=False)

    monkeypatch.setattr(
        "app.bootstrap.Redis.from_url",
        lambda *args, **kwargs: dummy_redis,
    )

    with pytest.raises(StartupCheckError, match="Redis ping failed"):
        await run_startup_checks(DummySettings(redis_url="redis://localhost:6379/0"))

    assert dummy_redis.closed is True
