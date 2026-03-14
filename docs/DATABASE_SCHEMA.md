# Gloomberg — Database Schema (PostgreSQL)

## Tables (MVP)

### 1. users (optional for MVP; can add later)
- id, email, created_at

### 2. chat_sessions
Stores AI chat sessions for continuity.

| Column      | Type         | Description        |
|------------|--------------|--------------------|
| id         | UUID PK      | Session id         |
| user_id    | UUID FK null | Optional           |
| title      | VARCHAR(255) | First message hint |
| created_at | TIMESTAMPTZ  |                    |
| updated_at | TIMESTAMPTZ  |                    |

### 3. chat_messages
| Column       | Type         | Description |
|-------------|--------------|-------------|
| id          | UUID PK      |             |
| session_id  | UUID FK      |             |
| role        | VARCHAR(20)  | user, assistant, system |
| content     | TEXT         |             |
| created_at  | TIMESTAMPTZ  |             |

### 4. strategies
Saved/user-submitted strategies for backtesting.

| Column      | Type         | Description |
|------------|--------------|-------------|
| id         | UUID PK      |             |
| user_id    | UUID FK null | Optional    |
| name       | VARCHAR(255) |             |
| symbol     | VARCHAR(20)  | e.g. AAPL   |
| type       | VARCHAR(50)  | ma_crossover, momentum, mean_reversion |
| params     | JSONB        | Strategy parameters |
| created_at | TIMESTAMPTZ  |             |

### 5. backtest_runs
Results of backtest executions.

| Column        | Type         | Description |
|---------------|--------------|-------------|
| id            | UUID PK      |             |
| strategy_id   | UUID FK      |             |
| symbol        | VARCHAR(20)  |             |
| start_date    | DATE         |             |
| end_date      | DATE         |             |
| initial_capital| NUMERIC(18,2)|             |
| final_equity  | NUMERIC(18,2)|             |
| total_return_pct | NUMERIC(10,4) |         |
| sharpe_ratio  | NUMERIC(10,4)|             |
| max_drawdown_pct | NUMERIC(10,4)|          |
| win_rate_pct  | NUMERIC(10,4)|             |
| num_trades    | INTEGER      |             |
| equity_curve  | JSONB        | Array of {date, equity} |
| trades        | JSONB        | Array of trade objects |
| created_at    | TIMESTAMPTZ  |             |

## SQL (create tables)

```sql
-- Run in order

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NULL,
    title VARCHAR(255) DEFAULT 'New chat',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);

CREATE TABLE IF NOT EXISTS strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NULL,
    name VARCHAR(255) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    type VARCHAR(50) NOT NULL,
    params JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS backtest_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID NULL REFERENCES strategies(id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital NUMERIC(18,2) NOT NULL,
    final_equity NUMERIC(18,2) NOT NULL,
    total_return_pct NUMERIC(10,4) NOT NULL,
    sharpe_ratio NUMERIC(10,4),
    max_drawdown_pct NUMERIC(10,4),
    win_rate_pct NUMERIC(10,4),
    num_trades INTEGER NOT NULL DEFAULT 0,
    equity_curve JSONB,
    trades JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_backtest_runs_strategy ON backtest_runs(strategy_id);
```

## Redis Keys (convention)

- `market:dashboard` — JSON, TTL 60s  
- `quote:{symbol}` — JSON, TTL 30s  
- `ohlcv:{symbol}:{interval}` — JSON, TTL 300s  
- `news:{symbol}` — JSON, TTL 600s  
