from __future__ import annotations

import math
from typing import Any, Dict, Optional

import pandas as pd
import requests


INTERVALS = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "2h": "2h",
    "4h": "4h",
    "6h": "6h",
    "8h": "8h",
    "12h": "12h",
    "1d": "1d",
}


class BinanceFuturesClient:
    def __init__(
        self,
        api_key: Optional[str],
        api_secret: Optional[str],
        testnet: bool = True,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.base_url = "https://testnet.binancefuture.com" if testnet else "https://fapi.binance.com"
        self._exchange_info: Optional[Dict[str, Any]] = None

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/fapi/v1{path}"
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_exchange_info(self) -> Dict[str, Any]:
        if self._exchange_info is None:
            self._exchange_info = self._get("/exchangeInfo")
        return self._exchange_info

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        info = self.get_exchange_info()
        for s in info.get("symbols", []):
            if s.get("symbol") == symbol:
                return s
        raise ValueError(f"Symbol not found in exchange info: {symbol}")

    def _step_size(self, symbol: str) -> float:
        s = self.get_symbol_info(symbol)
        for f in s.get("filters", []):
            if f.get("filterType") == "LOT_SIZE":
                return float(f.get("stepSize", 0.001))
        return 0.001

    def _tick_size(self, symbol: str) -> float:
        s = self.get_symbol_info(symbol)
        for f in s.get("filters", []):
            if f.get("filterType") == "PRICE_FILTER":
                return float(f.get("tickSize", 0.01))
        return 0.01

    def round_qty(self, symbol: str, quantity: float) -> float:
        step = self._step_size(symbol)
        if step <= 0:
            return quantity
        return math.floor(quantity / step) * step

    def round_price(self, symbol: str, price: float) -> float:
        tick = self._tick_size(symbol)
        if tick <= 0:
            return price
        return round(math.floor(price / tick) * tick, 8)

    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
        if interval not in INTERVALS:
            raise ValueError(f"Unsupported interval: {interval}")
        data = self._get("/klines", {"symbol": symbol, "interval": INTERVALS[interval], "limit": min(limit, 1500)})
        cols = [
            "open_time","open","high","low","close","volume","close_time","quote_asset_volume",
            "number_of_trades","taker_buy_base_asset_volume","taker_buy_quote_asset_volume","ignore"
        ]
        df = pd.DataFrame(data, columns=cols)
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
        for col in ["open","high","low","close","volume"]:
            df[col] = df[col].astype(float)
        df.set_index("close_time", inplace=True)
        return df[["open","high","low","close","volume"]]

    def get_price(self, symbol: str) -> float:
        ticker = self._get("/ticker/price", {"symbol": symbol})
        return float(ticker["price"])  # type: ignore[index]

    def get_balance(self) -> float:
        # Not available via public REST without key/signature. For paper we return a fixed balance.
        return 1000.0

    def set_leverage(self, symbol: str, leverage: int) -> None:
        # Requires signed POST; noop in paper/backtest
        return None

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "MARKET",
        reduce_only: bool = False,
    ) -> Dict[str, Any]:
        # For safety in this template, live trading is not implemented.
        raise NotImplementedError("Live trading via REST signed endpoints is not implemented in this template.")

    def set_stop_loss_take_profit(
        self,
        symbol: str,
        stop_price: Optional[float],
        take_profit_price: Optional[float],
        position_side: Optional[str] = None,
    ) -> None:
        # Not implemented in paper template
        return None