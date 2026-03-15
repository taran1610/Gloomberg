import re

import yfinance as yf
from fastapi import APIRouter, Path, Query

from services.technical_analysis import compute_indicators
from models.schemas import (
    AssetResponse, CandleData, InstitutionalHolder, OwnershipResponse,
    InsiderTransaction, InsiderTransactionsResponse,
    DebtResponse, DebtItem, CompanyOfficer,
)

router = APIRouter(prefix="/api/asset", tags=["assets"])

COMMODITY_TICKERS = {
    "GC=F": "Gold", "SI=F": "Silver", "CL=F": "Crude Oil WTI",
    "BZ=F": "Brent Crude", "NG=F": "Natural Gas", "HG=F": "Copper",
    "PL=F": "Platinum", "PA=F": "Palladium", "ZW=F": "Wheat",
    "ZC=F": "Corn", "ZS=F": "Soybeans",
}

FOREX_TICKERS = {
    "EURUSD=X": "EUR/USD", "GBPUSD=X": "GBP/USD", "USDJPY=X": "USD/JPY",
    "AUDUSD=X": "AUD/USD", "USDCAD=X": "USD/CAD", "USDCHF=X": "USD/CHF",
    "NZDUSD=X": "NZD/USD", "EURGBP=X": "EUR/GBP", "EURJPY=X": "EUR/JPY",
    "GBPJPY=X": "GBP/JPY", "DX-Y.NYB": "US Dollar Index",
}

INDEX_TICKERS = {
    "^GSPC": "S&P 500", "^DJI": "Dow Jones", "^IXIC": "NASDAQ",
    "^RUT": "Russell 2000", "^FTSE": "FTSE 100", "^N225": "Nikkei 225",
    "^VIX": "VIX",
}


def classify_ticker(ticker: str) -> str:
    t = ticker.upper()
    if t in COMMODITY_TICKERS or t.endswith("=F"):
        return "Commodity"
    if t in FOREX_TICKERS or t.endswith("=X"):
        return "Forex"
    if t in INDEX_TICKERS or t.startswith("^"):
        return "Index"
    if t.endswith("-USD") or t.endswith("-USDT"):
        return "Crypto"
    return "Equity"


def get_market_service():
    from main import get_market_data_service
    return get_market_data_service()


def get_ai_service():
    from main import get_ai_svc
    return get_ai_svc()


def _get_fin_client():
    from main import fin_client
    return fin_client


@router.get("/{ticker}/history")
async def get_history(
    ticker: str = Path(...),
    period: str = Query("1y"),
    interval: str = Query("1d"),
):
    svc = get_market_service()
    return await svc.get_history(ticker.upper(), period, interval)


@router.get("/{ticker}/ownership", response_model=OwnershipResponse)
async def get_ownership(ticker: str = Path(...)):
    svc = get_market_service()
    raw = await svc.get_ownership(ticker.upper())
    holders = [InstitutionalHolder(**h) for h in raw.get("institutional_holders", [])]
    return OwnershipResponse(
        ticker=raw["ticker"],
        shares_outstanding=raw.get("shares_outstanding"),
        insiders_pct=raw.get("insiders_pct"),
        institutions_pct=raw.get("institutions_pct"),
        institutions_float_pct=raw.get("institutions_float_pct"),
        institutions_count=raw.get("institutions_count"),
        institutional_holders=holders,
    )


@router.get("/{ticker}/insider-transactions", response_model=InsiderTransactionsResponse)
async def get_insider_transactions(ticker: str = Path(...)):
    svc = get_market_service()
    raw = await svc.get_insider_transactions(ticker.upper())
    txns = [InsiderTransaction(**t) for t in raw.get("insider_transactions", [])]
    return InsiderTransactionsResponse(
        ticker=raw["ticker"],
        transactions=raw.get("transactions", 0),
        buys=raw.get("buys", 0),
        sells=raw.get("sells", 0),
        insider_transactions=txns,
    )


@router.get("/{ticker}/debt", response_model=DebtResponse)
async def get_debt(ticker: str = Path(...)):
    svc = get_market_service()
    raw = await svc.get_debt_data(ticker.upper())
    items = [DebtItem(**i) for i in raw.get("items", [])]
    return DebtResponse(
        ticker=raw["ticker"],
        fiscal_year=raw.get("fiscal_year", ""),
        items=items,
    )


@router.get("/{ticker}/rel-index")
async def get_rel_index(
    ticker: str = Path(...),
    period: str = Query("1y"),
):
    from services.correlation import get_rel_index_data
    return get_rel_index_data(ticker.upper(), period)


@router.get("/{ticker}/rel-value")
async def get_rel_value(
    ticker: str = Path(...),
    period: str = Query("1y"),
):
    from services.rel_value import get_rel_value_data
    return get_rel_value_data(ticker.upper(), period)


@router.get("/{ticker}/news")
async def get_news_enhanced(ticker: str = Path(...)):
    """Fetch news: FD API (equity) / yfinance / Google News RSS, with AI analysis."""
    from services.news_search import search_news

    ticker = ticker.upper()
    asset_type = classify_ticker(ticker)
    articles: list[dict] = []

    # Equity: Financial Datasets API first
    fc = _get_fin_client()
    if fc and asset_type == "Equity":
        try:
            clean = re.sub(r"[^A-Z]", "", ticker)
            fd_result = await fc.get_company_news(clean)
            for item in (fd_result.get("data", []) if isinstance(fd_result, dict) else [])[:15]:
                articles.append({
                    "title": item.get("title", ""),
                    "publisher": item.get("source", item.get("publisher", "")),
                    "link": item.get("url", item.get("link", "")),
                    "published": item.get("date", item.get("published", "")),
                })
        except Exception:
            pass

    # Fallback: yfinance (works for some commodities/forex)
    if not articles:
        svc = get_market_service()
        articles = await svc.get_news(ticker)

    # Fallback: Google News RSS for commodities, forex, crypto, indices
    if not articles:
        articles = await search_news(ticker, limit=15)

    # AI News Agent: always analyze when we have headlines
    ai_analysis = None
    ai = get_ai_service()
    if articles and ai._is_available():
        headlines = "\n".join(f"- {a['title']} ({a.get('publisher', '')})" for a in articles[:10])
        try:
            resp = await ai.client.chat.completions.create(
                model=ai.settings.openai_model,
                messages=[{
                    "role": "system",
                    "content": (
                        "You are a senior financial news analyst. Analyze the following headlines "
                        f"for {ticker} ({asset_type}) and provide: 1) Overall sentiment (Bullish/Bearish/Neutral), "
                        "2) Key themes in 2-3 bullets, 3) A brief market impact assessment. "
                        "Be concise, professional, and data-driven. Use plain text, no markdown."
                    ),
                }, {"role": "user", "content": headlines}],
                max_tokens=300,
            )
            ai_analysis = resp.choices[0].message.content
        except Exception:
            pass

    return {"articles": articles, "ai_analysis": ai_analysis, "asset_type": asset_type}


@router.get("/{ticker}", response_model=AssetResponse)
async def get_asset(ticker: str = Path(...)):
    ticker = ticker.upper()
    asset_type = classify_ticker(ticker)
    svc = get_market_service()
    ai = get_ai_service()

    asset_data = await svc.get_asset(ticker)
    history = await svc.get_history(ticker, period="1y", interval="1d")

    news: list[dict] = []
    fc = _get_fin_client()
    if fc and asset_type == "Equity":
        try:
            clean = re.sub(r"[^A-Z]", "", ticker)
            fd_result = await fc.get_company_news(clean)
            for item in (fd_result.get("data", []) if isinstance(fd_result, dict) else [])[:10]:
                news.append({
                    "title": item.get("title", ""),
                    "publisher": item.get("source", item.get("publisher", "")),
                    "link": item.get("url", item.get("link", "")),
                    "published": item.get("date", item.get("published", "")),
                })
        except Exception:
            pass
    if not news:
        news = await svc.get_news(ticker)
    if not news:
        from services.news_search import search_news
        news = await search_news(ticker, limit=10)

    indicators = {}
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if not df.empty:
            indicators = compute_indicators(df)
    except Exception:
        pass

    ai_summary = await ai.analyze_asset(ticker, asset_data, indicators, asset_type)

    chart_data = [CandleData(**c) for c in history]

    officers_raw = asset_data.get("officers", [])
    officers = [CompanyOfficer(**o) for o in officers_raw] if officers_raw else []

    return AssetResponse(
        ticker=asset_data.get("ticker", ticker),
        name=asset_data.get("name", ticker),
        price=asset_data.get("price", 0),
        change=asset_data.get("change", 0),
        change_pct=asset_data.get("change_pct", 0),
        market_cap=asset_data.get("market_cap"),
        pe_ratio=asset_data.get("pe_ratio"),
        volume=asset_data.get("volume"),
        avg_volume=asset_data.get("avg_volume"),
        high_52w=asset_data.get("high_52w"),
        low_52w=asset_data.get("low_52w"),
        dividend_yield=asset_data.get("dividend_yield"),
        beta=asset_data.get("beta"),
        chart_data=chart_data,
        indicators=indicators if indicators else None,
        ai_summary=ai_summary,
        news=news,
        website=asset_data.get("website"),
        city=asset_data.get("city"),
        state=asset_data.get("state"),
        sector=asset_data.get("sector"),
        industry=asset_data.get("industry"),
        full_time_employees=asset_data.get("full_time_employees"),
        forward_pe=asset_data.get("forward_pe"),
        trailing_eps=asset_data.get("trailing_eps"),
        target_mean_price=asset_data.get("target_mean_price"),
        shares_outstanding=asset_data.get("shares_outstanding"),
        float_shares=asset_data.get("float_shares"),
        price_to_book=asset_data.get("price_to_book"),
        enterprise_value=asset_data.get("enterprise_value"),
        enterprise_to_revenue=asset_data.get("enterprise_to_revenue"),
        enterprise_to_ebitda=asset_data.get("enterprise_to_ebitda"),
        peg_ratio=asset_data.get("peg_ratio"),
        price_to_sales=asset_data.get("price_to_sales"),
        day_open=asset_data.get("day_open"),
        day_high=asset_data.get("day_high"),
        day_low=asset_data.get("day_low"),
        prev_close=asset_data.get("prev_close"),
        officers=officers,
        classification=asset_data.get("classification"),
        short_pct_float=asset_data.get("short_pct_float"),
        short_ratio=asset_data.get("short_ratio"),
        fifty_two_week_change=asset_data.get("fifty_two_week_change"),
        forward_eps=asset_data.get("forward_eps"),
        asset_type=asset_type,
    )
