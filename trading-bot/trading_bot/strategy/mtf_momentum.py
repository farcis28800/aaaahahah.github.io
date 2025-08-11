from __future__ import annotations

from typing import Dict

import pandas as pd

from trading_bot.strategy.base import Signal, Strategy


class MtfMomentumStrategy(Strategy):
    name = "mtf_momentum"

    def __init__(self, higher_tf: str = "1h") -> None:
        self.higher_tf = higher_tf

    def generate_signal_mtf(self, data: Dict[str, pd.DataFrame]) -> Signal:
        if self.higher_tf not in data:
            return Signal(side="flat")
        higher = data[self.higher_tf]
        base_iv = sorted(data.keys(), key=lambda x: (len(x), x))[0]
        base = data[base_iv]

        if len(higher) < 50 or len(base) < 50:
            return Signal(side="flat")

        h = higher.iloc[-1]
        b = base.iloc[-1]

        up_trend = h["macd"] > h["macd_signal"] and h["rsi"] > 55
        down_trend = h["macd"] < h["macd_signal"] and h["rsi"] < 45

        long_entry = up_trend and b["macd"] > b["macd_signal"] and b["rsi"] > 55 and b["close"] > b["bb_high"]
        short_entry = down_trend and b["macd"] < b["macd_signal"] and b["rsi"] < 45 and b["close"] < b["bb_low"]

        if long_entry:
            stop = b["close"] - 2.5 * b["atr"]
            tp = b["close"] + 3.5 * b["atr"]
            return Signal(side="long", stop_price=float(stop), take_profit_price=float(tp))
        if short_entry:
            stop = b["close"] + 2.5 * b["atr"]
            tp = b["close"] - 3.5 * b["atr"]
            return Signal(side="short", stop_price=float(stop), take_profit_price=float(tp))

        return Signal(side="flat")