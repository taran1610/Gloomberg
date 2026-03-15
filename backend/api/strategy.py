import asyncio
import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException

from services.ai_service import AIService
from services.market_data import MarketDataService
from services.backtester import run_backtest
from services.technical_analysis import compute_indicators
from services.auth import (
    get_current_user_optional,
    require_auth,
    check_limit,
    increment_usage,
)
from models.schemas import (
    BacktestRequest, BacktestResponse, BacktestMetrics,
    StrategyGenerateRequest, StrategyGenerateResponse,
)

router = APIRouter(prefix="/api/strategy", tags=["strategy"])


def get_market_service():
    from main import get_market_data_service
    return get_market_data_service()


def get_ai_service():
    from main import get_ai_svc
    return get_ai_svc()


@router.post("/generate", response_model=StrategyGenerateResponse)
async def generate_strategy(
    request: StrategyGenerateRequest,
    user: dict = Depends(require_auth),
):
    allowed, reason = check_limit(user["id"], "ai_strategy")
    if not allowed:
        raise HTTPException(status_code=402, detail=reason)

    allowed, reason = check_limit(user["id"], "ai_message")
    if not allowed:
        raise HTTPException(status_code=402, detail=reason)

    ticker = request.ticker.upper()
    svc = get_market_service()
    ai = get_ai_service()

    asset_data = await svc.get_asset(ticker)

    indicators = {}
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if not df.empty:
            indicators = compute_indicators(df)
    except Exception:
        pass

    strategy_info = await ai.generate_strategy(ticker, asset_data, indicators, request.risk_tolerance)

    rec_strategy = strategy_info.get("recommended_strategy", "ma_crossover")
    rec_params = strategy_info.get("params", {})

    backtest_result = await asyncio.to_thread(
        run_backtest, ticker, rec_strategy, rec_params, "2y"
    )

    backtest_response = None
    if "error" not in backtest_result:
        backtest_response = BacktestResponse(
            ticker=ticker,
            strategy=rec_strategy,
            metrics=BacktestMetrics(**backtest_result["metrics"]),
            equity_curve=backtest_result["equity_curve"],
            trades=backtest_result["trades"],
        )

    increment_usage(user["id"], "ai_messages")

    return StrategyGenerateResponse(
        strategy_name=strategy_info.get("strategy_name", f"Strategy for {ticker}"),
        description=strategy_info.get("description", ""),
        rules=strategy_info.get("rules", []),
        backtest=backtest_response,
    )


@router.post("/backtest", response_model=BacktestResponse)
async def backtest_strategy(
    request: BacktestRequest,
    user=Depends(get_current_user_optional),
):
    user_id = user["id"] if user else None

    allowed, reason = check_limit(user_id, "backtest")
    if not allowed:
        raise HTTPException(status_code=402, detail=reason)

    ticker = request.ticker.upper()
    result = await asyncio.to_thread(
        run_backtest, ticker, request.strategy, request.params or {}, request.period
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    if user_id:
        increment_usage(user_id, "backtests")

    return BacktestResponse(
        ticker=ticker,
        strategy=request.strategy,
        metrics=BacktestMetrics(**result["metrics"]),
        equity_curve=result["equity_curve"],
        trades=result["trades"],
    )
