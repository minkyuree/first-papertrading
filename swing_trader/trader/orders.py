import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus

from trader.config import (
    ALPACA_API_KEY, ALPACA_API_SECRET, ALPACA_PAPER,
    ATR_WINDOW, ATR_MULT, MAX_POSITIONS, POSITION_SIZE_PCT,
)

client = TradingClient(ALPACA_API_KEY, ALPACA_API_SECRET, paper=ALPACA_PAPER)


def get_account():
    return client.get_account()


def get_positions():
    positions = client.get_all_positions()
    if not positions:
        return pd.DataFrame()
    rows = []
    for p in positions:
        rows.append({
            "ticker"        : p.symbol,
            "shares"        : float(p.qty),
            "avg_cost"      : float(p.avg_entry_price),
            "current_price" : float(p.current_price),
            "market_value"  : float(p.market_value),
            "unrealized_pnl": float(p.unrealized_pl),
            "pnl_pct"       : float(p.unrealized_plpc) * 100,
        })
    return pd.DataFrame(rows)


def check_trailing_stops(indicators, positions_df):
    if positions_df.empty:
        return []

    exit_list = []
    for _, pos in positions_df.iterrows():
        ticker = pos["ticker"]
        if ticker not in indicators:
            continue

        row     = indicators[ticker].iloc[-1]
        atr_col = f"atr_{ATR_WINDOW}"
        if pd.isna(row.get(atr_col, float("nan"))):
            continue

        current_price = pos["current_price"]
        atr_val       = float(row[atr_col])
        peak_price    = max(pos["avg_cost"], current_price)
        stop_price    = peak_price - ATR_MULT * atr_val

        if current_price <= stop_price:
            exit_list.append({
                "ticker"      : ticker,
                "current_price": current_price,
                "stop_price"  : round(stop_price, 2),
                "pnl_pct"     : round(pos["pnl_pct"], 2),
            })

    return exit_list


def execute_sells(exit_list, dry_run=True):
    results = []
    for item in exit_list:
        ticker = item["ticker"]
        if dry_run:
            results.append({"ticker": ticker, "status": "DRY_RUN", "error": None})
            continue
        try:
            # 전량 청산: close_position 사용
            client.close_position(ticker)
            results.append({"ticker": ticker, "status": "OK", "error": None})
        except Exception as e:
            results.append({"ticker": ticker, "status": "FAIL", "error": str(e)})
    return results


def execute_buys(signals, positions_df, dry_run=True):
    account       = get_account()
    portfolio_val = float(account.portfolio_value)
    cash          = float(account.cash)
    held_tickers  = set(positions_df["ticker"].tolist()) if not positions_df.empty else set()
    n_positions   = len(held_tickers)

    results = []
    orders_placed = 0

    for sig in signals:
        if n_positions + orders_placed >= MAX_POSITIONS:
            break

        ticker   = sig["ticker"]
        notional = round(portfolio_val * POSITION_SIZE_PCT, 2)

        if ticker in held_tickers:
            continue
        if notional > cash:
            results.append({"ticker": ticker, "status": "SKIP_CASH", "notional": notional, "error": None})
            continue

        if dry_run:
            results.append({"ticker": ticker, "status": "DRY_RUN", "notional": notional, "error": None})
            orders_placed += 1
            continue

        try:
            order = client.submit_order(
                MarketOrderRequest(
                    symbol=ticker,
                    notional=notional,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY,
                )
            )
            cash -= notional
            orders_placed += 1
            results.append({"ticker": ticker, "status": "OK", "notional": notional, "error": None})
        except Exception as e:
            results.append({"ticker": ticker, "status": "FAIL", "notional": notional, "error": str(e)})

    return results, portfolio_val, cash
