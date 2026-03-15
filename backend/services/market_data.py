import yfinance as yf
import json
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from redis import asyncio as aioredis

from config import get_settings
from services.data_sources import (
    fetch_batch_prices_with_fallback,
    fetch_history_with_fallback,
    fetch_asset_ak,
    _is_us_stock_symbol,
)
from services.edgar_helper import (
    get_ownership_from_edgar,
    get_insider_transactions_from_edgar,
    get_debt_data_from_edgar,
)
from services.dummy_data import (
    get_dummy_ownership,
    get_dummy_debt,
    get_dummy_insider_transactions,
    get_dummy_news,
    get_dummy_candles,
)

logger = logging.getLogger(__name__)

MAJOR_INDICES = {
    "^GSPC": "S&P 500",
    "^DJI": "Dow Jones",
    "^IXIC": "NASDAQ",
    "^RUT": "Russell 2000",
    "^FTSE": "FTSE 100",
    "^N225": "Nikkei 225",
}

SECTOR_ETFS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLV": "Healthcare",
    "XLE": "Energy",
    "XLI": "Industrials",
    "XLY": "Consumer Disc.",
    "XLP": "Consumer Staples",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
    "XLB": "Materials",
    "XLC": "Communication",
}

CRYPTO_TICKERS = {
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "SOL-USD": "Solana",
    "BNB-USD": "BNB",
    "XRP-USD": "XRP",
    "ADA-USD": "Cardano",
}

STOCK_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
    "JPM", "V", "UNH", "MA", "HD", "PG", "JNJ", "COST", "ABBV", "MRK",
    "CRM", "NFLX", "AMD", "PEP", "ADBE", "TMO", "ORCL",
]

COMMODITY_TICKERS = {
    "GC=F": "Gold",
    "SI=F": "Silver",
    "CL=F": "Crude Oil WTI",
    "BZ=F": "Brent Crude",
    "NG=F": "Natural Gas",
    "HG=F": "Copper",
    "PL=F": "Platinum",
}

FOREX_TICKERS = {
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
    "USDJPY=X": "USD/JPY",
    "AUDUSD=X": "AUD/USD",
    "USDCAD=X": "USD/CAD",
    "USDCHF=X": "USD/CHF",
    "DX-Y.NYB": "US Dollar Index",
}


class MemCache:
    """Simple in-memory TTL cache for when Redis is unavailable."""

    def __init__(self):
        self._store: dict[str, tuple[float, str]] = {}

    def get(self, key: str) -> Optional[str]:
        entry = self._store.get(key)
        if entry is None:
            return None
        expiry, value = entry
        if time.time() > expiry:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: str, ttl: int):
        self._store[key] = (time.time() + ttl, value)


_mem_cache = MemCache()


def _batch_download_prices(symbols: list[str]) -> dict[str, dict]:
    """
    Fetch prices for many tickers. Uses yfinance with akshare fallback for US stocks.
    Returns {symbol: {"price": ..., "prev_close": ...}} for each.
    """
    if not symbols:
        return {}
    return fetch_batch_prices_with_fallback(symbols)


def _get_ticker_names(symbols: list[str]) -> dict[str, str]:
    """Fetch short names via yf.Tickers (one call for up to ~10 tickers)."""
    names = {}
    try:
        tickers_obj = yf.Tickers(" ".join(symbols))
        for sym in symbols:
            try:
                info = tickers_obj.tickers[sym].info
                names[sym] = info.get("shortName", sym)[:30]
            except Exception:
                names[sym] = sym
    except Exception:
        for sym in symbols:
            names[sym] = sym
    return names


class MarketDataService:
    def __init__(self, redis: Optional[aioredis.Redis] = None):
        self.redis = redis
        self.settings = get_settings()

    async def _cache_get(self, key: str) -> Optional[str]:
        val = _mem_cache.get(key)
        if val is not None:
            return val
        if not self.redis:
            return None
        try:
            val = await self.redis.get(key)
            if val:
                _mem_cache.set(key, val, 60)
            return val
        except Exception:
            return None

    async def _cache_set(self, key: str, value: str, ttl: int):
        _mem_cache.set(key, value, ttl)
        if not self.redis:
            return
        try:
            await self.redis.set(key, value, ex=ttl)
        except Exception:
            pass

    def _fetch_ticker_data(self, symbol: str) -> dict:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
            return info
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return {}

    def _fetch_history(self, symbol: str, period: str = "1y", interval: str = "1d") -> list[dict]:
        """Fetch OHLCV history. Uses yfinance with akshare fallback for US stocks."""
        return fetch_history_with_fallback(symbol, period, interval)

    async def get_indices(self) -> list[dict]:
        cached = await self._cache_get("indices")
        if cached:
            return json.loads(cached)

        symbols = list(MAJOR_INDICES.keys())
        prices = await asyncio.to_thread(_batch_download_prices, symbols)

        results = []
        for symbol, name in MAJOR_INDICES.items():
            p = prices.get(symbol, {})
            price = p.get("price", 0)
            prev = p.get("prev_close", price)
            change = price - prev if prev else 0
            change_pct = (change / prev * 100) if prev else 0
            results.append({
                "name": name,
                "ticker": symbol,
                "price": round(price, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
            })

        # If yfinance failed (all zeros), use ETF proxies via akshare
        if all(r["price"] == 0 for r in results):
            from services.alt_data_sources import fetch_indices_via_etf
            etf_results = await asyncio.to_thread(fetch_indices_via_etf)
            if etf_results:
                results = etf_results

        await self._cache_set("indices", json.dumps(results), self.settings.cache_ttl_dashboard)
        return results

    async def get_gainers_losers(self) -> tuple[list[dict], list[dict]]:
        cached = await self._cache_get("gainers_losers")
        if cached:
            data = json.loads(cached)
            return data["gainers"], data["losers"]

        prices = await asyncio.to_thread(_batch_download_prices, STOCK_TICKERS)
        names = await asyncio.to_thread(_get_ticker_names, [s for s in STOCK_TICKERS if s in prices])

        movers = []
        for symbol in STOCK_TICKERS:
            p = prices.get(symbol)
            if not p or not p["price"] or not p["prev_close"]:
                continue
            price = p["price"]
            prev = p["prev_close"]
            change_pct = ((price - prev) / prev * 100) if prev else 0
            movers.append({
                "ticker": symbol,
                "name": names.get(symbol, symbol),
                "price": round(price, 2),
                "change_pct": round(change_pct, 2),
            })

        movers.sort(key=lambda x: x["change_pct"], reverse=True)
        gainers = movers[:10]
        losers = sorted(movers, key=lambda x: x["change_pct"])[:10]

        data = {"gainers": gainers, "losers": losers}
        await self._cache_set("gainers_losers", json.dumps(data), self.settings.cache_ttl_dashboard)
        return gainers, losers

    async def get_sectors(self) -> list[dict]:
        cached = await self._cache_get("sectors")
        if cached:
            return json.loads(cached)

        symbols = list(SECTOR_ETFS.keys())
        prices = await asyncio.to_thread(_batch_download_prices, symbols)

        results = []
        for symbol, name in SECTOR_ETFS.items():
            p = prices.get(symbol, {})
            price = p.get("price", 0)
            prev = p.get("prev_close", price)
            change_pct = ((price - prev) / prev * 100) if prev else 0
            results.append({
                "name": name,
                "change_pct": round(change_pct, 2),
            })

        await self._cache_set("sectors", json.dumps(results), self.settings.cache_ttl_dashboard)
        return results

    async def get_crypto(self) -> list[dict]:
        cached = await self._cache_get("crypto")
        if cached:
            return json.loads(cached)

        # Prefer CoinGecko (free, no Yahoo rate limits)
        from services.alt_data_sources import fetch_crypto_coingecko
        results = await asyncio.to_thread(fetch_crypto_coingecko)
        if not results:
            symbols = list(CRYPTO_TICKERS.keys())
            prices = await asyncio.to_thread(_batch_download_prices, symbols)
            results = []
            for symbol, name in CRYPTO_TICKERS.items():
                p = prices.get(symbol, {})
                price = p.get("price", 0)
                prev = p.get("prev_close", price)
                change_pct = ((price - prev) / prev * 100) if prev else 0
                results.append({
                    "ticker": symbol,
                    "name": name,
                    "price": round(price, 2),
                    "change_pct": round(change_pct, 2),
                })

        if results:
            await self._cache_set("crypto", json.dumps(results), self.settings.cache_ttl_dashboard)
        return results

    async def get_commodities(self) -> list[dict]:
        cached = await self._cache_get("commodities")
        if cached:
            return json.loads(cached)

        # Prefer akshare commodities (avoids Yahoo rate limits)
        from services.alt_data_sources import fetch_commodities_akshare
        results = await asyncio.to_thread(fetch_commodities_akshare)
        if not results:
            symbols = list(COMMODITY_TICKERS.keys())
            prices = await asyncio.to_thread(_batch_download_prices, symbols)
            results = []
            for symbol, name in COMMODITY_TICKERS.items():
                p = prices.get(symbol, {})
                price = p.get("price", 0)
                prev = p.get("prev_close", price)
                change_pct = ((price - prev) / prev * 100) if prev else 0
                results.append({
                    "ticker": symbol,
                    "name": name,
                    "price": round(price, 2),
                    "change_pct": round(change_pct, 2),
                })

        if results:
            await self._cache_set("commodities", json.dumps(results), self.settings.cache_ttl_dashboard)
        return results

    async def get_forex(self) -> list[dict]:
        cached = await self._cache_get("forex")
        if cached:
            return json.loads(cached)

        # Prefer akshare forex (avoids Yahoo rate limits)
        from services.alt_data_sources import fetch_forex_akshare
        results = await asyncio.to_thread(fetch_forex_akshare)
        if not results:
            symbols = list(FOREX_TICKERS.keys())
            prices = await asyncio.to_thread(_batch_download_prices, symbols)
            results = []
            for symbol, name in FOREX_TICKERS.items():
                p = prices.get(symbol, {})
                price = p.get("price", 0)
                prev = p.get("prev_close", price)
                change_pct = ((price - prev) / prev * 100) if prev else 0
                results.append({
                    "ticker": symbol,
                    "name": name,
                    "price": round(price, 4),
                    "change_pct": round(change_pct, 2),
                })

        if results:
            await self._cache_set("forex", json.dumps(results), self.settings.cache_ttl_dashboard)
        return results

    async def get_vix(self) -> Optional[float]:
        try:
            prices = await asyncio.to_thread(_batch_download_prices, ["^VIX"])
            p = prices.get("^VIX", {})
            return round(p.get("price", 0), 2) or None
        except Exception:
            return None

    async def get_asset(self, ticker: str) -> dict:
        cached = await self._cache_get(f"asset:{ticker}")
        if cached:
            return json.loads(cached)

        info = await asyncio.to_thread(self._fetch_ticker_data, ticker)
        price = info.get("regularMarketPrice", info.get("currentPrice", info.get("previousClose", 0)))
        prev = info.get("regularMarketPreviousClose", info.get("previousClose", price))

        # Akshare fallback when yfinance fails (429 rate limit, JSON decode errors)
        if (not price or not prev) and _is_us_stock_symbol(ticker):
            ak_data = await asyncio.to_thread(fetch_asset_ak, ticker)
            if ak_data:
                info = {
                    **info,
                    "regularMarketPrice": ak_data["price"],
                    "currentPrice": ak_data["price"],
                    "previousClose": ak_data["prev_close"],
                    "regularMarketPreviousClose": ak_data["prev_close"],
                    "shortName": ak_data.get("name", ticker),
                }
                price = ak_data["price"]
                prev = ak_data["prev_close"]
                logger.info(f"akshare fallback: got asset data for {ticker}")
        change = price - prev if prev else 0
        change_pct = (change / prev * 100) if prev else 0

        officers = []
        raw_officers = info.get("companyOfficers", [])
        if isinstance(raw_officers, list):
            for off in raw_officers[:5]:
                if isinstance(off, dict):
                    officers.append({
                        "name": off.get("name", ""),
                        "title": off.get("title", ""),
                        "age": off.get("age"),
                    })

        classification = None
        ind = info.get("industry")
        sect = info.get("sector")
        if ind:
            classification = ind.upper()
        elif sect:
            classification = sect.upper()

        result = {
            "ticker": ticker.upper(),
            "name": info.get("shortName", info.get("longName", ticker)),
            "price": round(price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "volume": info.get("volume"),
            "avg_volume": info.get("averageVolume"),
            "high_52w": info.get("fiftyTwoWeekHigh"),
            "low_52w": info.get("fiftyTwoWeekLow"),
            "dividend_yield": info.get("dividendYield"),
            "beta": info.get("beta"),
            "website": info.get("website"),
            "city": info.get("city"),
            "state": info.get("state"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "full_time_employees": info.get("fullTimeEmployees"),
            "forward_pe": info.get("forwardPE"),
            "trailing_eps": info.get("trailingEps"),
            "target_mean_price": info.get("targetMeanPrice"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "float_shares": info.get("floatShares"),
            "price_to_book": info.get("priceToBook"),
            "enterprise_value": info.get("enterpriseValue"),
            "enterprise_to_revenue": info.get("enterpriseToRevenue"),
            "enterprise_to_ebitda": info.get("enterpriseToEbitda"),
            "peg_ratio": info.get("pegRatio"),
            "price_to_sales": info.get("priceToSalesTrailing12Months"),
            "day_open": info.get("regularMarketOpen", info.get("open")),
            "day_high": info.get("dayHigh", info.get("regularMarketDayHigh")),
            "day_low": info.get("dayLow", info.get("regularMarketDayLow")),
            "prev_close": info.get("regularMarketPreviousClose", info.get("previousClose")),
            "officers": officers,
            "classification": classification,
            "short_pct_float": info.get("shortPercentOfFloat"),
            "short_ratio": info.get("shortRatio"),
            "fifty_two_week_change": info.get("52WeekChange"),
            "forward_eps": info.get("forwardEps"),
        }

        await self._cache_set(f"asset:{ticker}", json.dumps(result), self.settings.cache_ttl_ticker)
        return result

    async def get_ownership(self, ticker: str) -> dict:
        cache_key = f"ownership:{ticker}"
        cached = await self._cache_get(cache_key)
        if cached:
            return json.loads(cached)

        try:
            t = yf.Ticker(ticker)
            major = t.major_holders
            inst = t.institutional_holders

            insiders_pct = None
            institutions_pct = None
            institutions_float_pct = None
            institutions_count = None

            if major is not None and not major.empty:
                for idx in major.index:
                    label = str(idx).strip().lower()
                    val = major.loc[idx].iloc[0]
                    try:
                        v = float(val)
                    except (ValueError, TypeError):
                        continue
                    if "insider" in label:
                        insiders_pct = round(v * 100, 2) if v <= 1 else round(v, 2)
                    elif "institutionspercentheld" in label:
                        institutions_pct = round(v * 100, 2) if v <= 1 else round(v, 2)
                    elif "float" in label:
                        institutions_float_pct = round(v * 100, 2) if v <= 1 else round(v, 2)
                    elif "count" in label:
                        institutions_count = int(v)

            holders = []
            if inst is not None and not inst.empty:
                for _, row in inst.head(20).iterrows():
                    d = row.to_dict()
                    holder = d.get("Holder", "")
                    pct = d.get("pctHeld", 0) or 0
                    shares = d.get("Shares", 0) or 0
                    value = d.get("Value")
                    pct_ch = d.get("pctChange")
                    date_r = d.get("Date Reported")
                    try:
                        pct = float(pct) * 100 if pct is not None and float(pct) <= 1 else float(pct or 0)
                    except (ValueError, TypeError):
                        pct = 0
                    try:
                        shares = int(float(shares))
                    except (ValueError, TypeError):
                        shares = 0
                    try:
                        value = float(value) if value is not None else None
                    except (ValueError, TypeError):
                        value = None
                    try:
                        pct_ch = float(pct_ch) * 100 if pct_ch is not None and abs(float(pct_ch)) <= 1 else float(pct_ch) if pct_ch is not None else None
                    except (ValueError, TypeError):
                        pct_ch = None
                    date_str = str(date_r) if date_r is not None else None
                    if hasattr(date_r, "strftime"):
                        date_str = date_r.strftime("%Y-%m-%d")
                    holders.append({
                        "holder": str(holder),
                        "pct_held": round(pct, 2),
                        "shares": shares,
                        "value": value,
                        "pct_change": round(pct_ch, 2) if pct_ch is not None else None,
                        "date_reported": date_str,
                    })

            result = {
                "ticker": ticker.upper(),
                "shares_outstanding": None,
                "insiders_pct": insiders_pct,
                "institutions_pct": institutions_pct,
                "institutions_float_pct": institutions_float_pct,
                "institutions_count": institutions_count,
                "institutional_holders": holders,
            }
            # Use EDGAR (SEC filings) as primary for shares_outstanding and public_float
            edgar_data = await asyncio.to_thread(get_ownership_from_edgar, ticker)
            if edgar_data:
                if edgar_data.get("shares_outstanding") is not None:
                    result["shares_outstanding"] = edgar_data["shares_outstanding"]
                if edgar_data.get("public_float") is not None:
                    result["public_float"] = edgar_data["public_float"]
            # Fallback to yfinance shares if EDGAR had none
            if result["shares_outstanding"] is None:
                yf_info = t.info or {}
                if yf_info.get("sharesOutstanding"):
                    result["shares_outstanding"] = float(yf_info["sharesOutstanding"])
            # Always show something: use dummy when empty
            if not result.get("institutional_holders"):
                dummy = get_dummy_ownership(ticker)
                result["institutional_holders"] = dummy["institutional_holders"]
                if result.get("shares_outstanding") is None:
                    result["shares_outstanding"] = dummy["shares_outstanding"]
                for k in ("insiders_pct", "institutions_pct", "institutions_float_pct", "institutions_count"):
                    if result.get(k) is None:
                        result[k] = dummy.get(k)
            await self._cache_set(cache_key, json.dumps(result), self.settings.cache_ttl_ticker)
            return result
        except Exception as e:
            logger.error(f"Error fetching ownership for {ticker}: {e}")
            return get_dummy_ownership(ticker)

    async def get_history(self, ticker: str, period: str = "1y", interval: str = "1d") -> list[dict]:
        cache_key = f"history:{ticker}:{period}:{interval}"
        cached = await self._cache_get(cache_key)
        if cached:
            return json.loads(cached)

        records = await asyncio.to_thread(self._fetch_history, ticker, period, interval)
        # Always show something: use dummy chart when empty
        if not records:
            records = get_dummy_candles(ticker)
        await self._cache_set(cache_key, json.dumps(records), self.settings.cache_ttl_history)
        return records

    async def get_news(self, ticker: str) -> list[dict]:
        cached = await self._cache_get(f"news:{ticker}")
        if cached:
            return json.loads(cached)

        try:
            t = yf.Ticker(ticker)
            news = t.news or []
            results = []
            for item in news[:15]:
                content = item.get("content", {}) if isinstance(item.get("content"), dict) else {}
                title = content.get("title") or item.get("title", "")
                provider = content.get("provider", {})
                publisher = provider.get("displayName", "") if isinstance(provider, dict) else item.get("publisher", "")
                link = content.get("clickThroughUrl", {}).get("url", "") if isinstance(content.get("clickThroughUrl"), dict) else item.get("link", "")
                if not link:
                    link = content.get("canonicalUrl", {}).get("url", "") if isinstance(content.get("canonicalUrl"), dict) else ""
                pub_date = content.get("pubDate") or item.get("providerPublishTime", "")
                if title:
                    results.append({
                        "title": title,
                        "publisher": publisher,
                        "link": link,
                        "published": pub_date,
                    })
            # Always show something: use dummy when empty
            if not results:
                results = get_dummy_news(ticker)
            await self._cache_set(f"news:{ticker}", json.dumps(results), self.settings.cache_ttl_news)
            return results
        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")
            return get_dummy_news(ticker)

    async def get_insider_transactions(self, ticker: str) -> dict:
        cache_key = f"insider_tx:{ticker}"
        cached = await self._cache_get(cache_key)
        if cached:
            return json.loads(cached)

        # Try edgartools (Form 4) first for US companies
        edgar_result = await asyncio.to_thread(get_insider_transactions_from_edgar, ticker)
        if edgar_result and edgar_result.get("insider_transactions"):
            await self._cache_set(cache_key, json.dumps(edgar_result), self.settings.cache_ttl_ticker)
            return edgar_result

        def _fetch():
            try:
                t = yf.Ticker(ticker)
                txns = getattr(t, "insider_transactions", None)
                if txns is None or (hasattr(txns, "empty") and txns.empty):
                    return {"ticker": ticker, "transactions": 0, "buys": 0, "sells": 0, "insider_transactions": []}

                records = []
                buys = 0
                sells = 0
                for _, row in txns.head(50).iterrows():
                    d = row.to_dict()
                    shares_raw = d.get("Shares", d.get("shares", 0))
                    try:
                        shares = int(float(shares_raw or 0))
                    except (ValueError, TypeError):
                        shares = 0

                    if shares > 0:
                        buys += 1
                    elif shares < 0:
                        sells += 1

                    insider_name = str(d.get("Insider", d.get("insider", d.get("Text", ""))))
                    title = str(d.get("Position", d.get("Ownership", d.get("Relation", ""))))
                    trans_date = d.get("Start Date", d.get("Date", d.get("startDate", "")))
                    if hasattr(trans_date, "strftime"):
                        trans_date = trans_date.strftime("%Y-%m-%d")
                    else:
                        trans_date = str(trans_date) if trans_date else ""

                    price_val = d.get("Value", d.get("value", None))
                    try:
                        price_val = float(price_val) if price_val else None
                    except (ValueError, TypeError):
                        price_val = None

                    records.append({
                        "insider_name": insider_name,
                        "title": title,
                        "trans_date": trans_date,
                        "shares": shares,
                        "price": round(abs(price_val / shares), 2) if price_val and shares else None,
                        "value": price_val,
                    })

                return {
                    "ticker": ticker,
                    "transactions": len(records),
                    "buys": buys,
                    "sells": sells,
                    "insider_transactions": records,
                }
            except Exception as e:
                logger.error(f"Error fetching insider transactions for {ticker}: {e}")
                return {"ticker": ticker, "transactions": 0, "buys": 0, "sells": 0, "insider_transactions": []}

        result = await asyncio.to_thread(_fetch)
        # Always show something: use dummy when empty
        if not result.get("insider_transactions"):
            result = get_dummy_insider_transactions(ticker)
        await self._cache_set(cache_key, json.dumps(result), self.settings.cache_ttl_ticker)
        return result

    async def get_debt_data(self, ticker: str) -> dict:
        cache_key = f"debt:{ticker}"
        cached = await self._cache_get(cache_key)
        if cached:
            return json.loads(cached)

        # Use EDGAR (10-K/10-Q) first for US stocks - official SEC filings
        if _is_us_stock_symbol(ticker):
            edgar_debt = await asyncio.to_thread(get_debt_data_from_edgar, ticker)
            if edgar_debt and edgar_debt.get("items"):
                await self._cache_set(cache_key, json.dumps(edgar_debt), self.settings.cache_ttl_ticker)
                return edgar_debt

        def _fetch():
            try:
                t = yf.Ticker(ticker)
                info = t.info or {}
                bs = t.balance_sheet

                items = []
                fiscal_year = ""

                if bs is not None and not bs.empty:
                    col = bs.columns[0]
                    if hasattr(col, "strftime"):
                        fiscal_year = col.strftime("%Y") + "-FY"
                    else:
                        fiscal_year = str(col)

                    def _get(label: str) -> Optional[float]:
                        for idx_name in bs.index:
                            if label.lower() in str(idx_name).lower():
                                val = bs.loc[idx_name, col]
                                if val is not None and str(val) != "nan":
                                    return float(val)
                        return None

                    total_debt = info.get("totalDebt") or _get("Total Debt")
                    current_debt = _get("Current Debt") or _get("Current Portion")
                    long_term_debt = info.get("longTermDebt") or _get("Long Term Debt")
                    total_liabilities = _get("Total Liabilities")
                    current_liabilities = _get("Current Liabilities")
                    noncurrent_liabilities = _get("Total Non Current Liabilities")
                    total_assets = _get("Total Assets")
                    stockholders_equity = _get("Stockholders Equity") or _get("Total Equity")

                    items = [
                        {"label": "Total Debt", "value": total_debt},
                        {"label": "Current Debt (Due < 1yr)", "value": current_debt},
                        {"label": "Long-Term Debt", "value": long_term_debt},
                        {"label": "Total Liabilities", "value": total_liabilities},
                        {"label": "Current Liabilities", "value": current_liabilities},
                        {"label": "Non-Current Liabilities", "value": noncurrent_liabilities},
                        {"label": "Total Assets", "value": total_assets},
                        {"label": "Shareholders' Equity", "value": stockholders_equity},
                    ]

                    debt_equity = None
                    debt_assets = None
                    liab_assets = None
                    if total_debt and stockholders_equity and stockholders_equity != 0:
                        debt_equity = round(total_debt / stockholders_equity * 100, 1)
                    if total_debt and total_assets and total_assets != 0:
                        debt_assets = round(total_debt / total_assets * 100, 1)
                    if total_liabilities and total_assets and total_assets != 0:
                        liab_assets = round(total_liabilities / total_assets * 100, 1)

                    items.extend([
                        {"label": "Debt / Equity Ratio", "value": debt_equity},
                        {"label": "Debt / Assets Ratio", "value": debt_assets},
                        {"label": "Liabilities / Assets", "value": liab_assets},
                    ])

                return {
                    "ticker": ticker,
                    "fiscal_year": fiscal_year,
                    "items": items,
                }
            except Exception as e:
                logger.error(f"Error fetching debt data for {ticker}: {e}")
                return {"ticker": ticker, "fiscal_year": "", "items": []}

        result = await asyncio.to_thread(_fetch)
        # Always show something: use dummy when empty
        if not result.get("items"):
            result = get_dummy_debt(ticker)
        await self._cache_set(cache_key, json.dumps(result), self.settings.cache_ttl_ticker)
        return result

    async def search_tickers(self, query: str) -> list[dict]:
        SEARCH_ALIASES = {
            "GOLD": ("GC=F", "Gold Futures", "COMMODITY"),
            "SILVER": ("SI=F", "Silver Futures", "COMMODITY"),
            "OIL": ("CL=F", "Crude Oil WTI Futures", "COMMODITY"),
            "CRUDE": ("CL=F", "Crude Oil WTI Futures", "COMMODITY"),
            "NATGAS": ("NG=F", "Natural Gas Futures", "COMMODITY"),
            "COPPER": ("HG=F", "Copper Futures", "COMMODITY"),
            "PLATINUM": ("PL=F", "Platinum Futures", "COMMODITY"),
            "BRENT": ("BZ=F", "Brent Crude Futures", "COMMODITY"),
            "EUR": ("EURUSD=X", "EUR/USD", "FOREX"),
            "EURUSD": ("EURUSD=X", "EUR/USD", "FOREX"),
            "GBP": ("GBPUSD=X", "GBP/USD", "FOREX"),
            "GBPUSD": ("GBPUSD=X", "GBP/USD", "FOREX"),
            "JPY": ("USDJPY=X", "USD/JPY", "FOREX"),
            "USDJPY": ("USDJPY=X", "USD/JPY", "FOREX"),
            "AUD": ("AUDUSD=X", "AUD/USD", "FOREX"),
            "CAD": ("USDCAD=X", "USD/CAD", "FOREX"),
            "CHF": ("USDCHF=X", "USD/CHF", "FOREX"),
            "DXY": ("DX-Y.NYB", "US Dollar Index", "INDEX"),
            "SPX": ("^GSPC", "S&P 500", "INDEX"),
            "SPY": ("^GSPC", "S&P 500", "INDEX"),
            "DOW": ("^DJI", "Dow Jones", "INDEX"),
            "NASDAQ": ("^IXIC", "NASDAQ Composite", "INDEX"),
            "VIX": ("^VIX", "CBOE Volatility Index", "INDEX"),
        }

        q = query.strip().upper()
        results = []

        if q in SEARCH_ALIASES:
            ticker, name, qtype = SEARCH_ALIASES[q]
            results.append({"ticker": ticker, "name": name, "type": qtype, "exchange": ""})
            return results

        for alias, (ticker, name, qtype) in SEARCH_ALIASES.items():
            if alias.startswith(q) or q in alias:
                results.append({"ticker": ticker, "name": name, "type": qtype, "exchange": ""})

        try:
            search = yf.Ticker(q)
            info = search.info or {}
            if info.get("shortName"):
                results.append({
                    "ticker": q,
                    "name": info.get("shortName", q),
                    "type": info.get("quoteType", "EQUITY"),
                    "exchange": info.get("exchange", ""),
                })
        except Exception:
            pass

        return results[:10]
