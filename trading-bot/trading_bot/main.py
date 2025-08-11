from __future__ import annotations

import time
from datetime import datetime
from typing import Dict

from trading_bot.config import settings
from trading_bot.data.market_data import get_featured_klines, get_multi_timeframe_data
from trading_bot.exchange.binance_client import BinanceFuturesClient
from trading_bot.risk.manager import RiskManager, RiskState
from trading_bot.strategy.mtf_momentum import MtfMomentumStrategy
from trading_bot.strategy.scalper import FastScalperStrategy
from trading_bot.telegram.notify import send_message


def run() -> None:
    client = BinanceFuturesClient(settings.binance_api_key, settings.binance_api_secret, testnet=settings.binance_testnet)
    risk = RiskManager(
        risk_per_trade_pct=settings.risk.risk_per_trade_pct,
        max_daily_loss_pct=settings.risk.max_daily_loss_pct,
        leverage=settings.risk.leverage,
        max_concurrent_positions=settings.risk.max_concurrent_positions,
    )

    mtf = MtfMomentumStrategy(higher_tf="1h")
    scalper = FastScalperStrategy()

    open_positions: Dict[str, str] = {}

    print("Starting live loop (paper_trading=%s, testnet=%s)" % (not settings.live_trading, settings.binance_testnet))

    while True:
        try:
            balance = client.get_balance() if settings.live_trading else 1000.0
            risk_state = RiskState(starting_balance=1000.0, current_balance=balance)

            for symbol in settings.symbols:
                try:
                    data = get_multi_timeframe_data(client, symbol, [settings.base_interval, "1h"])  # base + higher
                    base_df = data[settings.base_interval]
                    mtf_signal = mtf.generate_signal_mtf(data)
                    scalp_signal = scalper.generate_signal(base_df)

                    final_signal = mtf_signal if mtf_signal.side != "flat" else scalp_signal

                    price = float(base_df.iloc[-1]["close"]) if len(base_df) else client.get_price(symbol)
                    atr = float(base_df.iloc[-1]["atr"]) if len(base_df) else price * 0.01

                    can_open = risk.can_open_new(len(open_positions), risk_state)

                    if symbol not in open_positions and final_signal.side in ("long", "short") and can_open:
                        qty = risk.quantity_from_atr(price, atr, balance, lambda q: client.round_qty(symbol, q))
                        if qty <= 0:
                            continue

                        text = f"Signal {final_signal.side.upper()} {symbol} price={price:.2f} qty={qty:.6f}"
                        print(text)
                        send_message(settings.telegram_bot_token, settings.telegram_chat_id, text)

                        if settings.live_trading:
                            client.set_leverage(symbol, settings.risk.leverage)
                            client.place_order(symbol, side="BUY" if final_signal.side == "long" else "SELL", quantity=qty)
                        open_positions[symbol] = final_signal.side

                    elif symbol in open_positions:
                        # simplistic flat when opposite signal appears
                        if final_signal.side == "flat" or final_signal.side != open_positions[symbol]:
                            text = f"Exit {symbol} by opposite/flat signal"
                            print(text)
                            send_message(settings.telegram_bot_token, settings.telegram_chat_id, text)
                            if settings.live_trading:
                                side = "SELL" if open_positions[symbol] == "long" else "BUY"
                                client.place_order(symbol, side=side, quantity=0.0, reduce_only=True)  # reduce only market close
                            del open_positions[symbol]

                except Exception as sym_e:
                    print(f"Error processing {symbol}: {sym_e}")

            time.sleep(30)
        except KeyboardInterrupt:
            print("Stopped by user")
            break
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run()