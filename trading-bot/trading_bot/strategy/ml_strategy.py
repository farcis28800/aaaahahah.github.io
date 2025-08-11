from __future__ import annotations

import os
from typing import Optional

import numpy as np
import pandas as pd

from trading_bot.ml.nn import MLP
from trading_bot.data.market_data import compute_features
from trading_bot.strategy.base import Signal, Strategy


class MLStrategy(Strategy):
    name = "ml_strategy"

    def __init__(self, model_path: str, prob_long: float = 0.55, prob_short: float = 0.45) -> None:
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        self.model_path = model_path
        self.model = MLP.load(model_path)
        self.prob_long = prob_long
        self.prob_short = prob_short

    def _last_features(self, df: pd.DataFrame) -> np.ndarray:
        f = compute_features(df.copy()).iloc[-1]
        x = np.array([
            f["close"], f["volume"], f["rsi"], f["macd"], f["macd_signal"], f["atr"], f["bb_high"], f["bb_low"],
        ], dtype=float)
        x[0] = x[0] / max(1e-8, df["close"].mean())
        x[1] = (x[1] - df["volume"].mean()) / (df["volume"].std() + 1e-8)
        return x.reshape(1, -1)

    def generate_signal(self, df: pd.DataFrame) -> Signal:
        if len(df) < 60:
            return Signal(side="flat")
        x = self._last_features(df)
        p, _ = self.model.forward(x)
        p = float(p.ravel()[0])
        last = df.iloc[-1]
        if p >= self.prob_long:
            stop = last["close"] - 2.0 * last["atr"]
            tp = last["close"] + 2.5 * last["atr"]
            return Signal(side="long", stop_price=float(stop), take_profit_price=float(tp))
        if p <= self.prob_short:
            stop = last["close"] + 2.0 * last["atr"]
            tp = last["close"] - 2.5 * last["atr"]
            return Signal(side="short", stop_price=float(stop), take_profit_price=float(tp))
        return Signal(side="flat")