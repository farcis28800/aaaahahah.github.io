from __future__ import annotations

import argparse

from trading_bot.backtest.backtester import backtest_single
from trading_bot.config import settings
from trading_bot.exchange.bybit_client import BybitClient
from trading_bot.strategy.mtf_momentum import MtfMomentumStrategy
from trading_bot.strategy.scalper import FastScalperStrategy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", type=str, default="BTCUSDT")
    parser.add_argument("--interval", type=str, default="5m")
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--strategy", type=str, default="mtf", choices=["mtf", "scalper"])
    args = parser.parse_args()

    client = BybitClient(testnet=settings.bybit_testnet)

    if args.strategy == "mtf":
        strat = MtfMomentumStrategy(higher_tf="1h")
    else:
        strat = FastScalperStrategy()

    limit = min(max(int(args.days * 24 * 12), 300), 1500)  # approx 5m bars
    result = backtest_single(client, args.symbol, args.interval, strat, limit=limit)

    print("Strategy:", strat.name)
    print("Symbol:", args.symbol, "Interval:", args.interval)
    print("Trades:", len(result.trades))
    print("Total return %:", f"{result.total_return_pct:.2f}")
    print("Win rate %:", f"{result.win_rate_pct:.2f}")
    print("Max DD %:", f"{result.max_drawdown_pct:.2f}")
    print("Sharpe:", f"{result.sharpe:.2f}")


if __name__ == "__main__":
    main()