"""
Relative Value: peer comparison and normalized price chart (base 100).
Returns peer list, comparison table (with median), and chart series for REL VALUE tab.
"""
import logging
from typing import Optional

import yfinance as yf
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Sector / industry -> peer tickers (include ticker itself)
PEER_GROUPS = {
    "semiconductors": ["NVDA", "AMD", "INTC", "AVGO", "QCOM", "TXN", "MRVL", "ARM"],
    "technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "ORCL", "CRM", "ADBE"],
    "default": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "JPM"],
}


def _get_peer_tickers(ticker: str) -> list[str]:
    """Return list of peer tickers including the given ticker."""
    ticker = ticker.upper()
    for group in [PEER_GROUPS["semiconductors"], PEER_GROUPS["technology"]]:
        if ticker in group:
            return group
    return [ticker] + [t for t in PEER_GROUPS["default"] if t != ticker][:7]


def _safe_float(v, default=None):
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _safe_pct(v, default=None):
    x = _safe_float(v, default)
    if x is None:
        return default
    if abs(x) <= 1:
        x = x * 100
    return round(x, 2)


def get_rel_value_data(ticker: str, period: str = "1y") -> dict:
    """
    Returns:
      - ticker, period
      - chart_series: { ticker: [ { date, value } ] }  (normalized base 100)
      - peers: [ { ticker, name, market_cap, last_px, chg_pct_1d, chg_pct_1m,
                   rev_growth_1y, eps_growth_1y, pe, roe, dvd_yield }, ... ]
      - median: same keys for median row
    """
    ticker = ticker.upper()
    peer_tickers = _get_peer_tickers(ticker)
    if ticker not in peer_tickers:
        peer_tickers = [ticker] + peer_tickers[:7]

    # Map period to yfinance period
    period_map = {"3m": "3mo", "6m": "6mo", "1y": "1y", "2y": "2y", "5y": "5y"}
    yf_period = period_map.get(period, "1y")

    chart_series = {}
    try:
        # Download all peers in one call for efficiency
        syms = " ".join(peer_tickers)
        df = yf.download(syms, period=yf_period, interval="1d", group_by="ticker", progress=False, threads=False, auto_adjust=True)
        if df.empty:
            pass
        else:
            for sym in peer_tickers:
                try:
                    if sym in df.columns.get_level_values(0):
                        sub = df[sym].copy()
                    else:
                        continue
                    if sub is None or sub.empty or "Close" not in sub.columns:
                        continue
                    sub = sub.dropna(subset=["Close"])
                    if len(sub) < 2:
                        continue
                    close = sub["Close"]
                    base = float(close.iloc[0])
                    if base <= 0:
                        continue
                    normalized = (close / base * 100).round(2)
                    chart_series[sym] = [
                        {"date": d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)[:10], "value": float(normalized.iloc[i])}
                        for i, d in enumerate(normalized.index)
                    ]
                except Exception as e:
                    logger.debug(f"Chart series for {sym}: {e}")
    except Exception as e:
        logger.error(f"Rel value chart download: {e}")

    # Peer comparison: fetch info for each
    peers = []
    for sym in peer_tickers:
        try:
            t = yf.Ticker(sym)
            info = t.info or {}
            hist = t.history(period="1mo", interval="1d")
            price = _safe_float(info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose"), 0)
            prev_close = _safe_float(info.get("regularMarketPreviousClose") or info.get("previousClose"), price)
            chg_1d = ((price - prev_close) / prev_close * 100) if prev_close and prev_close != 0 else None

            chg_1m = None
            if hist is not None and not hist.empty and len(hist) >= 2:
                first = float(hist["Close"].iloc[0])
                last = float(hist["Close"].iloc[-1])
                if first and first != 0:
                    chg_1m = round((last - first) / first * 100, 2)

            rev_growth = info.get("revenueGrowth")
            if rev_growth is not None:
                rev_growth = _safe_pct(rev_growth)
            eps_growth = info.get("earningsGrowth")
            if eps_growth is not None:
                eps_growth = _safe_pct(eps_growth)
            roe = info.get("returnOnEquity")
            if roe is not None:
                roe = _safe_pct(roe)

            dvd = info.get("dividendYield")
            if dvd is not None:
                dvd = _safe_pct(dvd) if abs(dvd) <= 1 else round(float(dvd), 2)

            peers.append({
                "ticker": sym,
                "name": (info.get("shortName") or info.get("longName") or sym).upper(),
                "market_cap": _safe_float(info.get("marketCap")),
                "last_px": round(price, 2) if price is not None else None,
                "chg_pct_1d": round(chg_1d, 2) if chg_1d is not None else None,
                "chg_pct_1m": chg_1m,
                "rev_growth_1y": rev_growth,
                "eps_growth_1y": eps_growth,
                "pe": _safe_float(info.get("trailingPE")),
                "roe": roe,
                "dvd_yield": dvd,
            })
        except Exception as e:
            logger.debug(f"Peer {sym}: {e}")
            peers.append({
                "ticker": sym,
                "name": sym,
                "market_cap": None,
                "last_px": None,
                "chg_pct_1d": None,
                "chg_pct_1m": None,
                "rev_growth_1y": None,
                "eps_growth_1y": None,
                "pe": None,
                "roe": None,
                "dvd_yield": None,
            })

    # Median row (exclude nulls for numeric cols)
    median_row = {"ticker": "Median", "name": "Median", "market_cap": None, "last_px": None, "chg_pct_1d": None, "chg_pct_1m": None, "rev_growth_1y": None, "eps_growth_1y": None, "pe": None, "roe": None, "dvd_yield": None}
    for key in ["market_cap", "last_px", "chg_pct_1d", "chg_pct_1m", "rev_growth_1y", "eps_growth_1y", "pe", "roe", "dvd_yield"]:
        vals = [p[key] for p in peers if p[key] is not None]
        if vals:
            median_row[key] = round(float(np.median(vals)), 2) if key != "market_cap" else round(float(np.median(vals)), 0)

    return {
        "ticker": ticker,
        "period": period,
        "chart_series": chart_series,
        "peers": peers,
        "median": median_row,
    }
