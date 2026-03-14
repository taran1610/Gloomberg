"""Gloomberg Backend — FastAPI app entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import market, assets, chat, strategies, backtest
from app.core.config import settings
from app.services.market_data import get_market_data_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init services. Shutdown: cleanup."""
    from app.services.ai_agent import AIAgentService
    app.state.market_data = get_market_data_service()
    app.state.ai_agent = AIAgentService(app.state.market_data)
    yield
    if hasattr(app.state.market_data, "close"):
        await app.state.market_data.close()


app = FastAPI(
    title="Gloomberg API",
    description="AI-powered financial research terminal for retail traders",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market.router, prefix="/api/market", tags=["market"])
app.include_router(assets.router, prefix="/api/assets", tags=["assets"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])


@app.get("/health")
async def health():
    return {"status": "ok"}
