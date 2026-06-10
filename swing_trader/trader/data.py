import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from trader.config import (
    TICKERS, BREAKOUT_WINDOW, VOLUME_MULT, ATR_WINDOW,
    SPY_MA_WINDOW, VIX_THRESHOLD, LOOKBACK_DAYS,
)

ET = ZoneInfo("America/New_York")


def fetch_price_data(tickers=TICKERS, lookback_days=LOOKBACK_DAYS):
    end   = datetime.now(ET)
    start = end - timedelta(days=lookback_days)
    print(f"📥 데이터 다운로드 중... ({len(tickers)}개 종목)")

    raw = yf.download(
        tickers,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
    )

    price_data, failed = {}, []
    for ticker in tickers:
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                df = raw.xs(ticker, axis=1, level=1).copy()
            else:
                df = raw.copy()
            df.index = df.index.tz_localize(None) if df.index.tz else df.index
            df.columns = [c.lower() for c in df.columns]
            df.dropna(subset=["close", "volume"], inplace=True)
            if len(df) < 60:
                failed.append(ticker)
                continue
            price_data[ticker] = df
        except Exception:
            failed.append(ticker)

    print(f"✅ 성공: {len(price_data)}개 | ❌ 실패: {len(failed)}개")
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
        processed[ticker] = d
    print(f"✅ 지표 계산 완료 | {len(processed)}개 종목")
    return processed


def get_market_filter():
    end   = datetime.now(ET)
    start = end - timedelta(days=300)

    spy = yf.download("SPY",  start=start, end=end, auto_adjust=True, progress=False)
    vix = yf.download("^VIX", start=start, end=end, auto_adjust=True, progress=False)

    spy_close = spy["Close"].squeeze()
    vix_close = vix["Close"].squeeze()
    spy_ma    = spy_close.rolling(SPY_MA_WINDOW).mean()

    spy_ok    = bool(spy_close.iloc[-1] > spy_ma.iloc[-1])
    vix_ok    = bool(vix_close.iloc[-1] < VIX_THRESHOLD)
    market_ok = spy_ok and vix_ok

    return {
        "market_ok" : market_ok,
        "spy_price" : round(float(spy_close.iloc[-1]), 2),
        "spy_ma"    : round(float(spy_ma.iloc[-1]), 2),
        "vix"       : round(float(vix_close.iloc[-1]), 2),
        "spy_ok"    : spy_ok,
        "vix_ok"    : vix_ok,
    }
