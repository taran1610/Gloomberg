"""
News search service for commodities, forex, crypto, and indices.
Uses Google News RSS when Financial Datasets / yfinance don't have ticker-specific news.
"""

import logging
import re
import xml.etree.ElementTree as ET
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Map tickers to search queries for news
NEWS_QUERY_MAP: dict[str, str] = {
    "GC=F": "gold price",
    "SI=F": "silver price",
    "CL=F": "crude oil WTI",
    "BZ=F": "brent crude oil",
    "NG=F": "natural gas",
    "HG=F": "copper price",
    "PL=F": "platinum price",
    "PA=F": "palladium price",
    "ZW=F": "wheat futures",
    "ZC=F": "corn futures",
    "ZS=F": "soybeans futures",
    "EURUSD=X": "EUR USD forex",
    "GBPUSD=X": "GBP USD forex",
    "USDJPY=X": "USD JPY forex",
    "AUDUSD=X": "AUD USD forex",
    "USDCAD=X": "USD CAD forex",
    "USDCHF=X": "USD CHF forex",
    "NZDUSD=X": "NZD USD forex",
    "EURGBP=X": "EUR GBP forex",
    "EURJPY=X": "EUR JPY forex",
    "GBPJPY=X": "GBP JPY forex",
    "DX-Y.NYB": "US dollar index",
    "^GSPC": "S&P 500",
    "^DJI": "Dow Jones",
    "^IXIC": "NASDAQ",
    "^RUT": "Russell 2000",
    "^FTSE": "FTSE 100",
    "^N225": "Nikkei 225",
    "^VIX": "VIX volatility",
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "SOL-USD": "Solana",
    "XRP-USD": "XRP cryptocurrency",
    "ADA-USD": "Cardano",
    "BNB-USD": "BNB cryptocurrency",
}


def _get_news_query(ticker: str) -> Optional[str]:
    t = ticker.upper()
    if t in NEWS_QUERY_MAP:
        return NEWS_QUERY_MAP[t]
    if t.endswith("=F"):
        return f"{t.replace('=F', '')} futures"
    if t.endswith("=X"):
        return t.replace("=X", "").replace("USD", "USD ") + " forex"
    if t.startswith("^"):
        return t[1:] + " index"
    if t.endswith("-USD") or t.endswith("-USDT"):
        return t.replace("-USD", "").replace("-USDT", "") + " cryptocurrency"
    return None


async def search_news(ticker: str, limit: int = 15) -> list[dict]:
    """
    Fetch news via Google News RSS for commodities, forex, crypto, indices.
    Returns list of {title, publisher, link, published}.
    """
    query = _get_news_query(ticker)
    if not query:
        return []

    search_q = f"{query} news"
    url = "https://news.google.com/rss/search"
    params = {
        "q": search_q,
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
    except Exception as e:
        logger.warning(f"News RSS fetch failed for {ticker}: {e}")
        return []

    try:
        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = root.findall(".//item") or root.findall("channel/item")
        results = []
        for item in items[:limit]:
            title_el = item.find("title")
            link_el = item.find("link")
            source_el = item.find("source")
            pub_el = item.find("pubDate")
            title = title_el.text if title_el is not None and title_el.text else ""
            link = link_el.text if link_el is not None and link_el.text else ""
            publisher = ""
            if source_el is not None and source_el.text:
                publisher = source_el.text
            pub_date = pub_el.text if pub_el is not None and pub_el.text else ""
            if title:
                results.append({
                    "title": title,
                    "publisher": publisher,
                    "link": link,
                    "published": pub_date,
                })
        return results
    except ET.ParseError as e:
        logger.warning(f"News RSS parse error for {ticker}: {e}")
        return []
