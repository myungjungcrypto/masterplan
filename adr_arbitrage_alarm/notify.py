"""텔레그램 알림 — 토큰 미설정 시 stdout 출력으로 폴백."""
import logging

import requests

log = logging.getLogger("notify")


class Notifier:
    def __init__(self, cfg):
        self.token = cfg.telegram_bot_token
        self.chat_id = cfg.telegram_chat_id

    def send(self, text: str) -> None:
        if not self.token or not self.chat_id:
            print(f"\n=== ALERT (telegram 미설정) ===\n{text}\n", flush=True)
            return
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={"chat_id": self.chat_id, "text": text},
                timeout=10)
            r.raise_for_status()
        except Exception as e:
            log.error("telegram send failed: %s", e)
