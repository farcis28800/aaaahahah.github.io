from __future__ import annotations

import argparse

import numpy as np

from trading_bot.exchange.bybit_client import BybitClient
from trading_bot.data.market_data import get_featured_klines
from trading_bot.ml.dataset import build_dataset
from trading_bot.ml.nn import MLP, MLPConfig


def train(symbol: str, interval: str, epochs: int, model_out: str) -> None:
    client = BybitClient(testnet=False)
    df = get_featured_klines(client, symbol, interval, 1000)
    X, y, feats = build_dataset(df)
    cfg = MLPConfig(input_dim=X.shape[1], hidden_dim=64, output_dim=1, lr=1e-3, l2=1e-5)
    model = MLP(cfg)
    for ep in range(epochs):
        y_pred, cache = model.forward(X)
        loss, grad = model.bce_loss(y_pred, y)
        grads = model.backward(cache, grad)
        model.step_adam(grads)
        if (ep + 1) % max(1, epochs // 10) == 0:
            acc = float(((y_pred >= 0.5) == (y >= 0.5)).mean())
            print(f"epoch {ep+1}/{epochs} loss={loss:.4f} acc={acc:.3f}")
    model.save(model_out)
    print("saved:", model_out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--interval", default="5m")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--out", default="models/nn_BTCUSDT_5m.npz")
    args = ap.parse_args()
    train(args.symbol, args.interval, args.epochs, args.out)