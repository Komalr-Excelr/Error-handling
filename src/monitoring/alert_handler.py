import smtplib
from email.mime.text import MIMEText
from typing import List, Dict, Any
import requests


class AlertHandler:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def alert_critical(self, subject: str, message: str):
        self._send_email(subject, message)
        self._send_telegram(message)
        self._send_webhook({"subject": subject, "message": message})

    def _send_email(self, subject: str, message: str):
        cfg = self.config.get("email", {})
        if not cfg.get("enabled"):
            return
        try:
            msg = MIMEText(message)
            msg["Subject"] = subject
            msg["From"] = cfg.get("from")
            recipients: List[str] = cfg.get("to") or []
            msg["To"] = ", ".join(recipients)

            with smtplib.SMTP(cfg.get("smtp_host"), cfg.get("smtp_port")) as server:
                server.starttls()
                username = cfg.get("username")
                password = cfg.get("password")
                if username and password:
                    server.login(username, password)
                server.sendmail(cfg.get("from"), recipients, msg.as_string())
        except Exception:
            # Avoid raising on alert failures
            pass

    def _send_telegram(self, message: str):
        cfg = self.config.get("telegram", {})
        if not cfg.get("enabled"):
            return
        try:
            token = cfg.get("bot_token")
            chat_id = cfg.get("chat_id")
            if token and chat_id:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=5)
        except Exception:
            pass

    def _send_webhook(self, payload: Dict[str, Any]):
        cfg = self.config.get("webhook", {})
        if not cfg.get("enabled"):
            return
        try:
            url = cfg.get("url")
            if url:
                requests.post(url, json=payload, timeout=5)
        except Exception:
            pass
