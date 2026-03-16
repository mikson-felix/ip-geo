from dataclasses import dataclass, field
from enum import StrEnum
from time import monotonic

from app.domain.exceptions import CircuitBreakerOpenError


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    failure_threshold: int
    recovery_timeout_seconds: float
    _state: CircuitState = field(init=False, default=CircuitState.CLOSED)
    _failure_count: int = field(init=False, default=0)
    _opened_at: float | None = field(init=False, default=None)

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN and self._opened_at is not None:
            if monotonic() - self._opened_at >= self.recovery_timeout_seconds:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def before_call(self) -> None:
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerOpenError("Circuit breaker is open")

    def on_success(self) -> None:
        self._failure_count = 0
        self._opened_at = None
        self._state = CircuitState.CLOSED

    def on_failure(self) -> None:
        self._failure_count += 1
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = monotonic()
