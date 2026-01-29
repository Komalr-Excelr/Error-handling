import time
from typing import Callable, Any, Optional

from src.exceptions.errors import FailFastError, TransientError, PermanentError
from src.core.circuit_breaker import CircuitBreaker


class RetryHandler:
    """Configurable retry with exponential backoff, integrating with a circuit breaker."""

    def __init__(
        self,
        service_name: str,
        circuit_breaker: CircuitBreaker,
        initial_delay_seconds: float,
        max_attempts: int,
        backoff_factor: float,
        sleep_fn: Callable[[float], None] = time.sleep,
    ):
        self.service_name = service_name
        self.cb = circuit_breaker
        self.initial_delay = initial_delay_seconds
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.sleep = sleep_fn

    def execute(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        # Fail-fast if circuit breaker open
        if not self.cb.allow_request():
            raise FailFastError(f"Circuit open for {self.service_name}", self.service_name)

        attempt = 0
        delay = self.initial_delay
        last_error: Optional[Exception] = None

        while attempt < self.max_attempts:
            try:
                result = func(*args, **kwargs)
                self.cb.on_success()
                return result
            except PermanentError as e:
                # Permanent -> no retries
                self.cb.on_failure()
                raise e
            except TransientError as e:
                last_error = e
                self.cb.on_failure()
                attempt += 1
                if attempt >= self.max_attempts:
                    break
                # Exponential backoff
                self.sleep(delay)
                delay *= self.backoff_factor
            except Exception as e:
                # Unknown -> treat as transient to avoid crashing, but log
                last_error = e
                self.cb.on_failure()
                attempt += 1
                if attempt >= self.max_attempts:
                    break
                self.sleep(delay)
                delay *= self.backoff_factor

        # If we get here, retries exhausted
        if last_error:
            raise last_error
        raise RuntimeError(f"Unknown failure in retry handler for {self.service_name}")
