"""Backtest API: run backtest and get results."""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from app.engine.backtest import run_backtest

router = APIRouter()


class BacktestRequest(BaseModel):
    symbol: str = "AAPL"
    strategy_type: str = "ma_crossover"
    params: Optional[dict] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: float = 100_000.0


@router.post("")
async def execute_backtest(body: BacktestRequest, request: Request):
    """Run backtest. strategy_type: ma_crossover | momentum | mean_reversion."""
    svc = request.app.state.market_data
    start = body.start_date or "2023-01-01"
    end = body.end_date or datetime.utcnow().strftime("%Y-%m-%d")
    ohlcv = await svc.get_ohlcv(body.symbol, start_date=start, end_date=end, period="2y")
    if not ohlcv:
        raise HTTPException(status_code=400, detail="No OHLCV data for symbol and date range")
    result = run_backtest(
        strategy_type=body.strategy_type,
        ohlcv=ohlcv,
        symbol=body.symbol,
        params=body.params,
        initial_capital=body.initial_capital,
    )
    return {
        "symbol": result.symbol,
        "start_date": result.start_date,
        "end_date": result.end_date,
        "initial_capital": result.initial_capital,
        "final_equity": result.final_equity,
        "total_return_pct": result.total_return_pct,
        "sharpe_ratio": result.sharpe_ratio,
        "max_drawdown_pct": result.max_drawdown_pct,
        "win_rate_pct": result.win_rate_pct,
        "num_trades": result.num_trades,
        "equity_curve": result.equity_curve,
        "trades": result.trades,
    }


@router.get("/{run_id}")
async def get_backtest_run(run_id: str, request: Request):
    """Get backtest result by id. MVP: run_id not persisted; return 404 or use in-memory store."""
    raise HTTPException(status_code=501, detail="Backtest run persistence not implemented in MVP")
