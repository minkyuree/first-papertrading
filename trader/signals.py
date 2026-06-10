import pandas as pd
from trader.config import (
    BREAKOUT_WINDOW, VOLUME_MULT, ATR_WINDOW, ATR_MULT,
    MIN_ATR_PCT, MIN_PRICE, MIN_DOLLAR_VOL,
)


def scan_buy_signals(indicators, market_ok):
    if not market_ok:
        print("⛔ 시장 필터 차단 — 신호 스캔 생략")
        return []

    signals = []
    for ticker, df in indicators.items():
        row     = df.iloc[-1]
        hc_col  = f"highest_close_{BREAKOUT_WINDOW}"
        vol_col = f"vol_ma_{BREAKOUT_WINDOW}"
        atr_col = f"atr_{ATR_WINDOW}"

        if any(pd.isna(row.get(c, float("nan"))) for c in [hc_col, vol_col, atr_col, "atr_pct"]):
            continue
        if row["close"]  <= row[hc_col]:
            continue
        if row["volume"] < row[vol_col] * VOLUME_MULT:
            continue
        if row["atr_pct"] < MIN_ATR_PCT:
            continue
        if row["close"] < MIN_PRICE:
            continue
        if row["close"] * row["volume"] < MIN_DOLLAR_VOL:
            continue

        signals.append({
            "ticker"      : ticker,
            "close"       : round(row["close"], 2),
            "highest_20d" : round(row[hc_col], 2),
            "breakout_pct": round((row["close"] / row[hc_col] - 1) * 100, 2),
            "volume"      : int(row["volume"]),
            "vol_ma"      : int(row[vol_col]),
            "atr"         : round(row[atr_col], 2),
            "atr_pct"     : round(row["atr_pct"] * 100, 2),
            "stop_price"  : round(row["close"] - ATR_MULT * row[atr_col], 2),
        })

    signals.sort(key=lambda x: x["breakout_pct"], reverse=True)
    print(f"📡 신호 발생 종목: {len(signals)}개")
    return signals
