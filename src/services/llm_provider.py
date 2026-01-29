from src.exceptions.errors import ServiceUnavailableError, InvalidPayloadError


class LLMProviderService:
    def __init__(self):
        self.healthy = True

    def set_healthy(self, healthy: bool):
        self.healthy = healthy

    def complete(self, prompt: str) -> str:
        if not self.healthy:
            raise ServiceUnavailableError("LLM unavailable", service="llm")
        if not prompt:
            raise InvalidPayloadError("Empty prompt", service="llm")
        return "Mock completion"

    def health_check(self) -> bool:
        return self.healthy
