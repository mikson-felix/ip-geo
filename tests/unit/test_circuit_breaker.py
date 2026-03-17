import pytest

from app.domain.exceptions import CircuitBreakerOpenError
from app.infrastructure.circuit_breaker import CircuitBreaker, CircuitState


def test_circuit_breaker_opens_after_threshold() -> None:
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=60)

    cb.on_failure()
    assert cb.state == CircuitState.CLOSED

    cb.on_failure()
    assert cb.state == CircuitState.OPEN

    with pytest.raises(CircuitBreakerOpenError):
        cb.before_call()


def test_circuit_breaker_closes_on_success() -> None:
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=60)

    cb.on_failure()
    assert cb.state == CircuitState.OPEN

    cb.on_success()
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_half_open_after_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=10)

    cb.on_failure()
    assert cb.state == CircuitState.OPEN

    opened_at = cb._opened_at
    assert opened_at is not None

    monkeypatch.setattr(
        "app.infrastructure.circuit_breaker.monotonic",
        lambda: opened_at + 11,
    )

    assert cb.state == CircuitState.HALF_OPEN
