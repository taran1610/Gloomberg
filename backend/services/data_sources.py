"""
Data source helpers with yfinance primary and akshare fallback.
akshare is used when yfinance fails (JSONDecodeError, empty data, etc.).
"""
import logging
from typing import Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

_akshare_available = False
try:
    import akshare as ak
    _akshare_available = True
except ImportError:
    pass


def _is_us_stock_symbol(symbol: str) -> bool:
    """Heuristic: US stocks are typically 1-5 chars, no ^, =, or -USD. Allows BRK-B style."""
    s = symbol.upper()
    if s.startswith("^") or "=" in s or "=X" in s or "-USD" in s or "-USDT" in s:
        return False
    # Allow letters and single hyphen (e.g. BRK-B)
    clean = s.replace("-", "")
    return len(s) <= 6 and clean.isalpha() and len(clean) >= 2


def fetch_history_ak(symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
    """
    Fetch US stock history via akshare. Returns DataFrame with Open, High, Low, Close, Volume.
    stock_us_daily returns: date, open, high, low, close, volume (lowercase).
    """
    if not _akshare_available:
        return None
    try:
        from datetime import datetime, timedelta
        df = ak.stock_us_daily(symbol=symbol, adjust="")
        if df is None or df.empty or len(df) < 2:
            return None
        # akshare returns: date, open, high, low, close, volume
        df = df.rename(columns={
            "open": "Open", "high": "High", "low": "Low",
            "close": "Close", "volume": "Volume"
        })
        df = df.set_index(pd.to_datetime(df["date"])).drop(columns=["date"], errors="ignore")
        # Filter by period (stock_us_daily returns full history)
        end = datetime.now()
        if period == "5d":
            start = end - timedelta(days=5)
        elif period == "1mo":
            start = end - timedelta(days=30)
        elif period == "3mo":
            start = end - timedelta(days=90)
        elif period == "6mo":
            start = end - timedelta(days=180)
        elif period == "1y":
            start = end - timedelta(days=365)
        elif period == "2y":
            start = end - timedelta(days=730)
        elif period == "5y":
            start = end - timedelta(days=1825)
        else:
            start = end - timedelta(days=365)
        df = df[df.index >= pd.Timestamp(start)]
        if len(df) < 2:
            return None
        return df
    except Exception as e:
        logger.warning(f"akshare history fallback failed for {symbol}: {e}")
        return None


def fetch_asset_ak(symbol: str) -> Optional[dict]:
    """Build minimal asset dict from akshare for US stocks when yfinance fails.
    Returns {price, prev_close, name} or None."""
    if not _akshare_available or not _is_us_stock_symbol(symbol):
        return None
    try:
        p = fetch_price_ak(symbol)
        if not p:
            return None
        return {
            "price": p["price"],
            "prev_close": p["prev_close"],
            "name": symbol,
        }
    except Exception as e:
        logger.warning(f"akshare asset fallback failed for {symbol}: {e}")
        return None


def fetch_price_ak(symbol: str) -> Optional[dict]:
    """Fetch US stock price via akshare. Returns {price, prev_close} or None."""
    if not _akshare_available:
        return None
    try:
        df = ak.stock_us_daily(symbol=symbol, adjust="")
        if df is None or df.empty or len(df) < 1:
            return None
        # Get last row
        close_col = "close" if "close" in df.columns else "收盘"
        if close_col not in df.columns:
            close_col = df.columns[-2]  # often close is second to last
        if len(df) >= 2:
            price = float(df[close_col].iloc[-1])
            prev = float(df[close_col].iloc[-2])
        else:
            price = float(df[close_col].iloc[-1])
            prev = price
        return {"price": round(price, 2), "prev_close": round(prev, 2)}
    except Exception as e:
        logger.warning(f"akshare price fallback failed for {symbol}: {e}")
        return None


def fetch_history_yf(symbol: str, period: str = "1y", interval: str = "1d") -> Optional[pd.DataFrame]:
    """Fetch history via yfinance. Returns DataFrame or None."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        if hist.empty or len(hist) < 2:
            return None
        return hist
    except Exception as e:
        logger.warning(f"yfinance history failed for {symbol}: {e}")
        return None


def fetch_history_with_fallback(symbol: str, period: str = "1y", interval: str = "1d") -> list[dict]:
    """
    Fetch OHLCV history. For US stocks: try akshare first (avoids Yahoo rate limits).
    Returns list of {time, open, high, low, close, volume}.
    """
    hist = None
    if _is_us_stock_symbol(symbol) and _akshare_available:
        hist = fetch_history_ak(symbol, period)
    if hist is None:
        hist = fetch_history_yf(symbol, period, interval)
    if hist is None or hist.empty:
        return []
    records = []
    for date, row in hist.iterrows():
        try:
            records.append({
                "time": date.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row.get("Volume", 0)),
            })
        except (KeyError, ValueError, TypeError):
            continue
    return records


def fetch_history_df_with_fallback(symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV as DataFrame for backtesting. For US stocks: try akshare first.
    Returns DataFrame with Open, High, Low, Close, Volume columns and DatetimeIndex.
    """
    hist = None
    if _is_us_stock_symbol(symbol) and _akshare_available:
        hist = fetch_history_ak(symbol, period)
    if hist is None:
        hist = fetch_history_yf(symbol, period, "1d")
    return hist


def _fetch_single_price_yf(symbol: str) -> Optional[dict]:
    """Fetch one symbol via yf.Ticker().history(). Works for indices, crypto, commodities, forex."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d", interval="1d")
        if hist is None or hist.empty or len(hist) < 1:
            return None
        hist = hist.dropna(subset=["Close"])
        if len(hist) < 1:
            return None
        price = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price
        return {"price": round(price, 2), "prev_close": round(prev, 2)}
    except Exception as e:
        logger.debug(f"yfinance single fetch failed for {symbol}: {e}")
        return None


def fetch_batch_prices_with_fallback(symbols: list[str]) -> dict[str, dict]:
    """
    Fetch prices for multiple symbols.
    For US stocks: try akshare FIRST to avoid Yahoo rate limits (429).
    For indices/crypto/commodities/forex: use yfinance with per-symbol fallback.
    """
    results = {}

    # Try akshare first for US-stock-only lists (sectors, gainers) - avoids Yahoo entirely
    us_only = all(_is_us_stock_symbol(s) for s in symbols)
    if us_only and _akshare_available:
        for sym in symbols:
            p = fetch_price_ak(sym)
            if p:
                results[sym] = p
        if len(results) == len(symbols):
            return results
        # Partial success - fill rest via yfinance below
        if results:
            logger.info(f"akshare primary: got {len(results)}/{len(symbols)} US stock prices")

    # yfinance batch (skip if we already have everything from akshare)
    if len(results) < len(symbols):
        try:
            missing = [s for s in symbols if s not in results]
            df = yf.download(
                " ".join(missing),
                period="5d",
                interval="1d",
                group_by="ticker",
                progress=False,
                threads=False,
            )
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    ticker_names = df.columns.get_level_values(0).unique()
                else:
                    ticker_names = [missing[0]] if len(missing) == 1 else []

                for sym in missing:
                    try:
                        if sym not in ticker_names:
                            continue
                        sub = df[sym].copy() if isinstance(df.columns, pd.MultiIndex) else df
                        if sub is None or sub.empty:
                            continue
                        sub = sub.dropna(subset=["Close"])
                        if len(sub) < 1:
                            continue
                        price = float(sub["Close"].iloc[-1])
                        prev = float(sub["Close"].iloc[-2]) if len(sub) >= 2 else price
                        results[sym] = {"price": round(price, 2), "prev_close": round(prev, 2)}
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"yfinance batch download failed: {e}")

    # Fallback: akshare for missing US stocks
    for sym in symbols:
        if sym in results:
            continue
        if _is_us_stock_symbol(sym) and _akshare_available:
            p = fetch_price_ak(sym)
            if p:
                results[sym] = p

    # Fallback: per-symbol yfinance for indices, crypto, commodities, forex
    for sym in symbols:
        if sym in results:
            continue
        p = _fetch_single_price_yf(sym)
        if p:
            results[sym] = p

    return results
