# AI Agent Workflow — Market Research

## Role

The AI agent acts as a **Market Research Assistant**: it answers natural-language questions about markets using real data and returns concise, actionable insights.

## Tools Available to the Agent

1. **get_market_overview()**  
   Returns: indices (e.g. S&P 500, Nasdaq), daily change %, brief sentiment.

2. **get_top_movers(direction: "gainers" | "losers", limit: int)**  
   Returns: list of symbols with price change and volume.

3. **get_quote(symbol: str)**  
   Returns: price, change, volume, high/low for one ticker.

4. **get_news(symbol: str | null, limit: int)**  
   If symbol is null, returns general market news; otherwise news for that ticker.

5. **get_asset_summary(symbol: str)**  
   Returns: key stats (PE, market cap, 52w high/low), recent performance, and a short text summary (can be LLM-generated or template).

6. **get_technical_context(symbol: str)**  
   Returns: simple technical context (e.g. above/below 50-day MA, RSI bucket, recent trend).

## Workflow (Single Turn)

1. User sends message (e.g. "Why is the market down today?").
2. Backend optionally does lightweight intent/symbol extraction (or delegates to LLM).
3. Agent decides which tools to call (e.g. get_market_overview, get_top_movers("losers"), get_news(null)).
4. Backend runs tool calls, gets JSON results.
5. Backend builds a prompt:
   - System: "You are a market research assistant. Use the following data to answer the user. Be concise and cite numbers."
   - Context: tool results as structured text/JSON.
   - User message.
6. LLM returns final answer; backend streams or returns it to the client.

## Multi-Turn (Chat Session)

- Previous messages (user + assistant) are stored and sent as conversation history.
- Each new user message can trigger new tool calls; context from tools is appended for that turn only.
- Session stored in PostgreSQL (chat_sessions, chat_messages).

## Strategy Generation Workflow

1. User clicks "Generate Trading Strategy" (optionally selects symbol).
2. Backend fetches: OHLCV for symbol, basic technicals, recent news.
3. Prompt to LLM: "Given this data, suggest a simple trading rule (e.g. MA crossover, RSI oversold). Output in a structured format: type, params, description."
4. Backend parses response into strategy type + params, then runs backtest via Backtest Engine.
5. Response includes: strategy description, backtest metrics (win rate, Sharpe, drawdown, num_trades), and optionally equity curve for chart.

## Security / Cost

- Validate symbol and date ranges to avoid injection and runaway requests.
- Cache tool results (Redis) to reduce API and LLM calls.
- Rate limit per IP or per user for `/api/chat` and `/api/strategies/generate`.
