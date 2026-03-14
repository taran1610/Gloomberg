# Gloomberg — API Endpoints

Base URL: `http://localhost:8000` (FastAPI).

## Market & Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/market/dashboard` | Global indices, top gainers/losers, sectors, crypto, volatility |
| GET | `/api/market/indices` | List global indices (e.g. ^GSPC, ^IXIC) |
| GET | `/api/market/gainers` | Top gainers (stocks) |
| GET | `/api/market/losers` | Top losers (stocks) |
| GET | `/api/market/sectors` | Sector performance |
| GET | `/api/market/crypto` | Major crypto quotes |

## Assets

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/assets/{symbol}` | Full asset view: quote, stats, news, optional AI summary |
| GET | `/api/assets/{symbol}/quote` | Current quote |
| GET | `/api/assets/{symbol}/ohlcv` | OHLCV series (query: interval, start_date, end_date) |
| GET | `/api/assets/{symbol}/news` | Recent news |
| GET | `/api/assets/{symbol}/summary` | AI-generated summary (optional) |

## AI Chat (Research Assistant)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/sessions` | Create chat session |
| GET | `/api/chat/sessions/{session_id}` | Get session + messages |
| POST | `/api/chat/sessions/{session_id}/messages` | Send user message, return assistant reply |
| POST | `/api/chat/ask` | One-off ask (no session): body `{ "message": "..." }` |

## Strategies & Backtest

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/strategies/generate` | AI generates a strategy; body `{ "symbol": "AAPL" }` |
| POST | `/api/backtest` | Run backtest; body: symbol, strategy_type, params, start_date, end_date |
| GET | `/api/backtest/{run_id}` | Get backtest result by id |

## Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Liveness |
