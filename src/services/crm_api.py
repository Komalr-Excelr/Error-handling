from src.exceptions.errors import ServiceUnavailableError, InvalidPayloadError


class CRMApiService:
    def __init__(self):
        self.healthy = True
        self.contacts = [
            {"id": 1, "name": "Alice", "phone": "+1000001"},
            {"id": 2, "name": "Bob", "phone": "+1000002"},
        ]

    def set_healthy(self, healthy: bool):
        self.healthy = healthy

    def next_contact(self):
        if not self.healthy:
            raise ServiceUnavailableError("CRM unavailable", service="crm")
        return self.contacts.pop(0) if self.contacts else None

    def mark_failed(self, contact_id: int, reason: str):
        # In real life, would update CRM; here we just pretend
        return True

    def health_check(self) -> bool:
        return self.healthy
