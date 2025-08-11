from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd

from trading_bot.data.market_data import compute_features


def build_dataset(df: pd.DataFrame, horizon: int = 12, up_thresh: float = 0.003, down_thresh: float = -0.003) -> Tuple[np.ndarray, np.ndarray, list[str]]:
    df = compute_features(df)
    df["ret_fwd"] = df["close"].pct_change(periods=horizon).shift(-horizon)
    # Binary label: 1 if ret >= up_thresh, 0 if ret <= down_thresh; drop neutral
    mask = (df["ret_fwd"] >= up_thresh) | (df["ret_fwd"] <= down_thresh)
    df = df.loc[mask].dropna()
    features = [
        "close","volume","rsi","macd","macd_signal","atr","bb_high","bb_low",
    ]
    X = df[features].values.astype(float)
    # scale roughly
    X[:, 0] = X[:, 0] / X[:, 0].mean()
    X[:, 1] = (X[:, 1] - X[:, 1].mean()) / (X[:, 1].std() + 1e-8)
    y = (df["ret_fwd"] >= up_thresh).astype(float).values.reshape(-1, 1)
    return X, y, features