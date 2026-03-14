"""AI agent service: market research chat, asset summary, strategy generation."""
import json
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from app.core.config import settings


class AIAgentService:
    """LLM-backed agent with tools for market data."""

    def __init__(self, market_data_service: Any) -> None:
        self._market = market_data_service
        self._client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY or "sk-placeholder",
            base_url=settings.OPENAI_BASE_URL,
        ) if settings.OPENAI_API_KEY else None

    async def get_asset_summary(
        self,
        symbol: str,
        quote: Dict[str, Any],
        ohlcv: List[Dict],
        news: List[Dict],
    ) -> Optional[str]:
        """Generate a short AI summary for the asset."""
        if not self._client:
            return _template_summary(quote, ohlcv)
        try:
            prompt = _build_asset_summary_prompt(symbol, quote, ohlcv, news)
            r = await self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )
            return r.choices[0].message.content.strip()
        except Exception:
            return _template_summary(quote, ohlcv)

    async def ask(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """One-off question with optional tool context."""
        if not self._client:
            return await self._fallback_answer(message, context)
        try:
            # Fetch tools data based on message
            tool_results = await self._gather_tool_results(message)
            system = (
                "You are a concise financial research assistant for retail traders. "
                "Answer using the provided market data. Be brief and cite numbers when relevant."
            )
            user_content = message
            if tool_results:
                user_content = f"Market data:\n{json.dumps(tool_results, indent=2)}\n\nUser question: {message}"
            messages = [{"role": "system", "content": system}]
            if history:
                for h in history[-10:]:
                    messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": user_content})
            r = await self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                max_tokens=800,
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            return await self._fallback_answer(message, {"error": str(e)})

    async def _gather_tool_results(self, message: str) -> Dict[str, Any]:
        """Simple heuristic: always get overview; if symbol mentioned, get quote and news."""
        msg_lower = message.lower()
        out: Dict[str, Any] = {}
        dashboard = await self._market.get_dashboard()
        out["market_overview"] = {
            "indices": dashboard.get("indices", [])[:3],
            "gainers": dashboard.get("gainers", [])[:3],
            "losers": dashboard.get("losers", [])[:3],
        }
        # Try to find a ticker (crude: words in ALL CAPS or known tickers)
        known = ["aapl", "nvda", "tsla", "msft", "googl", "amzn", "meta", "btc", "eth", "spy", "qqq"]
        for t in known:
            if t in msg_lower:
                q = await self._market.get_quote(t.upper() if len(t) <= 5 else t)
                if q:
                    out["quote"] = q
                news = await self._market.get_news(t.upper() if len(t) <= 5 else t, limit=3)
                out["news"] = news
                break
        if "news" not in out:
            out["news"] = await self._market.get_news(None, limit=5)
        return out

    async def _fallback_answer(self, message: str, context: Optional[Dict] = None) -> str:
        """When LLM is not configured, return data-driven template."""
        dashboard = await self._market.get_dashboard()
        indices = dashboard.get("indices", [])
        gainers = dashboard.get("gainers", [])[:5]
        losers = dashboard.get("losers", [])[:5]
        lines = ["**Market snapshot**"]
        for i in indices:
            ch = i.get("regularMarketChangePercent") or 0
            lines.append(f"- {i.get('symbol', '')}: {ch:.2f}%")
        lines.append("\n**Top gainers** (sample)")
        for g in gainers:
            lines.append(f"- {g.get('symbol')}: {g.get('regularMarketChangePercent', 0):.2f}%")
        lines.append("\n**Top losers** (sample)")
        for l in losers:
            lines.append(f"- {l.get('symbol')}: {l.get('regularMarketChangePercent', 0):.2f}%")
        return "\n".join(lines)

    async def generate_strategy(self, symbol: str) -> Dict[str, Any]:
        """Suggest a simple strategy (type + params) for the symbol."""
        ohlcv = await self._market.get_ohlcv(symbol, period="1y")
        quote = await self._market.get_quote(symbol)
        if not ohlcv or not quote:
            return {"error": "Insufficient data", "strategy": None}
        if not self._client:
            return {
                "strategy": {
                    "type": "ma_crossover",
                    "params": {"fast_period": 10, "slow_period": 30},
                    "description": "Moving average crossover: buy when 10-day MA crosses above 30-day MA.",
                },
                "symbol": symbol,
            }
        try:
            prompt = f"""Given this asset's last year OHLCV (first 5 and last 5 rows) and quote, suggest ONE simple trading strategy.
Symbol: {symbol}. Quote: {json.dumps(quote)}.
OHLCV sample: {json.dumps(ohlcv[:5] + ohlcv[-5:])}
Respond with JSON only: {"type": "ma_crossover"|"momentum"|"mean_reversion", "params": {{}}, "description": "one sentence"}"""
            r = await self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )
            text = r.choices[0].message.content.strip()
            # Extract JSON
            if "```" in text:
                text = text.split("```")[1].replace("json", "").strip()
            data = json.loads(text)
            return {"strategy": data, "symbol": symbol}
        except Exception:
            return {
                "strategy": {
                    "type": "ma_crossover",
                    "params": {"fast_period": 10, "slow_period": 30},
                    "description": "Moving average crossover (default).",
                },
                "symbol": symbol,
            }


def _build_asset_summary_prompt(
    symbol: str,
    quote: Dict,
    ohlcv: List[Dict],
    news: List[Dict],
) -> str:
    recent = ohlcv[-30:] if len(ohlcv) >= 30 else ohlcv
    return f"""Write 2-3 short paragraphs summarizing this asset for a retail trader.
Symbol: {symbol}
Quote: {json.dumps(quote)}
Recent OHLCV (last 30): {json.dumps(recent[-5:])}
Recent news headlines: {[n.get('title') for n in news[:3]]}
Mention price, change%, and key stats if available. Be neutral and factual."""


def _template_summary(quote: Dict, ohlcv: List[Dict]) -> str:
    lines = [
        f"Price: {quote.get('price')}",
        f"Change: {quote.get('regularMarketChangePercent')}%",
        f"52w High/Low: {quote.get('fiftyTwoWeekHigh')} / {quote.get('fiftyTwoWeekLow')}",
    ]
    if ohlcv:
        last = ohlcv[-1]
        lines.append(f"Recent close: {last.get('close')} on {last.get('date')}")
    return " | ".join(str(x) for x in lines)
