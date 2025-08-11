from __future__ import annotations

import os
import requests


def send_message(token: str | None, chat_id: str | None, text: str) -> None:
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, data=data, timeout=5)
    except Exception:
        pass