from fastapi import APIRouter, Depends, Query
from services.market_data import MarketDataService
from models.schemas import DashboardResponse, SearchResult

router = APIRouter(prefix="/api/market", tags=["market"])


def get_market_service():
    from main import get_market_data_service
    return get_market_data_service()


def get_ai_service():
    from main import get_ai_svc
    return get_ai_svc()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    svc = get_market_service()
    indices = await svc.get_indices()
    gainers, losers = await svc.get_gainers_losers()
    sectors = await svc.get_sectors()
    crypto = await svc.get_crypto()
    commodities = await svc.get_commodities()
    forex = await svc.get_forex()
    vix = await svc.get_vix()

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
