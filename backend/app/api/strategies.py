"""Strategies API: generate strategy (AI). Use /api/backtest to run backtest."""
from typing import Any

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter()


class GenerateOut(BaseModel):
    strategy: Any
    symbol: str


@router.post("/generate", response_model=GenerateOut)
async def generate_strategy(request: Request, symbol: str = "AAPL"):
    """AI suggests a trading strategy for the symbol."""
    agent = getattr(request.app.state, "ai_agent", None)
    if not agent:
        return GenerateOut(
            strategy={
                "type": "ma_crossover",
                "params": {"fast_period": 10, "slow_period": 30},
                "description": "Moving average crossover (default). Set OPENAI_API_KEY for AI-generated strategies.",
            },
            symbol=symbol,
        )
    out = await agent.generate_strategy(symbol)
    if out.get("error"):
        raise HTTPException(status_code=400, detail=out["error"])
    return GenerateOut(strategy=out["strategy"], symbol=out["symbol"])
