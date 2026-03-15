"""
Fallback dummy data so every screen always shows something when real data fails.
"""
from datetime import datetime, timedelta

# Dashboard indices (sample prices)
DUMMY_INDICES = [
    {"name": "S&P 500", "ticker": "^GSPC", "price": 5820.0, "change": 12.5, "change_pct": 0.22},
    {"name": "Dow Jones", "ticker": "^DJI", "price": 45200.0, "change": -45.0, "change_pct": -0.10},
    {"name": "NASDAQ", "ticker": "^IXIC", "price": 18250.0, "change": 85.0, "change_pct": 0.47},
    {"name": "Russell 2000", "ticker": "^RUT", "price": 2150.0, "change": 5.0, "change_pct": 0.23},
]

# Gainers / losers
DUMMY_GAINERS = [
    {"ticker": "NVDA", "name": "NVIDIA", "price": 142.50, "change_pct": 2.45},
    {"ticker": "AAPL", "name": "Apple", "price": 228.30, "change_pct": 1.82},
    {"ticker": "META", "name": "Meta", "price": 585.20, "change_pct": 1.55},
]

DUMMY_LOSERS = [
    {"ticker": "TSLA", "name": "Tesla", "price": 245.00, "change_pct": -0.95},
    {"ticker": "AMD", "name": "AMD", "price": 128.40, "change_pct": -0.72},
]

# Sectors
DUMMY_SECTORS = [
    {"name": "Technology", "change_pct": 0.85},
    {"name": "Financials", "change_pct": 0.32},
    {"name": "Healthcare", "change_pct": 0.18},
]

# Crypto
DUMMY_CRYPTO = [
    {"ticker": "BTC-USD", "name": "Bitcoin", "price": 98000.0, "change_pct": 0.5},
    {"ticker": "ETH-USD", "name": "Ethereum", "price": 3650.0, "change_pct": -0.2},
]

# Commodities
DUMMY_COMMODITIES = [
    {"ticker": "GC=F", "name": "Gold", "price": 2650.0, "change_pct": 0.15},
    {"ticker": "CL=F", "name": "Crude Oil", "price": 78.50, "change_pct": -0.3},
]

# Forex
DUMMY_FOREX = [
    {"ticker": "EURUSD=X", "name": "EUR/USD", "price": 1.0850, "change_pct": 0.05},
    {"ticker": "USDJPY=X", "name": "USD/JPY", "price": 149.50, "change_pct": -0.12},
]


def get_dummy_ownership(ticker: str) -> dict:
    return {
        "ticker": ticker.upper(),
        "shares_outstanding": 15_000_000_000,
        "insiders_pct": 0.08,
        "institutions_pct": 61.5,
        "institutions_float_pct": 59.2,
        "institutions_count": 3421,
        "institutional_holders": [
            {"holder": "Vanguard Group", "pct_held": 8.2, "shares": 1_320_000_000, "value": 300_000_000_000, "pct_change": 0.1, "date_reported": "2024-09-30"},
            {"holder": "BlackRock", "pct_held": 6.5, "shares": 1_050_000_000, "value": 240_000_000_000, "pct_change": -0.2, "date_reported": "2024-09-30"},
        ],
    }


def get_dummy_debt(ticker: str) -> dict:
    return {
        "ticker": ticker.upper(),
        "fiscal_year": "2024-FY",
        "items": [
            {"label": "Total Debt", "value": 95_000_000_000},
            {"label": "Current Debt (Due < 1yr)", "value": 10_000_000_000},
            {"label": "Long-Term Debt", "value": 85_000_000_000},
            {"label": "Total Liabilities", "value": 290_000_000_000},
            {"label": "Current Liabilities", "value": 125_000_000_000},
            {"label": "Non-Current Liabilities", "value": 165_000_000_000},
            {"label": "Total Assets", "value": 350_000_000_000},
            {"label": "Shareholders' Equity", "value": 60_000_000_000},
            {"label": "Debt / Equity Ratio", "value": 158.3},
            {"label": "Debt / Assets Ratio", "value": 27.1},
            {"label": "Liabilities / Assets", "value": 82.9},
        ],
    }


def get_dummy_insider_transactions(ticker: str) -> dict:
    return {
        "ticker": ticker.upper(),
        "transactions": 3,
        "buys": 1,
        "sells": 2,
        "insider_transactions": [
            {"insider_name": "CEO", "title": "CEO", "trans_date": "2024-09-15", "shares": -50000, "price": 225.0, "value": 11_250_000},
            {"insider_name": "CFO", "title": "CFO", "trans_date": "2024-09-10", "shares": 10000, "price": 220.0, "value": 2_200_000},
        ],
    }


def get_dummy_news(ticker: str) -> list[dict]:
    return [
        {"title": "Market Update", "publisher": "Reuters", "link": "#", "published": datetime.now().isoformat()},
        {"title": "Earnings Preview", "publisher": "Bloomberg", "link": "#", "published": (datetime.now() - timedelta(days=1)).isoformat()},
    ]


def get_dummy_candles(ticker: str, days: int = 252) -> list[dict]:
    """Generate dummy OHLCV for chart."""
    base = 100.0
    now = datetime.now()
    out = []
    for i in range(days):
        d = now - timedelta(days=days - i)
        open_p = base
        change = (i % 5 - 2) * 0.5
        close = base * (1 + change / 100)
        high = max(open_p, close) * 1.01
        low = min(open_p, close) * 0.99
        base = close
        out.append({
            "time": d.strftime("%Y-%m-%d"),
            "open": round(open_p, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(close, 2),
            "volume": 50_000_000 + (i % 10) * 5_000_000,
        })
    return out
