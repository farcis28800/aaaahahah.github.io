from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from trading_bot.data.market_data import get_featured_klines
from trading_bot.exchange.binance_client import BinanceFuturesClient
from trading_bot.strategy.base import Signal, Strategy


@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    side: str
    entry_price: float
    exit_price: float
    pnl_pct: float


@dataclass
class BacktestResult:
    trades: List[Trade]
    total_return_pct: float
    win_rate_pct: float
    max_drawdown_pct: float
    sharpe: float


def max_drawdown(equity: pd.Series) -> float:
    roll_max = equity.cummax()
    drawdown = (equity - roll_max) / roll_max
    return drawdown.min() * 100.0


def sharpe_ratio(returns: pd.Series) -> float:
    if returns.std() == 0:
        return 0.0
    return (returns.mean() / returns.std()) * np.sqrt(252 * 24 * 12)  # rough for 5m


def backtest_single(
    client: BinanceFuturesClient,
    symbol: str,
    interval: str,
    strategy: Strategy,
    limit: int = 1500,
) -> BacktestResult:
    df = get_featured_klines(client, symbol, interval, limit)
    trades: List[Trade] = []

    position: str = "flat"
    entry_price = 0.0
    entry_time = None

    equity = [1.0]
    returns = []

    for i in range(50, len(df)):
        window = df.iloc[: i + 1]
        sig: Signal
        if hasattr(strategy, "generate_signal"):
            sig = strategy.generate_signal(window)  # type: ignore[assignment]
        else:
            raise ValueError("Strategy missing generate_signal")

        price = float(window.iloc[-1]["close"])
        atr = float(window.iloc[-1]["atr"])

        if position == "flat":
            if sig.side in ("long", "short"):
                position = sig.side
                entry_price = price
                entry_time = window.index[-1]
        else:
            # exit by stop or tp
            if position == "long":
                stop = sig.stop_price or (entry_price - 2.0 * atr)
                tp = sig.take_profit_price or (entry_price + 2.0 * atr)
                if price <= stop or price >= tp:
                    pnl = (price - entry_price) / entry_price
                    trades.append(Trade(entry_time, window.index[-1], position, entry_price, price, pnl * 100))
                    equity.append(equity[-1] * (1 + pnl))
                    returns.append(pnl)
                    position = "flat"
            elif position == "short":
                stop = sig.stop_price or (entry_price + 2.0 * atr)
                tp = sig.take_profit_price or (entry_price - 2.0 * atr)
                if price >= stop or price <= tp:
                    pnl = (entry_price - price) / entry_price
                    trades.append(Trade(entry_time, window.index[-1], position, entry_price, price, pnl * 100))
                    equity.append(equity[-1] * (1 + pnl))
                    returns.append(pnl)
                    position = "flat"

    if len(equity) == 1:
        equity = [1.0, 1.0]
    equity_series = pd.Series(equity)
    rets = pd.Series(returns) if returns else pd.Series([0.0])

    total_return_pct = (equity_series.iloc[-1] - 1.0) * 100.0
    wins = sum(1 for t in trades if t.pnl_pct > 0)
    win_rate_pct = (wins / len(trades) * 100.0) if trades else 0.0
    mdd = float(max_drawdown(equity_series))
    shrp = float(sharpe_ratio(rets))

    return BacktestResult(trades, float(total_return_pct), float(win_rate_pct), mdd, shrp)