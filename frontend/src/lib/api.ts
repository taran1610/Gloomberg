const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("gloomberg_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
        ...options?.headers,
      },
    });
  } catch (e) {
    const err = e as Error & { cause?: { code?: string } };
    const isConnection =
      err instanceof Error &&
      (err.message === "fetch failed" ||
        err.message.includes("Failed to fetch") ||
        err.cause?.code === "ECONNREFUSED");
    const msg = isConnection
      ? "Cannot reach backend. Start the API (e.g. uvicorn in backend/) and ensure it runs on port 8000."
      : err instanceof Error
        ? err.message
        : "Network error";
    throw new Error(msg);
  }
  if (!res.ok) {
    if (res.status === 402) {
      const data = await res.json().catch(() => ({ detail: "Upgrade required" }));
      throw new UpgradeRequiredError(data.detail || "Upgrade required");
    }
    if (res.status === 401) {
      throw new AuthRequiredError("Authentication required");
    }
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  try {
    return await res.json();
  } catch {
    throw new Error("Invalid JSON from API");
  }
}

export class UpgradeRequiredError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "UpgradeRequiredError";
  }
}

export class AuthRequiredError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AuthRequiredError";
  }
}

export interface MarketIndex {
  name: string;
  ticker: string;
  price: number;
  change: number;
  change_pct: number;
}

export interface MarketMover {
  ticker: string;
  name: string;
  price: number;
  change_pct: number;
}

export interface SectorPerformance {
  name: string;
  change_pct: number;
}

export interface DashboardData {
  indices: MarketIndex[];
  gainers: MarketMover[];
  losers: MarketMover[];
  sectors: SectorPerformance[];
  crypto: MarketMover[];
  commodities: MarketMover[];
  forex: MarketMover[];
  vix: number | null;
  ai_summary?: string;
}

export interface CandleData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TechnicalIndicators {
  sma_20?: number;
  sma_50?: number;
  sma_200?: number;
  rsi?: number;
  macd?: number;
  macd_signal?: number;
  macd_histogram?: number;
  bb_upper?: number;
  bb_middle?: number;
  bb_lower?: number;
}

export interface AssetData {
  ticker: string;
  name: string;
  price: number;
  change: number;
  change_pct: number;
  market_cap?: number;
  pe_ratio?: number;
  volume?: number;
  avg_volume?: number;
  high_52w?: number;
  low_52w?: number;
  dividend_yield?: number;
  beta?: number;
  chart_data: CandleData[];
  indicators?: TechnicalIndicators;
  ai_summary?: string;
  news: { title: string; publisher: string; link: string; published: string }[];
  website?: string;
  city?: string;
  state?: string;
  sector?: string;
  industry?: string;
  full_time_employees?: number;
  forward_pe?: number;
  trailing_eps?: number;
  target_mean_price?: number;
  shares_outstanding?: number;
  float_shares?: number;
  price_to_book?: number;
  enterprise_value?: number;
  enterprise_to_revenue?: number;
  enterprise_to_ebitda?: number;
  peg_ratio?: number;
  price_to_sales?: number;
  day_open?: number;
  day_high?: number;
  day_low?: number;
  prev_close?: number;
  officers?: CompanyOfficer[];
  classification?: string;
  short_pct_float?: number;
  short_ratio?: number;
  fifty_two_week_change?: number;
  forward_eps?: number;
  asset_type?: string;
}

export interface InstitutionalHolder {
  holder: string;
  pct_held: number;
  shares: number;
  value?: number;
  pct_change?: number;
  date_reported?: string;
}

export interface OwnershipData {
  ticker: string;
  insiders_pct?: number;
  institutions_pct?: number;
  institutions_float_pct?: number;
  institutions_count?: number;
  institutional_holders: InstitutionalHolder[];
}

export interface InsiderTransaction {
  insider_name: string;
  title: string;
  trans_date: string;
  shares: number;
  price?: number;
  value?: number;
}

export interface InsiderTransactionsData {
  ticker: string;
  transactions: number;
  buys: number;
  sells: number;
  insider_transactions: InsiderTransaction[];
}

export interface DebtItem {
  label: string;
  value?: number;
}

export interface DebtData {
  ticker: string;
  fiscal_year: string;
  items: DebtItem[];
}

export interface CompanyOfficer {
  name: string;
  title: string;
  age?: number;
}

export interface RelIndexData {
  ticker: string;
  benchmark: string;
  benchmark_name: string;
  period: string;
  start_date: string;
  end_date: string;
  scatter: { x: number; y: number; date: string }[];
  regression_line: { x: number; y: number }[];
  equation: string;
  stats: {
    raw_beta: number;
    adjusted_beta: number;
    alpha: number;
    r_sq: number;
    r: number;
    std_dev_error: number;
    std_err_alpha: number;
    std_err_beta: number;
    t_test_alpha: number;
    significance: string;
    last_t_value: number;
    last_p_value: number;
    num_points: number;
    last_spread: number;
    last_ratio: number;
  };
  overlay: { date: string; ticker: number; benchmark: number }[];
}

export interface BacktestMetrics {
  total_return: number;
  annual_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  num_trades: number;
  profit_factor: number;
}

export interface EquityCurvePoint {
  date: string;
  value: number;
}

export interface TradeRecord {
  date: string;
  type: string;
  price: number;
  shares: number;
  pnl?: number;
}

export interface BacktestResult {
  ticker: string;
  strategy: string;
  metrics: BacktestMetrics;
  equity_curve: EquityCurvePoint[];
  trades: TradeRecord[];
}

export interface StrategyResult {
  strategy_name: string;
  description: string;
  rules: string[];
  backtest?: BacktestResult;
}

export async function fetchDashboard(): Promise<DashboardData> {
  return fetchJSON("/api/market/dashboard");
}

export async function fetchAsset(ticker: string): Promise<AssetData> {
  return fetchJSON(`/api/asset/${encodeURIComponent(ticker)}`);
}

export async function fetchHistory(
  ticker: string,
  period = "1y",
  interval = "1d"
): Promise<CandleData[]> {
  return fetchJSON(
    `/api/asset/${encodeURIComponent(ticker)}/history?period=${period}&interval=${interval}`
  );
}

export interface NewsEnhanced {
  articles: { title: string; publisher: string; link: string; published: string }[];
  ai_analysis: string | null;
  asset_type: string;
}

export async function fetchNewsEnhanced(ticker: string): Promise<NewsEnhanced> {
  return fetchJSON(`/api/asset/${encodeURIComponent(ticker)}/news`);
}

export async function fetchRelIndex(
  ticker: string,
  period = "1y"
): Promise<RelIndexData> {
  return fetchJSON(
    `/api/asset/${encodeURIComponent(ticker)}/rel-index?period=${period}`
  );
}

export async function fetchOwnership(ticker: string): Promise<OwnershipData> {
  return fetchJSON(`/api/asset/${encodeURIComponent(ticker)}/ownership`);
}

export async function fetchInsiderTransactions(ticker: string): Promise<InsiderTransactionsData> {
  return fetchJSON(`/api/asset/${encodeURIComponent(ticker)}/insider-transactions`);
}

export async function fetchDebt(ticker: string): Promise<DebtData> {
  return fetchJSON(`/api/asset/${encodeURIComponent(ticker)}/debt`);
}

export interface PeerRow {
  ticker: string;
  name: string;
  market_cap?: number | null;
  last_px?: number | null;
  chg_pct_1d?: number | null;
  chg_pct_1m?: number | null;
  rev_growth_1y?: number | null;
  eps_growth_1y?: number | null;
  pe?: number | null;
  roe?: number | null;
  dvd_yield?: number | null;
}

export interface RelValueData {
  ticker: string;
  period: string;
  chart_series: Record<string, { date: string; value: number }[]>;
  peers: PeerRow[];
  median: PeerRow;
}

export async function fetchRelValue(
  ticker: string,
  period = "1y"
): Promise<RelValueData> {
  return fetchJSON(
    `/api/asset/${encodeURIComponent(ticker)}/rel-value?period=${period}`
  );
}

export async function runBacktest(
  ticker: string,
  strategy: string,
  params: Record<string, number> = {},
  period = "2y"
): Promise<BacktestResult> {
  return fetchJSON("/api/strategy/backtest", {
    method: "POST",
    body: JSON.stringify({ ticker, strategy, params, period }),
  });
}

export async function generateStrategy(
  ticker: string,
  riskTolerance = "moderate"
): Promise<StrategyResult> {
  return fetchJSON("/api/strategy/generate", {
    method: "POST",
    body: JSON.stringify({ ticker, risk_tolerance: riskTolerance }),
  });
}

export async function* streamChat(
  message: string,
  context?: string
): AsyncGenerator<string, void, unknown> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ message, context }),
  });

  if (!res.ok) throw new Error(`Chat error: ${res.status}`);
  if (!res.body) throw new Error("No response body");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data: ")) continue;
      const data = trimmed.slice(6);
      if (data === "[DONE]") return;
      try {
        const parsed = JSON.parse(data);
        if (parsed.content) yield parsed.content;
      } catch {
        // skip malformed chunks
      }
    }
  }
}

// --- Deep Research (Dexter agent) ---

export interface ResearchEvent {
  type: "thinking" | "tool_start" | "tool_end" | "tool_error" | "answer" | "done";
  content?: string;
  tool?: string;
  args?: Record<string, unknown>;
  ticker?: string;
  result_summary?: string;
  error?: string;
  iterations?: number;
  tools_called?: number;
  time_ms?: number;
  limit_reached?: boolean;
}

export async function* streamResearch(
  message: string
): AsyncGenerator<ResearchEvent, void, unknown> {
  const res = await fetch(`${API_BASE}/api/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) throw new Error(`Research error: ${res.status}`);
  if (!res.body) throw new Error("No response body");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data: ")) continue;
      const data = trimmed.slice(6);
      if (data === "[DONE]") return;
      try {
        yield JSON.parse(data) as ResearchEvent;
      } catch {
        // skip malformed chunks
      }
    }
  }
}

export async function getResearchStatus(): Promise<{ available: boolean; provider: string }> {
  return fetchJSON("/api/research/status");
}

export async function createCheckout(): Promise<{ checkout_url: string }> {
  return fetchJSON("/api/billing/create-checkout", { method: "POST" });
}

export async function createPortalSession(): Promise<{ portal_url: string }> {
  return fetchJSON("/api/billing/portal", { method: "POST" });
}

export async function getBillingStatus(): Promise<{ configured: boolean }> {
  return fetchJSON("/api/billing/status");
}

export function formatNumber(num: number | undefined | null): string {
  if (num === undefined || num === null) return "N/A";
  if (Math.abs(num) >= 1e12) return `${(num / 1e12).toFixed(2)}T`;
  if (Math.abs(num) >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
  if (Math.abs(num) >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
  if (Math.abs(num) >= 1e3) return `${(num / 1e3).toFixed(2)}K`;
  return num.toFixed(2);
}

export function formatPercent(num: number | undefined | null): string {
  if (num === undefined || num === null) return "N/A";
  const sign = num >= 0 ? "+" : "";
  return `${sign}${num.toFixed(2)}%`;
}
