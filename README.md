# GLOOMBERG

**AI-Powered Financial Research Terminal for Retail Traders**

A Bloomberg Terminal-inspired platform that combines real-time market data, technical analysis, AI-powered insights, and strategy backtesting — built for individual traders who want institutional-grade tools without the $24,000/year price tag.

---

## Features

- **Market Dashboard** — Global indices, sector heatmap, top gainers/losers, crypto markets, VIX volatility tracker
- **AI Chat** — Ask questions about markets, get AI-powered analysis with streaming responses
- **Asset Analysis** — Deep dive into any ticker with candlestick charts, technical indicators (RSI, MACD, Bollinger Bands, SMAs), key stats, news, and AI-generated summaries
- **Strategy Lab** — Backtest trading strategies (MA crossover, RSI momentum, Bollinger mean reversion) with full performance metrics
- **AI Strategy Generator** — Let AI analyze an asset and generate optimized trading rules with automatic backtesting

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│                  FRONTEND                         │
│            Next.js + TailwindCSS                  │
│     TradingView Charts (lightweight-charts)       │
└──────────────────┬───────────────────────────────┘
                   │ HTTP / SSE
┌──────────────────▼───────────────────────────────┐
│                 BACKEND                           │
│              Python + FastAPI                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ Market   │ │ AI       │ │ Strategy Engine   │  │
│  │ Data Svc │ │ Service  │ │ + Backtester      │  │
│  └─────┬────┘ └────┬─────┘ └────────┬─────────┘  │
│        │           │                │             │
│  ┌─────▼────┐ ┌────▼─────┐ ┌───────▼──────────┐  │
│  │ yfinance │ │ OpenAI   │ │ pandas + ta-lib   │  │
│  └──────────┘ └──────────┘ └──────────────────┘  │
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────┐
│              INFRASTRUCTURE                       │
│         Redis (cache)  +  PostgreSQL (storage)    │
└──────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer       | Technology                          |
| ----------- | ----------------------------------- |
| Frontend    | Next.js 15, React 19, TailwindCSS   |
| Charts      | TradingView lightweight-charts      |
| Backend     | Python 3.12, FastAPI                |
| AI          | OpenAI API (GPT-4o-mini)            |
| Market Data | Yahoo Finance (yfinance)            |
| Cache       | Redis                               |
| Database    | PostgreSQL                          |
| Deployment  | Docker Compose                      |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis (optional, for caching)
- Docker & Docker Compose (optional, for containerized setup)

### Option 1: Run with Docker (Recommended)

```bash
# Clone and enter the project
cd gloomberg

# Copy environment file
cp .env.example .env

# (Optional) Add your OpenAI API key to .env for AI features
# OPENAI_API_KEY=sk-...

# Start all services
docker compose up --build
```

Open http://localhost:3000 in your browser.

### Option 2: Run Locally (Development)

**Backend:**

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Copy env file to backend directory
cp ../.env .env

# Start the API server
python main.py
```

The API runs at http://localhost:8000. Swagger docs at http://localhost:8000/docs.

**Frontend:**

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The dashboard runs at http://localhost:3000.

**Redis (optional):**

```bash
# macOS
brew install redis && redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:7-alpine
```

---

## API Endpoints

| Method | Endpoint                  | Description                    |
| ------ | ------------------------- | ------------------------------ |
| GET    | `/api/health`             | Health check                   |
| GET    | `/api/market/dashboard`   | Full market dashboard data     |
| GET    | `/api/market/search?q=`   | Search tickers                 |
| GET    | `/api/asset/{ticker}`     | Asset analysis with AI summary |
| GET    | `/api/asset/{ticker}/history` | Historical OHLCV data      |
| POST   | `/api/chat`               | AI chat (SSE streaming)        |
| POST   | `/api/strategy/backtest`  | Run a backtest                 |
| POST   | `/api/strategy/generate`  | AI-generated strategy          |

---

## Database Schema

```sql
CREATE TABLE saved_strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker VARCHAR(20) NOT NULL,
    strategy_type VARCHAR(50) NOT NULL,
    params JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE watchlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    tickers TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Project Structure

```
gloomberg/
├── backend/
│   ├── api/
│   │   ├── assets.py          # Asset analysis endpoints
│   │   ├── chat.py            # AI chat with SSE streaming
│   │   ├── market.py          # Dashboard & search endpoints
│   │   └── strategy.py        # Backtest & strategy generation
│   ├── models/
│   │   ├── database.py        # SQL schema definitions
│   │   └── schemas.py         # Pydantic request/response models
│   ├── services/
│   │   ├── ai_service.py      # OpenAI integration + fallbacks
│   │   ├── backtester.py      # Strategy backtesting engine
│   │   ├── market_data.py     # Yahoo Finance data service
│   │   └── technical_analysis.py  # RSI, MACD, Bollinger, SMA
│   ├── config.py              # App configuration
│   ├── main.py                # FastAPI application entry point
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── asset/[ticker]/page.tsx   # Asset detail page
│   │   │   ├── chat/page.tsx             # AI chat interface
│   │   │   ├── strategy/page.tsx         # Strategy lab
│   │   │   ├── layout.tsx                # Root layout + sidebar
│   │   │   ├── page.tsx                  # Market dashboard
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── EquityCurve.tsx           # Backtest equity chart
│   │   │   ├── MarketHeatmap.tsx         # Sector performance heatmap
│   │   │   ├── PriceChart.tsx            # TradingView candlestick chart
│   │   │   └── Sidebar.tsx               # Navigation sidebar
│   │   └── lib/
│   │       └── api.ts                    # API client + types
│   ├── package.json
│   ├── tailwind.config.ts
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## AI Agent Workflow

The AI service operates in two modes:

**Online Mode** (with OpenAI API key):
1. User sends a question or requests analysis
2. System gathers relevant market data (prices, indicators, news)
3. Data is formatted into context and sent to GPT-4o-mini with specialized system prompts
4. Responses stream back via Server-Sent Events for real-time display

**Offline Mode** (no API key):
1. System generates rule-based analysis from market data
2. Technical indicators drive automated insights (RSI overbought/oversold, MA trend direction)
3. Strategy recommendations based on indicator values

**Specialized Prompts:**
- **Chat**: General market analyst persona with broad financial knowledge
- **Asset Analysis**: Focused technical + fundamental analysis with specific data context
- **Strategy Generation**: Quantitative strategist that outputs structured JSON trading rules

---

## Configuration

| Variable              | Default             | Description                      |
| --------------------- | ------------------- | -------------------------------- |
| `OPENAI_API_KEY`      | (empty)             | OpenAI API key for AI features   |
| `OPENAI_MODEL`        | `gpt-4o-mini`       | LLM model to use                 |
| `REDIS_URL`           | `redis://localhost:6379` | Redis connection URL        |
| `CACHE_TTL_DASHBOARD` | `300`               | Dashboard cache TTL (seconds)    |
| `CACHE_TTL_TICKER`    | `900`               | Ticker info cache TTL            |
| `CACHE_TTL_HISTORY`   | `3600`              | History data cache TTL           |

---

## License

MIT
