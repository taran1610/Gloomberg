import asyncio
import logging

from fastapi import APIRouter, Depends, Query

from services.dummy_data import (
    DUMMY_INDICES,
    DUMMY_GAINERS,
    DUMMY_LOSERS,
    DUMMY_SECTORS,
    DUMMY_CRYPTO,
    DUMMY_COMMODITIES,
    DUMMY_FOREX,
)
from services.market_data import MarketDataService
from models.schemas import DashboardResponse, SearchResult

router = APIRouter(prefix="/api/market", tags=["market"])
logger = logging.getLogger(__name__)


def get_market_service():
    from main import get_market_data_service
    return get_market_data_service()


def get_ai_service():
    from main import get_ai_svc
    return get_ai_svc()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    svc = get_market_service()
    # Fetch all in parallel; if one fails, use empty default so dashboard still loads
    results = await asyncio.gather(
        svc.get_indices(),
        svc.get_gainers_losers(),
        svc.get_sectors(),
        svc.get_crypto(),
        svc.get_commodities(),
        svc.get_forex(),
        svc.get_vix(),
        return_exceptions=True,
    )
    def ok(i: int, default):
        r = results[i]
        if isinstance(r, Exception):
            logger.warning(f"Dashboard fetch {i} failed: {r}")
            return default
        return r

    indices = ok(0, DUMMY_INDICES)
    gl = ok(1, (DUMMY_GAINERS, DUMMY_LOSERS))
    gainers, losers = gl if isinstance(gl, tuple) else (DUMMY_GAINERS, DUMMY_LOSERS)
    sectors = ok(2, DUMMY_SECTORS)
    crypto = ok(3, DUMMY_CRYPTO)
    commodities = ok(4, DUMMY_COMMODITIES)
    forex = ok(5, DUMMY_FOREX)
    vix = ok(6, 15.5)
    # Ensure non-empty: use dummy when real data is empty
    if not indices:
        indices = DUMMY_INDICES
    if not gainers:
        gainers = DUMMY_GAINERS
    if not losers:
        losers = DUMMY_LOSERS
    if not sectors:
        sectors = DUMMY_SECTORS
    if not crypto:
        crypto = DUMMY_CRYPTO
    if not commodities:
        commodities = DUMMY_COMMODITIES
    if not forex:
        forex = DUMMY_FOREX

    ai_summary = None
    ai = get_ai_service()
    if ai._is_available():
        try:
            top_g = gainers[0] if gainers else None
            top_l = losers[0] if losers else None
            spx = next((i for i in indices if i.get("ticker") == "^GSPC"), None)
            vix_val = f"{vix:.1f}" if vix is not None else "N/A"
            parts = []
            if spx is not None:
                parts.append(f"S&P 500 {spx.get('change_pct', 0):.2f}%")
            if top_g:
                parts.append(f"Top gainer: {top_g['ticker']} {top_g['change_pct']:+.2f}%")
            if top_l:
                parts.append(f"Top loser: {top_l['ticker']} {top_l['change_pct']:+.2f}%")
            parts.append(f"VIX: {vix_val}")
            ctx = " | ".join(parts)
            resp = await ai.client.chat.completions.create(
                model=ai.settings.openai_model,
                messages=[{
                    "role": "system",
                    "content": "You are a market analyst. In 2-3 sentences, summarize today's market action: indices, risk sentiment (VIX), standout movers. Be concise and data-driven.",
                }, {"role": "user", "content": ctx}],
                max_tokens=150,
            )
            ai_summary = resp.choices[0].message.content
        except Exception:
            pass

    return DashboardResponse(
        indices=indices,
        gainers=gainers,
        losers=losers,
        sectors=sectors,
        crypto=crypto,
        commodities=commodities,
        forex=forex,
        vix=vix,
        ai_summary=ai_summary,
    )


@router.get("/search", response_model=list[SearchResult])
async def search_tickers(q: str = Query(..., min_length=1)):
    svc = get_market_service()
    return await svc.search_tickers(q)
