import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis import asyncio as aioredis

from config import get_settings
from services.market_data import MarketDataService
from services.ai_service import AIService
from services.financial_datasets import FinancialDatasetsClient
from services.dexter_agent import DexterAgent
from api.market import router as market_router
from api.assets import router as assets_router
from api.chat import router as chat_router
from api.strategy import router as strategy_router
from api.auth import router as auth_router
from api.billing import router as billing_router
from api.research import router as research_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Reduce yfinance noise when Yahoo rate limits (429) - we use akshare fallback
logging.getLogger("yfinance").setLevel(logging.CRITICAL)

settings = get_settings()

redis_client = None
market_data_service = None
ai_service = None
fin_client = None
dexter_agent = None


def get_market_data_service() -> MarketDataService:
    return market_data_service


def get_ai_svc() -> AIService:
    return ai_service


def get_dexter_agent() -> DexterAgent | None:
    return dexter_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, market_data_service, ai_service, fin_client, dexter_agent

    settings = get_settings()

    try:
        redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await redis_client.ping()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.warning(f"Redis unavailable ({e}), running without cache")
        redis_client = None

    market_data_service = MarketDataService(redis=redis_client)
    ai_service = AIService()

    if ai_service._is_available():
        logger.info("AI service initialized with OpenAI")
    else:
        logger.info("AI service running in offline mode (no API key)")

    fin_client = FinancialDatasetsClient()
    if fin_client.is_available() and settings.openai_api_key:
        dexter_agent = DexterAgent(fin_client)
        logger.info(
            "Dexter deep research agent initialized (Financial Datasets API + OpenAI)"
        )
    else:
        dexter_agent = None
        missing = []
        if not settings.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if not fin_client.is_available():
            missing.append("FINANCIAL_DATASETS_API_KEY")
        logger.info(f"Dexter agent disabled (missing: {', '.join(missing)})")

    from services.edgar_helper import init_edgar
    init_edgar(settings.edgar_identity)

    yield

    if fin_client:
        await fin_client.close()
    if redis_client:
        await redis_client.close()


app = FastAPI(
    title="Gloomberg API",
    description="AI-powered financial research terminal",
    version="0.1.0",
    lifespan=lifespan,
)

cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

if settings.frontend_url and settings.frontend_url not in cors_origins:
    cors_origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(market_router)
app.include_router(assets_router)
app.include_router(chat_router)
app.include_router(research_router)
app.include_router(strategy_router)


@app.get("/")
async def root():
    return {
        "service": "Gloomberg API",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "redis": redis_client is not None,
        "ai": ai_service._is_available() if ai_service else False,
        "dexter": dexter_agent is not None and dexter_agent.is_available(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
