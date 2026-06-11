import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from trader.config import (
    ALPACA_API_KEY, ALPACA_API_SECRET,
    TICKERS, BREAKOUT_WINDOW, ATR_WINDOW,
    SPY_MA_WINDOW, VIX_THRESHOLD, LOOKBACK_DAYS,
)

ET = ZoneInfo("America/New_York")
data_client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_API_SECRET)


def _fetch_bars(symbols, start, end):
    req = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
        adjustment="all",
        feed="iex", 
    )
    bars = data_client.get_stock_bars(req).df
    if bars.empty:
        return {}

    price_data = {}
    if isinstance(bars.index, pd.MultiIndex):
        for symbol in bars.index.get_level_values(0).unique():
            df = bars.xs(symbol, level=0).copy()
            df.index = pd.to_datetime(df.index).tz_localize(None) if df.index.tz else pd.to_datetime(df.index)
            df.columns = [c.lower() for c in df.columns]
            if len(df) >= 60:
                price_data[symbol] = df
    return price_data


def fetch_price_data(tickers=TICKERS, lookback_days=LOOKBACK_DAYS):
    end   = datetime.now(ET)
    start = end - timedelta(days=lookback_days)
    print(f"📥 Alpaca 데이터 다운로드 중... ({len(tickers)}개 종목)")

    BATCH = 50
    price_data = {}
    for i in range(0, len(tickers), BATCH):
        batch = tickers[i:i+BATCH]
        result = _fetch_bars(batch, start, end)
        price_data.update(result)

    failed = len(tickers) - len(price_data)
    print(f"✅ 성공: {len(price_data)}개 | ❌ 실패: {failed}개")
    return price_data


def compute_atr(df, window=ATR_WINDOW):
    high, low, prev_close = df["high"], df["low"], df["close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(span=window, min_periods=window, adjust=False).mean()


def compute_indicators(price_data):
    processed = {}
    for ticker, df in price_data.items():
        d = df.copy()
        d[f"highest_close_{BREAKOUT_WINDOW}"] = (
            d["close"].shift(1).rolling(BREAKOUT_WINDOW).max()
        )
        d[f"vol_ma_{BREAKOUT_WINDOW}"] = d["volume"].rolling(BREAKOUT_WINDOW).mean()
        d[f"atr_{ATR_WINDOW}"]         = compute_atr(d, ATR_WINDOW)
        d["atr_pct"]                   = d[f"atr_{ATR_WINDOW}"] / d["close"]
        d.dropna(inplace=True)
        if len(d) > 0:
            processed[ticker] = d
    print(f"✅ 지표 계산 완료 | {len(processed)}개 종목")
    return processed


def get_market_filter():
    end   = datetime.now(ET)
    start = end - timedelta(days=300)

    spy_data = _fetch_bars(["SPY"], start, end)

    if not spy_data:
        print("⚠️ SPY 데이터 없음 — 시장 필터 비활성화")
        return {"market_ok": True, "spy_price": 0, "spy_ma": 0, "vix": 0, "spy_ok": True, "vix_ok": True}

    spy_close = spy_data["SPY"]["close"]
    spy_ma    = spy_close.rolling(SPY_MA_WINDOW).mean()
    spy_ok    = bool(spy_close.iloc[-1] > spy_ma.iloc[-1])

    # ^VIX는 Alpaca 미지원 → VIXY ETF로 근사
    vix_data = _fetch_bars(["VIXY"], start, end)
    vix_val  = 0.0
    vix_ok   = True
    if vix_data and "VIXY" in vix_data:
        vix_close = vix_data["VIXY"]["close"]
        vix_val   = float(vix_close.iloc[-1])
        vix_ok    = vix_val < (VIX_THRESHOLD / 3)

    return {
        "market_ok" : spy_ok and vix_ok,
        "spy_price" : round(float(spy_close.iloc[-1]), 2),
        "spy_ma"    : round(float(spy_ma.iloc[-1]), 2),
        "vix"       : round(vix_val, 2),
        "spy_ok"    : spy_ok,
        "vix_ok"    : vix_ok,
    }
