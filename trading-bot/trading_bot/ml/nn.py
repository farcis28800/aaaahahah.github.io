from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np


@dataclass
class MLPConfig:
    input_dim: int
    hidden_dim: int = 64
    output_dim: int = 1
    lr: float = 1e-3
    l2: float = 1e-4


class MLP:
    def __init__(self, config: MLPConfig) -> None:
        self.cfg = config
        rng = np.random.default_rng(123)
        self.W1 = rng.normal(0, 0.05, size=(self.cfg.input_dim, self.cfg.hidden_dim))
        self.b1 = np.zeros((self.cfg.hidden_dim,))
        self.W2 = rng.normal(0, 0.05, size=(self.cfg.hidden_dim, self.cfg.output_dim))
        self.b2 = np.zeros((self.cfg.output_dim,))
        # adam
        self.m = {k: np.zeros_like(v) for k, v in self.params().items()}
        self.v = {k: np.zeros_like(v) for k, v in self.params().items()}
        self.t = 0

    def params(self) -> Dict[str, np.ndarray]:
        return {"W1": self.W1, "b1": self.b1, "W2": self.W2, "b2": self.b2}

    @staticmethod
    def relu(x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)

    @staticmethod
    def sigmoid(x: np.ndarray) -> np.ndarray:
        return 1 / (1 + np.exp(-x))

    def forward(self, X: np.ndarray) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        z1 = X @ self.W1 + self.b1
        h1 = self.relu(z1)
        z2 = h1 @ self.W2 + self.b2
        y = self.sigmoid(z2)
        cache = {"X": X, "z1": z1, "h1": h1, "z2": z2, "y": y}
        return y, cache

    @staticmethod
    def bce_loss(y_pred: np.ndarray, y_true: np.ndarray, eps: float = 1e-8) -> Tuple[float, np.ndarray]:
        y_pred = np.clip(y_pred, eps, 1 - eps)
        loss = -(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))
        return float(loss.mean()), (y_pred - y_true) / (y_pred * (1 - y_pred) * y_true.shape[0])

    def backward(self, cache: Dict[str, np.ndarray], grad_out: np.ndarray) -> Dict[str, np.ndarray]:
        h1 = cache["h1"]
        X = cache["X"]
        dW2 = h1.T @ grad_out
        db2 = grad_out.sum(axis=0)
        dh1 = grad_out @ self.W2.T
        dz1 = dh1 * (cache["z1"] > 0)
        dW1 = X.T @ dz1
        db1 = dz1.sum(axis=0)
        # L2
        dW2 += self.cfg.l2 * self.W2
        dW1 += self.cfg.l2 * self.W1
        return {"W1": dW1, "b1": db1, "W2": dW2, "b2": db2}

    def step_adam(self, grads: Dict[str, np.ndarray], beta1: float = 0.9, beta2: float = 0.999, eps: float = 1e-8) -> None:
        self.t += 1
        lr_t = self.cfg.lr * (np.sqrt(1 - beta2 ** self.t) / (1 - beta1 ** self.t))
        for k, p in self.params().items():
            g = grads[k]
            self.m[k] = beta1 * self.m[k] + (1 - beta1) * g
            self.v[k] = beta2 * self.v[k] + (1 - beta2) * (g * g)
            p -= lr_t * self.m[k] / (np.sqrt(self.v[k]) + eps)

    def save(self, path: str) -> None:
        np.savez_compressed(path, W1=self.W1, b1=self.b1, W2=self.W2, b2=self.b2, meta=np.array([self.cfg.input_dim, self.cfg.hidden_dim, self.cfg.output_dim]))

    @staticmethod
    def load(path: str) -> "MLP":
        data = np.load(path, allow_pickle=True)
        input_dim, hidden_dim, output_dim = data["meta"]
        cfg = MLPConfig(int(input_dim), int(hidden_dim), int(output_dim))
        mlp = MLP(cfg)
        mlp.W1 = data["W1"]
        mlp.b1 = data["b1"]
        mlp.W2 = data["W2"]
        mlp.b2 = data["b2"]
        return mlp