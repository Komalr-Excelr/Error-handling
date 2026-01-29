from src.core.circuit_breaker import CircuitBreaker


def test_circuit_breaker_opens_and_half_open_then_closes():
    # Controlled time progression
    t = {"now": 0.0}

    def time_provider():
        return t["now"]

    cb = CircuitBreaker("svc", failure_threshold=2, reset_timeout_seconds=10, time_provider=time_provider)

    # Two failures -> open
    cb.on_failure()
    cb.on_failure()
    assert cb.state() == CircuitBreaker.OPEN
    assert not cb.allow_request()

    # Advance time to trigger half-open
    t["now"] += 10
    assert cb.state() == CircuitBreaker.HALF_OPEN
    assert cb.allow_request()

    # Success in half-open -> closes
    cb.on_success()
    assert cb.state() == CircuitBreaker.CLOSED

    # Failures again -> open
    cb.on_failure()
    cb.on_failure()
    assert cb.state() == CircuitBreaker.OPEN

    # Advance, then fail probe -> re-open
    t["now"] += 10
    assert cb.state() == CircuitBreaker.HALF_OPEN
    cb.on_failure()
    assert cb.state() == CircuitBreaker.OPEN
