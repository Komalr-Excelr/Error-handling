import time

from src.core.circuit_breaker import CircuitBreaker
from src.core.retry_handler import RetryHandler
from src.exceptions.errors import ServiceUnavailableError


class Sleeper:
    def __init__(self):
        self.sleeps = []

    def sleep(self, t):
        self.sleeps.append(t)


def test_retry_exponential_backoff_transient():
    cb = CircuitBreaker("svc", failure_threshold=3, reset_timeout_seconds=30)
    sleeper = Sleeper()

    retries = RetryHandler(
        "svc", cb, initial_delay_seconds=5, max_attempts=3, backoff_factor=2.0, sleep_fn=sleeper.sleep
    )

    call_count = {"n": 0}

    def op():
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise ServiceUnavailableError("503", service="svc")
        return "ok"

    result = retries.execute(op)
    assert result == "ok"
    # Should have slept with 5 then 10 seconds (but not actually sleeping)
    assert sleeper.sleeps == [5, 10]
