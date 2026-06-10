import os

# ── Alpaca ───────────────────────────────────────────────────
ALPACA_API_KEY    = os.environ["ALPACA_API_KEY"]
ALPACA_API_SECRET = os.environ["ALPACA_API_SECRET"]
ALPACA_PAPER      = True   # False로 바꾸면 실계좌

# ── Telegram ─────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# ── 유니버스 ─────────────────────────────────────────────────
TICKERS = [
    "AAPL", "MSFT", "NVDA", "META", "GOOGL", "AMZN", "TSLA",
    "AMD",  "AVGO", "QCOM", "AMAT", "LRCX",  "KLAC", "MRVL", "TXN",
    "INTC", "MU",   "SNPS", "CDNS", "ADBE",  "CRM",  "NOW",  "INTU",
    "ORCL", "PANW", "CRWD", "FTNT", "SNOW",  "PLTR", "APP",  "UBER",
    "ABNB", "UNH",  "LLY",  "JNJ",  "ABBV",  "MRK",  "TMO",  "ABT",
    "ISRG", "REGN", "VRTX", "AMGN", "JPM",   "BAC",  "GS",   "MS",
    "BLK",  "V",    "MA",   "AXP",  "HD",    "LOW",  "TJX",  "BKNG",
    "MCD",  "SBUX", "NKE",  "LULU", "WMT",   "COST", "PG",   "KO",
    "XOM",  "CVX",  "COP",  "CAT",  "DE",    "HON",  "LMT",  "RTX",
    "GE",   "NEE",  "NFLX", "DIS",  "CMCSA", "TMUS",
]
TICKERS = list(dict.fromkeys(TICKERS))

# ── 전략 파라미터 ─────────────────────────────────────────────
BREAKOUT_WINDOW   = 20
VOLUME_MULT       = 1.5
ATR_WINDOW        = 14
ATR_MULT          = 2.5
MIN_ATR_PCT       = 0.01
SPY_MA_WINDOW     = 200
VIX_THRESHOLD     = 25.0
POSITION_SIZE_PCT = 0.10
MAX_POSITIONS     = 10
MIN_PRICE         = 10.0
MIN_DOLLAR_VOL    = 50_000_000
LOOKBACK_DAYS     = 250
