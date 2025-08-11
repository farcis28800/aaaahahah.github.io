from __future__ import annotations

import os
from typing import List
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env if present
load_dotenv()


def _split_csv(value: str | None, default: List[str]) -> List[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


class RiskConfig(BaseModel):
    risk_per_trade_pct: float = float(os.getenv("RISK_PER_TRADE_PCT", 1.0))
    leverage: int = int(os.getenv("LEVERAGE", 5))
    max_concurrent_positions: int = int(os.getenv("MAX_CONCURRENT_POSITIONS", 2))
    max_daily_loss_pct: float = float(os.getenv("MAX_DAILY_LOSS_PCT", 5.0))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bybit_testnet: bool = os.getenv("BYBIT_TESTNET", "false").lower() == "true"

    symbols: List[str] = _split_csv(os.getenv("SYMBOLS"), ["BTCUSDT", "ETHUSDT"])
    timeframes: List[str] = _split_csv(os.getenv("TIMEFRAMES"), ["1m", "5m", "1h", "4h"])
    base_interval: str = os.getenv("BASE_INTERVAL", "5m")

    strategy: str = os.getenv("STRATEGY", "mtf")  # mtf|scalper|ml|ensemble
    model_path: str = os.getenv("MODEL_PATH", "models/nn_BTCUSDT_5m.npz")

    risk: RiskConfig = RiskConfig()

    telegram_bot_token: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = os.getenv("TELEGRAM_CHAT_ID")

    live_trading: bool = os.getenv("LIVE_TRADING", "false").lower() == "true"


settings = Settings()