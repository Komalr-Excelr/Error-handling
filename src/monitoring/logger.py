import json
import logging
import os
from typing import Dict, Optional

from src.monitoring.google_sheets_logger import GoogleSheetsLogger


def _ensure_log_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


class StructuredLogger:
    def __init__(self, file_path: str, level: str = "INFO", gsheet: Optional[GoogleSheetsLogger] = None):
        _ensure_log_dir(file_path)
        self.logger = logging.getLogger("ai_call_agent")
        if not self.logger.handlers:
            handler = logging.FileHandler(file_path)
            handler.setLevel(getattr(logging, level.upper(), logging.INFO))
            self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
            self.logger.addHandler(handler)
        self.gsheet = gsheet

    def log_event(self, record: Dict):
        self.logger.info(json.dumps(record))
        if self.gsheet and self.gsheet.enabled:
            try:
                self.gsheet.log(record)
            except Exception:
                # Swallow Google Sheets failures to avoid blocking
                pass
