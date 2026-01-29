from typing import Optional

from src.exceptions.errors import ServiceUnavailableError, UnauthorizedError, InvalidPayloadError


class ElevenLabsService:
    """Mock ElevenLabs service with controllable health."""

    def __init__(self):
        self.healthy = True
        self.force_503 = False

    def set_healthy(self, healthy: bool):
        self.healthy = healthy

    def simulate_503_once(self):
        self.force_503 = True

    def tts(self, text: str) -> str:
        """Simulate a TTS call that may raise errors."""
        if self.force_503:
            self.force_503 = False
            raise ServiceUnavailableError("503 Service Unavailable", service="elevenlabs")
        if not self.healthy:
            raise ServiceUnavailableError("Service down", service="elevenlabs")
        if not text:
            raise InvalidPayloadError("Empty text", service="elevenlabs")
        # Simulate success
        return "AUDIO_BYTES_MOCK"

    def health_check(self) -> bool:
        return self.healthy
