import threading
import time
from typing import Callable, Dict

from src.core.circuit_breaker import CircuitBreaker


class HealthChecker:
    """Periodic health checks for external services."""

    def __init__(self, interval_seconds: int):
        self.interval = interval_seconds
        self._checks: Dict[str, Callable[[], bool]] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def register(self, service_name: str, check_fn: Callable[[], bool], cb: CircuitBreaker):
        self._checks[service_name] = check_fn
        self._circuit_breakers[service_name] = cb

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)

    def _run_loop(self):
        while not self._stop.is_set():
            self.run_once()
            time.sleep(self.interval)

    def run_once(self):
        """Run a single health check cycle. Useful for tests or manual triggering."""
        for name, check_fn in self._checks.items():
            cb = self._circuit_breakers[name]
            try:
                healthy = check_fn()
                if healthy:
                    cb.force_close()
                else:
                    cb.force_open()
            except Exception:
                cb.force_open()

    
