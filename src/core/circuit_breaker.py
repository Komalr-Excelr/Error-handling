import time
from typing import Callable


class CircuitBreaker:
    """Simple per-service circuit breaker with Closed/Open/Half-Open states."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(
        self,
        service_name: str,
        failure_threshold: int,
        reset_timeout_seconds: int,
        time_provider: Callable[[], float] = time.time,
    ):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout_seconds
        self._time = time_provider

        self.failure_count = 0
        self.last_failure_ts: float | None = None
        self._state = CircuitBreaker.CLOSED

    def state(self) -> str:
        # If open and timeout elapsed, move to half-open
        if self._state == CircuitBreaker.OPEN and self.last_failure_ts is not None:
            if self._time() - self.last_failure_ts >= self.reset_timeout:
                self._state = CircuitBreaker.HALF_OPEN
        return self._state

    def allow_request(self) -> bool:
        s = self.state()
        if s == CircuitBreaker.OPEN:
            return False
        return True

    def on_success(self):
        # On success from half-open, reset to closed
        if self.state() == CircuitBreaker.HALF_OPEN:
            self._state = CircuitBreaker.CLOSED
            self.failure_count = 0
            self.last_failure_ts = None
        elif self.state() == CircuitBreaker.CLOSED:
            # normal success, keep closed
            pass

    def on_failure(self):
        current_state = self.state()
        if current_state == CircuitBreaker.HALF_OPEN:
            # Failed probe -> open again
            self._state = CircuitBreaker.OPEN
            self.last_failure_ts = self._time()
            self.failure_count = max(self.failure_count, self.failure_threshold)
            return

        # Increment failure count
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self._state = CircuitBreaker.OPEN
            self.last_failure_ts = self._time()

    def force_open(self):
        self._state = CircuitBreaker.OPEN
        self.last_failure_ts = self._time()

    def force_close(self):
        self._state = CircuitBreaker.CLOSED
        self.failure_count = 0
        self.last_failure_ts = None
