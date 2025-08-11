from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class RiskState:
    starting_balance: float
    current_balance: float
    daily_pnl_pct: float = 0.0


class RiskManager:
    def __init__(self, risk_per_trade_pct: float, max_daily_loss_pct: float, leverage: int, max_concurrent_positions: int) -> None:
        self.risk_per_trade_pct = risk_per_trade_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.leverage = leverage
        self.max_concurrent_positions = max_concurrent_positions

    def can_open_new(self, open_positions: int, risk_state: RiskState) -> bool:
        if open_positions >= self.max_concurrent_positions:
            return False
        if risk_state.daily_pnl_pct <= -abs(self.max_daily_loss_pct):
            return False
        return True

    def position_size_usdt(self, balance_usdt: float) -> float:
        return balance_usdt * (self.risk_per_trade_pct / 100.0) * self.leverage

    def quantity_from_atr(self, symbol_price: float, atr: float, balance_usdt: float, step_round: callable) -> float:
        risk_capital = self.position_size_usdt(balance_usdt)
        if atr <= 0:
            return 0.0
        qty = risk_capital / (2.0 * atr)
        qty = qty / symbol_price  # convert notional to quantity
        qty = step_round(qty)
        return max(qty, 0.0)