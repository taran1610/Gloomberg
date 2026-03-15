from pydantic import BaseModel
from typing import Optional


class MarketIndex(BaseModel):
    name: str
    ticker: str
    price: float
    change: float
    change_pct: float


class MarketMover(BaseModel):
    ticker: str
    name: str
    price: float
    change_pct: float


class SectorPerformance(BaseModel):
    name: str
    change_pct: float


class DashboardResponse(BaseModel):
    indices: list[MarketIndex]
    gainers: list[MarketMover]
    losers: list[MarketMover]
    sectors: list[SectorPerformance]
    crypto: list[MarketMover]
    commodities: list[MarketMover] = []
    forex: list[MarketMover] = []
    vix: Optional[float] = None
    ai_summary: Optional[str] = None


class CandleData(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class TechnicalIndicators(BaseModel):
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None


class CompanyOfficer(BaseModel):
    name: str
    title: str
    age: Optional[int] = None


class AssetResponse(BaseModel):
    ticker: str
    name: str
    price: float
    change: float
    change_pct: float
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    volume: Optional[int] = None
    avg_volume: Optional[int] = None
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    chart_data: list[CandleData] = []
    indicators: Optional[TechnicalIndicators] = None
    ai_summary: Optional[str] = None
    news: list[dict] = []
    # Perplexity-style overview fields
    website: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    full_time_employees: Optional[int] = None
    forward_pe: Optional[float] = None
    trailing_eps: Optional[float] = None
    target_mean_price: Optional[float] = None
    shares_outstanding: Optional[int] = None
    float_shares: Optional[int] = None
    # REL VALUE (valuation)
    price_to_book: Optional[float] = None
    enterprise_value: Optional[float] = None
    enterprise_to_revenue: Optional[float] = None
    enterprise_to_ebitda: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_sales: Optional[float] = None
    # Day OHLC
    day_open: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    prev_close: Optional[float] = None
    # Management
    officers: list[CompanyOfficer] = []
    # Classification
    classification: Optional[str] = None
    # Short interest
    short_pct_float: Optional[float] = None
    short_ratio: Optional[float] = None
    # Returns
    fifty_two_week_change: Optional[float] = None
    # Est EPS
    forward_eps: Optional[float] = None
    # Asset classification type
    asset_type: str = "Equity"


class InstitutionalHolder(BaseModel):
    holder: str
    pct_held: float
    shares: int
    value: Optional[float] = None
    pct_change: Optional[float] = None
    date_reported: Optional[str] = None


class OwnershipResponse(BaseModel):
    ticker: str
    shares_outstanding: Optional[float] = None
    insiders_pct: Optional[float] = None
    institutions_pct: Optional[float] = None
    institutions_float_pct: Optional[float] = None
    institutions_count: Optional[int] = None
    institutional_holders: list[InstitutionalHolder] = []


class InsiderTransaction(BaseModel):
    insider_name: str
    title: str = ""
    trans_date: str = ""
    shares: int = 0
    price: Optional[float] = None
    value: Optional[float] = None


class InsiderTransactionsResponse(BaseModel):
    ticker: str
    transactions: int = 0
    buys: int = 0
    sells: int = 0
    insider_transactions: list[InsiderTransaction] = []


class DebtItem(BaseModel):
    label: str
    value: Optional[float] = None


class DebtResponse(BaseModel):
    ticker: str
    fiscal_year: str = ""
    items: list[DebtItem] = []


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None


class ChatChunk(BaseModel):
    content: str


class BacktestRequest(BaseModel):
    ticker: str
    strategy: str  # ma_crossover, momentum, mean_reversion
    params: dict = {}
    period: str = "2y"


class TradeRecord(BaseModel):
    date: str
    type: str  # BUY or SELL
    price: float
    shares: float
    pnl: Optional[float] = None


class BacktestMetrics(BaseModel):
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    num_trades: int
    profit_factor: float


class EquityCurvePoint(BaseModel):
    date: str
    value: float


class BacktestResponse(BaseModel):
    ticker: str
    strategy: str
    metrics: BacktestMetrics
    equity_curve: list[EquityCurvePoint]
    trades: list[TradeRecord]


class StrategyGenerateRequest(BaseModel):
    ticker: str
    risk_tolerance: str = "moderate"  # conservative, moderate, aggressive


class StrategyGenerateResponse(BaseModel):
    strategy_name: str
    description: str
    rules: list[str]
    backtest: Optional[BacktestResponse] = None


class SearchResult(BaseModel):
    ticker: str
    name: str
    type: str
    exchange: str
