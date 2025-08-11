from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class Signal:
    side: str  # 'long', 'short', 'flat'
    stop_price: Optional[float] = None
    take_profit_price: Optional[float] = None


class Strategy:
    name: str = "base"

    def generate_signal(self, df: pd.DataFrame) -> Signal:
        raise NotImplementedError