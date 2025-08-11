from __future__ import annotations

import pandas as pd

from trading_bot.strategy.base import Signal, Strategy


class FastScalperStrategy(Strategy):
    name = "fast_scalper"

    def __init__(self) -> None:
        pass

    def generate_signal(self, df: pd.DataFrame) -> Signal:
        if len(df) < 50:
            return Signal(side="flat")
        last = df.iloc[-1]
        prev = df.iloc[-2]

        breakout_up = last["close"] > last["bb_high"] and last["rsi"] > 60 and last["macd"] > last["macd_signal"]
        breakout_dn = last["close"] < last["bb_low"] and last["rsi"] < 40 and last["macd"] < last["macd_signal"]

        if breakout_up and last["close"] > prev["close"]:
            stop = last["close"] - 1.8 * last["atr"]
            tp = last["close"] + 2.2 * last["atr"]
            return Signal(side="long", stop_price=float(stop), take_profit_price=float(tp))
        if breakout_dn and last["close"] < prev["close"]:
            stop = last["close"] + 1.8 * last["atr"]
            tp = last["close"] - 2.2 * last["atr"]
            return Signal(side="short", stop_price=float(stop), take_profit_price=float(tp))

        return Signal(side="flat")