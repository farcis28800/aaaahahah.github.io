from __future__ import annotations

from typing import Dict, List

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import AverageTrueRange, BollingerBands

from trading_bot.exchange.binance_client import BinanceFuturesClient


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["rsi"] = RSIIndicator(close=df["close"], window=14).rsi()
    macd = MACD(close=df["close"], window_slow=26, window_fast=12, window_sign=9)
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    atr = AverageTrueRange(high=df["high"], low=df["low"], close=df["close"], window=14)
    df["atr"] = atr.average_true_range()
    bb = BollingerBands(close=df["close"], window=20, window_dev=2)
    df["bb_high"] = bb.bollinger_hband()
    df["bb_low"] = bb.bollinger_lband()
    df.dropna(inplace=True)
    return df


def get_featured_klines(client: BinanceFuturesClient, symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
    df = client.get_klines(symbol, interval, limit)
    return compute_features(df)


def get_multi_timeframe_data(
    client: BinanceFuturesClient,
    symbol: str,
    intervals: List[str],
    limit: int = 500,
) -> Dict[str, pd.DataFrame]:
    result: Dict[str, pd.DataFrame] = {}
    for iv in intervals:
        result[iv] = get_featured_klines(client, symbol, iv, limit)
    return result