from __future__ import annotations

import time
from typing import Dict, Optional

import requests

from trading_bot.config import settings
from trading_bot.exchange.bybit_client import BybitClient
from trading_bot.data.market_data import get_featured_klines
from trading_bot.strategy.mtf_momentum import MtfMomentumStrategy
from trading_bot.strategy.scalper import FastScalperStrategy


API = "https://api.telegram.org/bot{token}/{method}"


def send(chat_id: str, text: str, reply_markup: Optional[dict] = None) -> None:
    if not settings.telegram_bot_token or not chat_id:
        return
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = reply_markup
    requests.post(API.format(token=settings.telegram_bot_token, method="sendMessage"), json=data, timeout=5)


def keyboard() -> dict:
    return {
        "keyboard": [
            [{"text": "Fast Signal"}, {"text": "Set Strategy: mtf"}],
            [{"text": "Set Strategy: scalper"}, {"text": "Status"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def fast_signal() -> str:
    client = BybitClient(testnet=settings.bybit_testnet)
    mtf = MtfMomentumStrategy(higher_tf="1h")
    scalper = FastScalperStrategy()
    messages = []
    for symbol in settings.symbols:
        df = get_featured_klines(client, symbol, settings.base_interval, 400)
        s1 = mtf.generate_signal_mtf({settings.base_interval: df, "1h": get_featured_klines(client, symbol, "1h", 400)})
        s2 = scalper.generate_signal(df)
        pick = s1 if s1.side != "flat" else s2
        messages.append(f"{symbol}: {pick.side.upper()} stop={pick.stop_price:.2f} tp={pick.take_profit_price:.2f}" if pick.side != "flat" else f"{symbol}: FLAT")
    return "\n".join(messages)


def run_bot() -> None:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        print("Telegram token/chat_id not set")
        return
    offset = None
    send(settings.telegram_chat_id, "Bot started", keyboard())
    current_strategy = "mtf"
    while True:
        try:
            resp = requests.get(API.format(token=settings.telegram_bot_token, method="getUpdates"), params={"timeout": 30, "offset": offset}, timeout=35)
            data = resp.json()
            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message") or {}
                chat_id = str(msg.get("chat", {}).get("id"))
                text = (msg.get("text") or "").strip().lower()
                if not chat_id:
                    continue
                if text in ("/start", "start"):
                    send(chat_id, "Choose:", keyboard())
                elif text.startswith("set strategy"):
                    current_strategy = "scalper" if "scalper" in text else "mtf"
                    send(chat_id, f"Strategy set to {current_strategy}", keyboard())
                elif text == "fast signal":
                    send(chat_id, fast_signal(), keyboard())
                elif text == "status":
                    send(chat_id, f"Strategy: {current_strategy}\nSymbols: {', '.join(settings.symbols)}\nInterval: {settings.base_interval}", keyboard())
        except Exception as e:
            print("bot loop error:", e)
            time.sleep(2)


if __name__ == "__main__":
    run_bot()