"""
Alternative data sources when yfinance is rate limited.
- Indices: ETF proxies (SPY, QQQ, DIA, IWM) via akshare
- Crypto: CoinGecko (free, no API key)
- Forex: akshare forex_spot_em
- Commodities: akshare futures_foreign_hist (if available)
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Index -> ETF proxy (US stocks, akshare works)
INDEX_ETF_PROXY = {
    "^GSPC": ("SPY", "S&P 500"),
    "^IXIC": ("QQQ", "NASDAQ"),
    "^DJI": ("DIA", "Dow Jones"),
    "^RUT": ("IWM", "Russell 2000"),
    "^FTSE": ("EWU", "FTSE 100"),
    "^N225": ("EWJ", "Nikkei 225"),
}

# CoinGecko coin IDs
COINGECKO_IDS = {
    "BTC-USD": "bitcoin",
    "ETH-USD": "ethereum",
    "SOL-USD": "solana",
    "BNB-USD": "binancecoin",
    "XRP-USD": "ripple",
    "ADA-USD": "cardano",
}

# Yahoo forex symbol -> akshare forex_spot_em code (from 代码 column)
FOREX_AKSHARE_MAP = {
    "EURUSD=X": "EURUSD",
    "GBPUSD=X": "GBPUSD",
    "USDJPY=X": "USDJPY",
    "AUDUSD=X": "AUDUSD",
    "USDCAD=X": "USDCAD",
    "USDCHF=X": "USDCHF",
}

# Yahoo commodity -> (akshare symbol code, display name, name substring to match in df)
COMMODITY_AKSHARE_MAP = {
    "GC=F": ("GC", "Gold", "COMEX黄金"),
    "SI=F": ("SI", "Silver", "COMEX白银"),
    "CL=F": ("CL", "Crude Oil WTI", "NYMEX原油"),
    "BZ=F": ("OIL", "Brent Crude", "布伦特"),
    "NG=F": ("NG", "Natural Gas", "NYMEX天然气"),
    "HG=F": ("HG", "Copper", "COMEX铜"),
    "PL=F": ("XPT", "Platinum", "伦敦铂金"),
}


def fetch_indices_via_etf() -> list[dict]:
    """Fetch index data via ETF proxies (SPY, QQQ, etc.) using akshare."""
    try:
        from services.data_sources import fetch_price_ak, _is_us_stock_symbol
    except ImportError:
        from data_sources import fetch_price_ak, _is_us_stock_symbol

    results = []
    for yf_symbol, (etf, name) in INDEX_ETF_PROXY.items():
        p = fetch_price_ak(etf)
        if p and p.get("price") and p.get("prev_close"):
            change = p["price"] - p["prev_close"]
            change_pct = (change / p["prev_close"] * 100) if p["prev_close"] else 0
            results.append({
                "name": name,
                "ticker": yf_symbol,
                "price": round(p["price"], 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
            })
    return results


def fetch_crypto_coingecko() -> list[dict]:
    """Fetch crypto prices via CoinGecko (free, no API key)."""
    import urllib.request
    import json

    ids = ",".join(COINGECKO_IDS.values())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        logger.warning(f"CoinGecko fetch failed: {e}")
        return []

    results = []
    id_to_ticker = {v: k for k, v in COINGECKO_IDS.items()}
    ticker_names = {
        "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana",
        "BNB-USD": "BNB", "XRP-USD": "XRP", "ADA-USD": "Cardano",
    }
    for cg_id, ticker in id_to_ticker.items():
        d = data.get(cg_id, {})
        price = d.get("usd")
        change_pct = d.get("usd_24h_change")
        if price is not None:
            results.append({
                "ticker": ticker,
                "name": ticker_names.get(ticker, ticker),
                "price": round(float(price), 2),
                "change_pct": round(float(change_pct or 0), 2),
            })
    return results


def fetch_forex_akshare() -> list[dict]:
    """Fetch forex via akshare forex_spot_em."""
    try:
        import akshare as ak
    except ImportError:
        return []

    try:
        df = ak.forex_spot_em()
        if df is None or df.empty:
            return []
        # Columns: 序号, 代码, 名称, 最新价, 涨跌额, 涨跌幅, 今开, 最高, 最低, 昨收
        col_code = "代码" if "代码" in df.columns else df.columns[1]
        col_price = "最新价" if "最新价" in df.columns else df.columns[3]
        col_pct = "涨跌幅" if "涨跌幅" in df.columns else df.columns[5]

        results = []
        name_map = {
            "EURUSD=X": "EUR/USD", "GBPUSD=X": "GBP/USD", "USDJPY=X": "USD/JPY",
            "AUDUSD=X": "AUD/USD", "USDCAD=X": "USD/CAD", "USDCHF=X": "USD/CHF",
        }
        for yf_sym, ak_code in FOREX_AKSHARE_MAP.items():
            row = df[df[col_code].astype(str).str.upper() == ak_code.upper()]
            if not row.empty:
                price = float(row[col_price].iloc[0])
                change_pct = float(row[col_pct].iloc[0]) if col_pct in row.columns else 0
                results.append({
                    "ticker": yf_sym,
                    "name": name_map.get(yf_sym, yf_sym),
                    "price": round(price, 4),
                    "change_pct": round(change_pct, 2),
                })
        return results
    except Exception as e:
        logger.warning(f"akshare forex fetch failed: {e}")
        return []


def fetch_commodities_akshare() -> list[dict]:
    """Fetch commodity prices via akshare futures_foreign_commodity_realtime."""
    try:
        import akshare as ak
    except ImportError:
        return []

    try:
        symbols_str = ",".join(v[0] for v in COMMODITY_AKSHARE_MAP.values())
        df = ak.futures_foreign_commodity_realtime(symbol=symbols_str)
        if df is None or df.empty:
            return []

        col_name = "名称" if "名称" in df.columns else df.columns[0]
        col_price = "最新价" if "最新价" in df.columns else df.columns[1]
        col_pct = "涨跌幅" if "涨跌幅" in df.columns else df.columns[4]

        results = []
        for yf_sym, (_, display_name, match_sub) in COMMODITY_AKSHARE_MAP.items():
            row = df[df[col_name].astype(str).str.contains(match_sub, na=False)]
            if not row.empty:
                price = float(row[col_price].iloc[0])
                change_pct = float(row[col_pct].iloc[0]) if col_pct in row.columns else 0
                results.append({
                    "ticker": yf_sym,
                    "name": display_name,
                    "price": round(price, 2),
                    "change_pct": round(change_pct, 2),
                })
        return results
    except Exception as e:
        logger.warning(f"akshare commodities fetch failed: {e}")
        return []
