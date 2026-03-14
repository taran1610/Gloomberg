"""Asset API: quote, OHLCV, news, full summary."""
from typing import Optional

from fastapi import APIRouter, Request, HTTPException

router = APIRouter()


@router.get("/{symbol}/quote")
async def get_quote(symbol: str, request: Request):
    svc = request.app.state.market_data
    out = await svc.get_quote(symbol)
    if not out:
        raise HTTPException(status_code=404, detail="Quote not found")
    return out


@router.get("/{symbol}/ohlcv")
async def get_ohlcv(
    symbol: str,
    request: Request,
    interval: str = "1d",
    period: str = "1y",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    svc = request.app.state.market_data
    out = await svc.get_ohlcv(
        symbol=symbol,
        interval=interval,
        start_date=start_date,
        end_date=end_date,
        period=period,
    )
    return out


@router.get("/{symbol}/news")
async def get_news(symbol: str, request: Request, limit: int = 10):
    svc = request.app.state.market_data
    return await svc.get_news(symbol=symbol, limit=limit)


@router.get("/{symbol}")
async def get_asset(symbol: str, request: Request, include_summary: bool = False):
    """Full asset view: quote, stats, news. Optionally AI summary."""
    svc = request.app.state.market_data
    quote = await svc.get_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail="Asset not found")
    news = await svc.get_news(symbol=symbol, limit=5)
    ohlcv = await svc.get_ohlcv(symbol=symbol, period="3mo")
    summary = None
    if include_summary and hasattr(request.app.state, "ai_agent"):
        summary = await request.app.state.ai_agent.get_asset_summary(symbol, quote, ohlcv, news)
    return {
        "symbol": symbol.upper(),
        "quote": quote,
        "news": news,
        "ohlcv": ohlcv,
        "summary": summary,
    }
