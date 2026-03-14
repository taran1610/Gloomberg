import json
import logging
from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI

from config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_CHAT = """You are Gloomberg AI, an expert financial market analyst and trading assistant.
You provide concise, data-driven insights about markets, stocks, and crypto.
When analyzing markets, consider: price action, technical indicators, fundamentals, macro trends, and sentiment.
Always be direct and actionable. Use specific numbers and data when available.
Format responses with clear structure using bullet points and headers when appropriate.
Never provide specific financial advice or guarantees. Remind users that past performance doesn't guarantee future results."""

SYSTEM_PROMPT_ASSET = """You are Gloomberg AI, analyzing a financial asset. Adapt your analysis to the asset type:

For STOCKS/EQUITIES: Price action, technical levels, fundamentals (P/E, growth), risk factors, outlook.
For COMMODITIES (Gold, Silver, Oil, etc.): Supply/demand dynamics, macro drivers (inflation, USD, rates), seasonal patterns, geopolitical risks, key price levels.
For FOREX pairs: Interest rate differentials, central bank policy, economic data drivers, key support/resistance, correlation with risk sentiment.
For CRYPTO: Network fundamentals, adoption metrics, regulatory landscape, correlation with risk assets, technical levels.
For INDICES: Sector rotation, breadth, macro backdrop, earnings season impact, key levels.

Keep it under 200 words. Be specific with numbers. Always include near-term outlook (bullish/bearish/neutral)."""

SYSTEM_PROMPT_STRATEGY = """You are Gloomberg AI, a quantitative trading strategist.
Given the asset data and analysis, generate a specific trading strategy with clear rules.
Output a JSON object with:
- strategy_name: short descriptive name
- description: 1-2 sentence description
- rules: array of specific trading rules
- recommended_strategy: one of "ma_crossover", "momentum", "mean_reversion"
- params: strategy parameters as a dict
Keep rules specific and actionable."""


class AIService:
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        if self.settings.openai_api_key:
            self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)

    def _is_available(self) -> bool:
        return self.client is not None

    async def stream_chat(self, message: str, context: Optional[str] = None) -> AsyncGenerator[str, None]:
        if not self._is_available():
            yield self._fallback_chat(message)
            return

        messages = [{"role": "system", "content": SYSTEM_PROMPT_CHAT}]
        if context:
            messages.append({"role": "system", "content": f"Market context:\n{context}"})
        messages.append({"role": "user", "content": message})

        try:
            stream = await self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=1000,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"AI chat error: {e}")
            yield f"I'm experiencing issues connecting to the AI service. Error: {str(e)}"

    async def analyze_asset(self, ticker: str, asset_data: dict, indicators: dict, asset_type: str = "Equity") -> str:
        if not self._is_available():
            return self._fallback_analysis(ticker, asset_data, indicators)

        context_lines = [
            f"Ticker: {ticker}",
            f"Asset Type: {asset_type}",
            f"Name: {asset_data.get('name', ticker)}",
            f"Price: ${asset_data.get('price', 'N/A')}",
            f"Change: {asset_data.get('change_pct', 'N/A')}%",
        ]
        if asset_data.get("market_cap"):
            context_lines.append(f"Market Cap: {asset_data['market_cap']}")
        if asset_data.get("pe_ratio"):
            context_lines.append(f"P/E Ratio: {asset_data['pe_ratio']}")
        if asset_data.get("sector"):
            context_lines.append(f"Sector: {asset_data['sector']}")
        context_lines.extend([
            f"52W High: {asset_data.get('high_52w', 'N/A')}",
            f"52W Low: {asset_data.get('low_52w', 'N/A')}",
            f"RSI: {indicators.get('rsi', 'N/A')}",
            f"MACD: {indicators.get('macd', 'N/A')}",
            f"SMA 20: {indicators.get('sma_20', 'N/A')}",
            f"SMA 50: {indicators.get('sma_50', 'N/A')}",
        ])
        context = "\n".join(context_lines)

        try:
            response = await self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_ASSET},
                    {"role": "user", "content": f"Analyze this {asset_type}: {ticker}\n{context}"},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI asset analysis error: {e}")
            return self._fallback_analysis(ticker, asset_data, indicators)

    async def generate_strategy(self, ticker: str, asset_data: dict, indicators: dict, risk_tolerance: str) -> dict:
        if not self._is_available():
            return self._fallback_strategy(ticker, indicators, risk_tolerance)

        context = f"""
Ticker: {ticker}
Price: ${asset_data.get('price', 'N/A')}
RSI: {indicators.get('rsi', 'N/A')}
MACD: {indicators.get('macd', 'N/A')}
SMA 20: {indicators.get('sma_20', 'N/A')}
SMA 50: {indicators.get('sma_50', 'N/A')}
Risk tolerance: {risk_tolerance}
"""
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_STRATEGY},
                    {"role": "user", "content": f"Generate a trading strategy for {ticker}:\n{context}"},
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"AI strategy error: {e}")
            return self._fallback_strategy(ticker, indicators, risk_tolerance)

    def _fallback_chat(self, message: str) -> str:
        return (
            "**Gloomberg AI** (running in offline mode — no API key configured)\n\n"
            "I can still help you explore market data, run backtests, and analyze assets using the tools in the sidebar. "
            "To enable AI-powered chat, add your `OPENAI_API_KEY` to the `.env` file.\n\n"
            f"Your question: *{message}*\n\n"
            "Try exploring the **Dashboard** for market overview, or search for a ticker to see detailed analysis."
        )

    def _fallback_analysis(self, ticker: str, data: dict, indicators: dict) -> str:
        price = data.get("price", 0)
        change = data.get("change_pct", 0)
        rsi = indicators.get("rsi")
        sma_20 = indicators.get("sma_20")
        sma_50 = indicators.get("sma_50")

        trend = "bullish" if change > 0 else "bearish" if change < 0 else "neutral"
        rsi_status = ""
        if rsi:
            if rsi > 70:
                rsi_status = "overbought"
            elif rsi < 30:
                rsi_status = "oversold"
            else:
                rsi_status = "neutral"

        ma_status = ""
        if sma_20 and sma_50:
            ma_status = "above" if sma_20 > sma_50 else "below"

        lines = [
            f"**{ticker}** is trading at **${price:.2f}** ({change:+.2f}% today).",
            f"The short-term trend appears **{trend}**.",
        ]
        if rsi:
            lines.append(f"RSI at **{rsi:.1f}** indicates {rsi_status} conditions.")
        if ma_status:
            lines.append(f"The 20-day SMA is {ma_status} the 50-day SMA.")
        lines.append("\n*AI-powered deep analysis available with OpenAI API key.*")
        return " ".join(lines)

    def _fallback_strategy(self, ticker: str, indicators: dict, risk_tolerance: str) -> dict:
        rsi = indicators.get("rsi", 50)
        strategy = "ma_crossover"
        params = {"fast_period": 20, "slow_period": 50}

        if rsi and rsi < 35:
            strategy = "mean_reversion"
            params = {}
        elif risk_tolerance == "aggressive":
            strategy = "momentum"
            params = {"rsi_buy": 25, "rsi_sell": 75}
        elif risk_tolerance == "conservative":
            strategy = "ma_crossover"
            params = {"fast_period": 50, "slow_period": 200}

        return {
            "strategy_name": f"{strategy.replace('_', ' ').title()} for {ticker}",
            "description": f"A {risk_tolerance} {strategy.replace('_', ' ')} strategy based on current market conditions.",
            "rules": [
                f"Apply {strategy.replace('_', ' ')} strategy on {ticker}",
                f"Risk tolerance: {risk_tolerance}",
                "Use 2-year historical data for backtesting",
                "Review performance metrics before trading",
            ],
            "recommended_strategy": strategy,
            "params": params,
        }
