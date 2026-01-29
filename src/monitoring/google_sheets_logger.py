from typing import Dict
import requests


class GoogleSheetsLogger:
    """HTTP-based logger to a Google Apps Script endpoint, with optional CSV mock.
    If `endpoint_url` is empty but `mock_file_path` is provided, it will append rows to CSV.
    """

    def __init__(self, endpoint_url: str | None, enabled: bool, mock_file_path: str | None = None):
        self.endpoint_url = endpoint_url or ""
        self.mock_file_path = mock_file_path
        self.enabled = enabled

    def log(self, record: Dict):
        if not self.enabled:
            return
        if self.endpoint_url:
            # Best-effort POST; ignore failures
            try:
                requests.post(self.endpoint_url, json=record, timeout=3)
            except Exception:
                pass
        elif self.mock_file_path:
            # Append CSV row for visualization
            try:
                import csv, os
                os.makedirs(os.path.dirname(self.mock_file_path), exist_ok=True)
                write_header = not os.path.exists(self.mock_file_path)
                with open(self.mock_file_path, "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=[
                            "timestamp",
                            "service",
                            "category",
                            "retry_count",
                            "circuit_breaker_state",
                            "message",
                        ],
                    )
                    if write_header:
                        writer.writeheader()
                    writer.writerow(record)
            except Exception:
                pass
