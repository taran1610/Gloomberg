"""Market data service: quotes, indices, gainers, losers, sectors, crypto. Uses yfinance + Redis cache."""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
import yfinance as yf

from app.core.config import settings


class MarketDataService:
    """Fetch and cache market data. Primary source: yfinance."""

    CACHE_TTL = 60  # seconds for dashboard
    QUOTE_TTL = 30
    OHLCV_TTL = 300

    def __init__(self) -> None:
        self._redis: Optional[redis.Redis] = None
        self._redis_url = settings.REDIS_URL

    async def _get_redis(self) -> Optional[redis.Redis]:
        if self._redis is None:
            try:
                self._redis = redis.from_url(self._redis_url, decode_responses=True)
            except Exception:
                pass
        return self._redis

    async def _get_cached(self, key: str) -> Optional[Any]:
        r = await self._get_redis()
        if not r:
            return None
        try:
            raw = await r.get(key)
            return json.loads(raw) if raw else None
        except Exception:
            return None

    async def _set_cached(self, key: str, value: Any, ttl: int) -> None:
        r = await self._get_redis()
        if not r:
            return
        try:
            await r.set(key, json.dumps(value, default=str), ex=ttl)
        except Exception:
            pass

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    # --- Dashboard ---

    async def get_dashboard(self) -> Dict[str, Any]:
        """Aggregate data for homepage: indices, gainers, losers, sectors, crypto."""
        cache_key = "market:dashboard"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        indices = await self._fetch_indices()
        gainers = await self._fetch_movers("gainers")
        losers = await self._fetch_movers("losers")
        sectors = await self._fetch_sectors()
        crypto = await self._fetch_crypto()

        out = {
            "indices": indices,
            "gainers": gainers,
            "losers": losers,
            "sectors": sectors,
            "crypto": crypto,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }
        await self._set_cached(cache_key, out, self.CACHE_TTL)
        return out

    async def _fetch_indices(self) -> List[Dict[str, Any]]:
        symbols = ["^GSPC", "^IXIC", "^DJI", "^RUT", "^VIX"]
        result = []
        for s in symbols:
            q = await self.get_quote(s)
            if q:
                result.append({"symbol": s, **q})
        return result

    async def _fetch_movers(self, direction: str) -> List[Dict[str, Any]]:
        """Use yfinance screener or predefined list + sort by change."""
        # yfinance doesn't have a direct "gainers" API; use a small universe and sort
        symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
            "JPM", "V", "JNJ", "WMT", "PG", "MA", "HD", "DIS", "ADBE", "NFLX",
        ]
        quotes = []
        for s in symbols:
            q = await self.get_quote(s)
            if q and q.get("regularMarketChange") is not None:
                quotes.append({"symbol": s, **q})
        quotes.sort(key=lambda x: x.get("regularMarketChange", 0) or 0, reverse=(direction == "gainers"))
        return quotes[:10]

    async def _fetch_sectors(self) -> List[Dict[str, Any]]:
        # Sector ETFs as proxy
        etfs = ["XLK", "XLF", "XLV", "XLE", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE"]
        result = []
        for s in etfs:
            q = await self.get_quote(s)
            if q:
                result.append({"symbol": s, **q})
        return result

    async def _fetch_crypto(self) -> List[Dict[str, Any]]:
        symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD"]
        result = []
        for s in symbols:
            q = await self.get_quote(s)
            if q:
                result.append({"symbol": s, **q})
        return result

    # --- Quote ---

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        cache_key = f"quote:{symbol.upper()}"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        try:
            t = yf.Ticker(symbol)
            info = t.info
            hist = t.history(period="5d")
            if hist.empty:
                # Build from info only
                price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose")
                prev = info.get("previousClose") or price
                change = (price - prev) if (price and prev) else None
                change_pct = (change / prev * 100) if (prev and change is not None) else None
            else:
                last = hist.iloc[-1]
                prev = hist.iloc[-2]["Close"] if len(hist) > 1 else last["Close"]
                price = float(last["Close"])
                change = float(last["Close"] - prev)
                change_pct = float(change / prev * 100) if prev else None

            out = {
                "symbol": symbol.upper(),
                "price": price,
                "regularMarketChange": change,
                "regularMarketChangePercent": change_pct,
                "regularMarketVolume": info.get("volume") or (int(hist["Volume"].iloc[-1]) if not hist.empty else None),
                "marketCap": info.get("marketCap"),
                "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
                "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
                "shortName": info.get("shortName") or symbol,
            }
            await self._set_cached(cache_key, out, self.QUOTE_TTL)
            return out
        except Exception:
            return None

    # --- OHLCV ---

    async def get_ohlcv(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1y",
    ) -> List[Dict[str, Any]]:
        cache_key = f"ohlcv:{symbol.upper()}:{interval}:{period}"
        if start_date and end_date:
            cache_key = f"ohlcv:{symbol.upper()}:{interval}:{start_date}:{end_date}"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        try:
            t = yf.Ticker(symbol)
            if start_date and end_date:
                df = t.history(start=start_date, end=end_date, interval=interval)
            else:
                df = t.history(period=period, interval=interval)
            if df.empty:
                return []
            df = df.reset_index()
            df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
            out = df[["Date", "Open", "High", "Low", "Close", "Volume"]].rename(
                columns={"Date": "date", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}
            ).to_dict(orient="records")
            for r in out:
                r["open"] = float(r["open"])
                r["high"] = float(r["high"])
                r["low"] = float(r["low"])
                r["close"] = float(r["close"])
                r["volume"] = int(r["volume"])
            await self._set_cached(cache_key, out, self.OHLCV_TTL)
            return out
        except Exception:
            return []

    # --- News ---

    async def get_news(self, symbol: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        cache_key = f"news:{symbol or 'market'}:{limit}"
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        try:
            if symbol:
                t = yf.Ticker(symbol)
                news = t.news or []
            else:
                # General market: use a broad ticker
                t = yf.Ticker("^GSPC")
                news = t.news or []
            out = []
            for n in news[:limit]:
                out.append({
                    "title": n.get("title", ""),
                    "publisher": n.get("publisher", ""),
                    "link": n.get("link", ""),
                    "published": n.get("providerPublishTime"),
                })
            await self._set_cached(cache_key, out, 600)
            return out
        except Exception:
            return []


def get_market_data_service() -> MarketDataService:
    return MarketDataService()
