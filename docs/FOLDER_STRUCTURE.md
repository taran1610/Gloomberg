# Gloomberg — Folder Structure

```
gloomberg/
├── docs/
│   ├── ARCHITECTURE.md      # System diagram, components, data flow
│   ├── DATABASE_SCHEMA.md   # PostgreSQL tables + Redis keys
│   ├── API_ENDPOINTS.md     # REST API reference
│   ├── AI_AGENT_WORKFLOW.md # How the research agent and tools work
│   └── FOLDER_STRUCTURE.md  # This file
│
├── backend/                  # Python FastAPI
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app, lifespan, CORS, routers
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── market.py     # /api/market/dashboard, indices, gainers, etc.
│   │   │   ├── assets.py    # /api/assets/{symbol}, quote, ohlcv, news
│   │   │   ├── chat.py      # /api/chat/sessions, messages, ask
│   │   │   ├── strategies.py # /api/strategies/generate
│   │   │   └── backtest.py  # POST /api/backtest
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py    # Settings from env
│   │   ├── engine/
│   │   │   ├── __init__.py
│   │   │   └── backtest.py  # run_ma_crossover, run_momentum, run_mean_reversion
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── market_data.py # yfinance + Redis cache
│   │       └── ai_agent.py   # LLM chat, asset summary, strategy generation
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
│
├── frontend/                 # Next.js 14 (App Router)
│   ├── src/
│   │   ├── app/
│   │   │   ├── globals.css
│   │   │   ├── layout.tsx   # Header nav, layout
│   │   │   ├── page.tsx     # Dashboard (market overview)
│   │   │   ├── chat/
│   │   │   │   └── page.tsx # AI research chat
│   │   │   ├── strategies/
│   │   │   │   └── page.tsx # Generate strategy + backtest
│   │   │   └── asset/
│   │   │       └── [symbol]/
│   │   │           └── page.tsx # Asset detail, chart, news, summary
│   │   └── lib/
│   │       └── api.ts       # fetchDashboard, fetchAsset, createChatSession, etc.
│   ├── package.json
│   ├── next.config.js       # rewrites to backend
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   └── Dockerfile
│
├── docker-compose.yml       # backend, redis, frontend
└── README.md
```
