"""
Dexter-style autonomous financial research agent.

Mirrors virattt/dexter's architecture:
- Autonomous agent loop with iterative planning
- OpenAI function-calling for tool routing
- Financial Datasets API tools (income stmts, balance sheets, cash flow,
  key ratios, prices, news, insider trades, estimates, segments)
- Self-reflection & context management
- Streaming events (thinking, tool_start, tool_end, done)
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, AsyncGenerator

from openai import AsyncOpenAI

from config import get_settings
from services.financial_datasets import FinancialDatasetsClient
from services.news_search import search_news

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 8
MAX_TOOL_CALLS_PER_ITERATION = 5

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_income_statements",
            "description": "Fetch a company's income statements (revenue, expenses, net income, EPS). Use for profitability and growth analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol, e.g. AAPL"},
                    "period": {"type": "string", "enum": ["annual", "quarterly", "ttm"], "description": "Reporting period"},
                    "limit": {"type": "integer", "description": "Number of periods to return (default 4)", "default": 4},
                },
                "required": ["ticker", "period"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_balance_sheets",
            "description": "Fetch a company's balance sheets (assets, liabilities, equity). Use for financial health and solvency analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                    "period": {"type": "string", "enum": ["annual", "quarterly", "ttm"], "description": "Reporting period"},
                    "limit": {"type": "integer", "description": "Number of periods (default 4)", "default": 4},
                },
                "required": ["ticker", "period"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cash_flow_statements",
            "description": "Fetch cash flow statements (operating, investing, financing activities). Use for liquidity and free cash flow analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                    "period": {"type": "string", "enum": ["annual", "quarterly", "ttm"], "description": "Reporting period"},
                    "limit": {"type": "integer", "description": "Number of periods (default 4)", "default": 4},
                },
                "required": ["ticker", "period"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_financials",
            "description": "Fetch all three financial statements at once (income, balance sheet, cash flow). Use when you need comprehensive financial analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                    "period": {"type": "string", "enum": ["annual", "quarterly", "ttm"], "description": "Reporting period"},
                    "limit": {"type": "integer", "description": "Number of periods (default 4)", "default": 4},
                },
                "required": ["ticker", "period"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_key_ratios",
            "description": "Fetch key financial ratios and metrics (P/E, P/B, ROE, margins, EPS, market cap, dividend yield, enterprise value). Use for valuation and quick fundamental snapshot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                    "period": {"type": "string", "enum": ["annual", "quarterly", "ttm"], "description": "Reporting period"},
                    "limit": {"type": "integer", "description": "Number of periods (default 1)", "default": 1},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_analyst_estimates",
            "description": "Fetch analyst consensus estimates (revenue estimates, EPS estimates, price targets). Use for forward-looking analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                    "period": {"type": "string", "enum": ["annual", "quarterly"], "description": "Estimate period"},
                    "limit": {"type": "integer", "description": "Number of periods (default 4)", "default": 4},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Fetch current stock price snapshot (price, change, market cap, volume). Use for real-time pricing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_prices",
            "description": "Fetch historical stock prices over a date range. Use for price trends, chart data, and historical performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                    "start_date": {"type": "string", "description": "Start date in YYYY-MM-DD format"},
                    "end_date": {"type": "string", "description": "End date in YYYY-MM-DD format"},
                    "interval": {"type": "string", "enum": ["day", "week", "month"], "description": "Price interval", "default": "day"},
                    "limit": {"type": "integer", "description": "Max data points (default 252)", "default": 252},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_news",
            "description": "Fetch recent company news (equities only). Use for catalyst analysis, sentiment, and 'why did stock move' queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol (e.g. AAPL, NVDA)"},
                    "limit": {"type": "integer", "description": "Number of articles (default 10)", "default": 10},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_news_search",
            "description": "Fetch news for commodities (GC=F gold, SI=F silver, CL=F oil), forex (EURUSD=X), crypto (BTC-USD), indices (^GSPC). Use when get_company_news does not apply.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Ticker: GC=F, SI=F, CL=F, EURUSD=X, BTC-USD, ^GSPC, etc."},
                    "limit": {"type": "integer", "description": "Number of articles (default 10)", "default": 10},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_insider_trades",
            "description": "Fetch insider trading activity (buys, sells, officer transactions). Use for insider sentiment analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                    "limit": {"type": "integer", "description": "Number of trades (default 20)", "default": 20},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_segmented_revenues",
            "description": "Fetch revenue breakdown by business segment and geography. Use for understanding revenue concentration and diversification.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                    "period": {"type": "string", "enum": ["annual", "quarterly"], "description": "Reporting period"},
                    "limit": {"type": "integer", "description": "Number of periods (default 4)", "default": 4},
                },
                "required": ["ticker"],
            },
        },
    },
]

SYSTEM_PROMPT_TEMPLATE = """You are Dexter, an autonomous financial research agent integrated into the Gloomberg Terminal.
You think, plan, and execute deep financial research using real market data.

Current date: {current_date}

## Behavior

- Decompose complex financial questions into a research plan, then execute it step by step
- Use the available financial tools to gather real data — never fabricate numbers
- After gathering data, synthesize findings into a clear, data-backed answer
- For comparisons (e.g. "AAPL vs MSFT"), gather data for each company then compare
- For "why did X move" queries, combine price data with news
- Be thorough but efficient — use the minimum number of tool calls needed
- When you have sufficient data, write your final answer directly without calling more tools

## Tool Selection Guide

- Current price/quote → get_stock_price
- Historical prices over date range → get_stock_prices
- Revenue, earnings, profitability → get_income_statements
- Debt, assets, equity → get_balance_sheets
- Cash flow, free cash flow → get_cash_flow_statements
- All financials at once (comprehensive) → get_all_financials
- Valuation metrics (P/E, P/B, ROE, margins) → get_key_ratios
- Forward estimates, price targets → get_analyst_estimates
- News for stocks → get_company_news
- News for gold, silver, oil, forex, crypto, indices → get_news_search (use tickers: GC=F, SI=F, CL=F, EURUSD=X, BTC-USD, ^GSPC)
- Insider buying/selling → get_insider_trades
- Revenue segments & geography → get_segmented_revenues

## Response Format

- Use **bold** for emphasis, keep responses structured
- Use tables for comparative data (use markdown table syntax)
- Abbreviate: Rev, Op Inc, Net Inc, OCF, FCF, GM, OM, EPS
- Numbers compact: 102.5B not $102,466,000,000
- Cite specific data points from your research
- End with a clear conclusion or recommendation (bullish/bearish/neutral with reasoning)
"""


def _build_system_prompt() -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        current_date=datetime.now().strftime("%A, %B %d, %Y")
    )


class DexterAgent:
    """Autonomous research agent modeled after virattt/dexter."""

    def __init__(self, fin_client: FinancialDatasetsClient):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.fin = fin_client
        self.model = settings.openai_model

        async def _news_search(ticker: str, limit: int = 10) -> dict:
            articles = await search_news(ticker.upper(), limit=limit)
            return {"tool": "get_news_search", "ticker": ticker, "data": articles}

        self._tool_dispatch: dict[str, Any] = {
            "get_income_statements": self.fin.get_income_statements,
            "get_balance_sheets": self.fin.get_balance_sheets,
            "get_cash_flow_statements": self.fin.get_cash_flow_statements,
            "get_all_financials": self.fin.get_all_financials,
            "get_key_ratios": self.fin.get_key_ratios,
            "get_analyst_estimates": self.fin.get_analyst_estimates,
            "get_stock_price": self.fin.get_stock_price,
            "get_stock_prices": self.fin.get_stock_prices,
            "get_company_news": self.fin.get_company_news,
            "get_news_search": _news_search,
            "get_insider_trades": self.fin.get_insider_trades,
            "get_segmented_revenues": self.fin.get_segmented_revenues,
        }

    def is_available(self) -> bool:
        settings = get_settings()
        return bool(settings.openai_api_key) and self.fin.is_available()

    @staticmethod
    def _serialize_assistant_message(msg) -> dict[str, Any]:
        """Safely serialize an OpenAI ChatCompletionMessage for the messages list.
        model_dump() includes extra fields (refusal, audio, annotations, etc.)
        that the API rejects on round-trip. Build the dict manually."""
        out: dict[str, Any] = {"role": "assistant"}
        if msg.content:
            out["content"] = msg.content
        if msg.tool_calls:
            out["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        return out

    async def run(self, query: str) -> AsyncGenerator[dict[str, Any], None]:
        """
        Run the autonomous research loop. Yields SSE-compatible events:
          {"type": "thinking",   "content": "..."}
          {"type": "tool_start", "tool": "...", "args": {...}}
          {"type": "tool_end",   "tool": "...", "result_summary": "..."}
          {"type": "tool_error", "tool": "...", "error": "..."}
          {"type": "answer",     "content": "..."}
          {"type": "done",       "iterations": N, "tools_called": N, "time_ms": N}
        """
        start = time.time()
        total_tool_calls = 0
        iteration = 0

        system_prompt = _build_system_prompt()
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        for iteration in range(1, MAX_ITERATIONS + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    temperature=0.2,
                )
            except Exception as e:
                logger.error(f"Dexter LLM error at iteration {iteration}: {e}")
                yield {"type": "answer", "content": f"Research error: {e}"}
                break

            choice = response.choices[0]
            msg = choice.message

            if msg.content and msg.tool_calls:
                yield {"type": "thinking", "content": msg.content}

            if not msg.tool_calls:
                final_text = msg.content or "I was unable to complete the research."
                yield {"type": "answer", "content": final_text}
                break

            messages.append(self._serialize_assistant_message(msg))

            tool_results = []
            for tc in msg.tool_calls[:MAX_TOOL_CALLS_PER_ITERATION]:
                fn_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                yield {"type": "tool_start", "tool": fn_name, "args": args}

                handler = self._tool_dispatch.get(fn_name)
                if not handler:
                    err = f"Unknown tool: {fn_name}"
                    yield {"type": "tool_error", "tool": fn_name, "error": err}
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps({"error": err}),
                    })
                    continue

                try:
                    result = await handler(**args)
                    result_json = json.dumps(result, default=str)
                    total_tool_calls += 1

                    data = result.get("data", {})
                    if isinstance(data, list):
                        summary = f"{len(data)} records returned"
                    elif isinstance(data, dict):
                        summary = ", ".join(f"{k}: {v}" for k, v in list(data.items())[:5])
                    else:
                        summary = str(data)[:200]

                    yield {
                        "type": "tool_end",
                        "tool": fn_name,
                        "ticker": args.get("ticker", ""),
                        "result_summary": summary,
                    }

                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_json,
                    })
                except Exception as e:
                    logger.error(f"Dexter tool error {fn_name}: {e}")
                    yield {"type": "tool_error", "tool": fn_name, "error": str(e)}
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps({"error": str(e)}),
                    })

            messages.extend(tool_results)

            if iteration == MAX_ITERATIONS:
                messages.append({
                    "role": "user",
                    "content": "You have reached the maximum number of research iterations. "
                    "Please synthesize all the data you've gathered and provide your final answer now.",
                })
                try:
                    final_resp = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.2,
                    )
                    yield {"type": "answer", "content": final_resp.choices[0].message.content or "Research complete."}
                except Exception as e:
                    yield {"type": "answer", "content": f"Error generating final answer: {e}"}

        elapsed_ms = int((time.time() - start) * 1000)
        yield {
            "type": "done",
            "iterations": min(iteration, MAX_ITERATIONS),
            "tools_called": total_tool_calls,
            "time_ms": elapsed_ms,
        }
