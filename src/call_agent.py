import time
import yaml
from typing import Dict, Any

from src.core.circuit_breaker import CircuitBreaker
from src.core.retry_handler import RetryHandler
from src.core.health_check import HealthChecker
from src.monitoring.logger import StructuredLogger
from src.monitoring.google_sheets_logger import GoogleSheetsLogger
from src.monitoring.alert_handler import AlertHandler
from src.exceptions.errors import FailFastError, TransientError, PermanentError
from src.services.eleven_labs import ElevenLabsService
from src.services.llm_provider import LLMProviderService
from src.services.crm_api import CRMApiService


class CallAgent:
    def __init__(self, config: Dict[str, Any]):
        # Monitoring
        gsheet_logger = GoogleSheetsLogger(
            endpoint_url=config.get("logging", {}).get("google_sheets", {}).get("endpoint_url"),
            enabled=config.get("logging", {}).get("google_sheets", {}).get("enabled", False),
            mock_file_path=config.get("logging", {}).get("google_sheets", {}).get("mock_file_path"),
        )
        self.logger = StructuredLogger(
            file_path=config.get("logging", {}).get("file_path", "logs/app.log"),
            level=config.get("logging", {}).get("level", "INFO"),
            gsheet=gsheet_logger,
        )
        self.alerts = AlertHandler(config.get("alerts", {}))

        # Services
        self.eleven = ElevenLabsService()
        self.llm = LLMProviderService()
        self.crm = CRMApiService()

        # Circuit breakers
        cb_cfg = config.get("circuit_breaker", {})
        self.eleven_cb = CircuitBreaker(
            "elevenlabs", cb_cfg.get("failure_threshold", 3), cb_cfg.get("reset_timeout_seconds", 30)
        )
        self.llm_cb = CircuitBreaker(
            "llm", cb_cfg.get("failure_threshold", 3), cb_cfg.get("reset_timeout_seconds", 30)
        )

        # Retry config
        retry_cfg = config.get("retry", {})
        self.eleven_retry = RetryHandler(
            "elevenlabs",
            self.eleven_cb,
            initial_delay_seconds=retry_cfg.get("initial_delay_seconds", 5),
            max_attempts=retry_cfg.get("max_attempts", 3),
            backoff_factor=retry_cfg.get("backoff_factor", 2.0),
        )
        self.llm_retry = RetryHandler(
            "llm",
            self.llm_cb,
            initial_delay_seconds=retry_cfg.get("initial_delay_seconds", 5),
            max_attempts=retry_cfg.get("max_attempts", 3),
            backoff_factor=retry_cfg.get("backoff_factor", 2.0),
        )

        # Health checks
        hc_cfg = config.get("health_check", {})
        self.health = HealthChecker(hc_cfg.get("interval_seconds", 10))
        self.health.register("elevenlabs", self.eleven.health_check, self.eleven_cb)
        self.health.register("llm", self.llm.health_check, self.llm_cb)
        self.health.register("crm", self.crm.health_check, CircuitBreaker("crm", 3, 30))

    def _log(self, service: str, category: str, retry_count: int, cb_state: str, message: str):
        self.logger.log_event(
            {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "service": service,
                "category": category,
                "retry_count": retry_count,
                "circuit_breaker_state": cb_state,
                "message": message,
            }
        )

    def process_queue(self):
        self.health.start()
        try:
            while True:
                contact = self.crm.next_contact()
                if not contact:
                    break
                text = f"Hello {contact['name']}!"  # simple prompt -> tts
                retry_count = 0
                try:
                    audio = self.eleven_retry.execute(self.eleven.tts, text)
                    self._log("elevenlabs", "success", retry_count, self.eleven_cb.state(), "TTS success")
                    # Normally, would place the audio or continue the call
                except FailFastError as e:
                    self._log("elevenlabs", "transient", retry_count, self.eleven_cb.state(), str(e))
                    # Graceful degradation: mark failed and move on
                    self.crm.mark_failed(contact["id"], str(e))
                    self.alerts.alert_critical(
                        subject="Circuit breaker open for ElevenLabs",
                        message="Fail-fast: ElevenLabs unhealthy",
                    )
                    continue
                except PermanentError as e:
                    self._log("elevenlabs", "permanent", retry_count, self.eleven_cb.state(), str(e))
                    self.crm.mark_failed(contact["id"], str(e))
                    self.alerts.alert_critical("Permanent failure", str(e))
                    continue
                except TransientError as e:
                    # Retries exhausted
                    self._log("elevenlabs", "transient", self.eleven_retry.max_attempts, self.eleven_cb.state(), str(e))
                    self.crm.mark_failed(contact["id"], str(e))
                    self.alerts.alert_critical("Retries exhausted", str(e))
                    continue
        finally:
            self.health.stop()


def load_config() -> Dict[str, Any]:
    import os
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cfg_path = os.path.join(base_dir, "config", "settings.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    cfg = load_config()
    agent = CallAgent(cfg)
    # Simulate required scenario: ElevenLabs returns 503
    agent.eleven.simulate_503_once()
    agent.process_queue()
