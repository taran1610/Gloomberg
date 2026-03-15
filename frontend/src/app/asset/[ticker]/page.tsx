"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  fetchAsset,
  fetchHistory,
  fetchRelIndex,
  fetchRelValue,
  fetchOwnership,
  fetchInsiderTransactions,
  fetchDebt,
  fetchNewsEnhanced,
  getDummyOwnership,
  getDummyDebt,
  getDummyInsiderTransactions,
  formatNumber,
  formatPercent,
  type AssetData,
  type CandleData,
  type RelIndexData,
  type RelValueData,
  type OwnershipData,
  type InsiderTransactionsData,
  type DebtData,
  type NewsEnhanced,
} from "@/lib/api";
import { PriceChart, RelIndexChart, RelValueChart } from "@/components/Charts";

type Tab = "overview" | "chart" | "analysis" | "rel_index" | "rel_value" | "news" | "ownership" | "ai";

const PERIODS = [
  { value: "6mo", label: "6M" },
  { value: "ytd", label: "YTD" },
  { value: "1y", label: "1Y" },
  { value: "2y", label: "2Y" },
  { value: "5y", label: "5Y" },
];

export default function AssetPage() {
  const params = useParams();
  const ticker = (params.ticker as string).toUpperCase();
  const [data, setData] = useState<AssetData | null>(null);
  const [chartData, setChartData] = useState<CandleData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<Tab>("overview");
  const [chartPeriod, setChartPeriod] = useState("1y");
  const [relIndexData, setRelIndexData] = useState<RelIndexData | null>(null);
  const [relIndexPeriod, setRelIndexPeriod] = useState("1y");
  const [ownershipData, setOwnershipData] = useState<OwnershipData | null>(null);
  const [insiderData, setInsiderData] = useState<InsiderTransactionsData | null>(null);
  const [debtData, setDebtData] = useState<DebtData | null>(null);
  const [ownershipSubTab, setOwnershipSubTab] = useState<"current" | "insider" | "debt">("current");
  const [relValueData, setRelValueData] = useState<RelValueData | null>(null);
  const [relValuePeriod, setRelValuePeriod] = useState("1y");
  const [visiblePeerTickers, setVisiblePeerTickers] = useState<string[]>([]);

  useEffect(() => {
    setLoading(true);
    setError("");
    fetchAsset(ticker)
      .then((d) => {
        setData(d);
        setChartData(Array.isArray(d.chart_data) ? d.chart_data : []);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [ticker]);

  useEffect(() => {
    if (!ticker) return;
    fetchHistory(ticker, chartPeriod).then(setChartData).catch(() => {});
  }, [ticker, chartPeriod]);

  useEffect(() => {
    if (!ticker || tab !== "rel_index") return;
    fetchRelIndex(ticker, relIndexPeriod)
      .then(setRelIndexData)
      .catch(() => setRelIndexData(null));
  }, [ticker, tab, relIndexPeriod]);

  useEffect(() => {
    if (!ticker || tab !== "ownership") return;
    fetchOwnership(ticker)
      .then(setOwnershipData)
      .catch(() => setOwnershipData(getDummyOwnership(ticker)));
    fetchInsiderTransactions(ticker)
      .then(setInsiderData)
      .catch(() => setInsiderData(getDummyInsiderTransactions(ticker)));
    fetchDebt(ticker)
      .then(setDebtData)
      .catch(() => setDebtData(getDummyDebt(ticker)));
  }, [ticker, tab]);

  useEffect(() => {
    if (!ticker || tab !== "rel_value") return;
    setRelValueData(null);
    fetchRelValue(ticker, relValuePeriod)
      .then((d) => {
        setRelValueData(d);
        if (visiblePeerTickers.length === 0 && d.chart_series)
          setVisiblePeerTickers(Object.keys(d.chart_series));
      })
      .catch(() => setRelValueData(null));
  }, [ticker, tab, relValuePeriod]);

  useEffect(() => {
    if (relValueData?.chart_series && visiblePeerTickers.length === 0)
      setVisiblePeerTickers(Object.keys(relValueData.chart_series));
  }, [relValueData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-term-orange text-sm mb-1">LOADING {ticker}...</div>
          <div className="text-term-dim text-xxs">Fetching market data</div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-term-red text-sm mb-1">ERROR: {error || "ASSET NOT FOUND"}</div>
          <div className="text-term-dim text-xxs">Verify ticker symbol and backend connection</div>
        </div>
      </div>
    );
  }

  const pos = data.change_pct >= 0;
  const isEquity = !data.asset_type || data.asset_type === "Equity";
  const now = new Date();
  const timeStr = now.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit" });

  return (
    <div className="h-full flex flex-col">
      {/* ─── Ticker Status Bar ─── */}
      <div className="bg-term-bg border-b border-term-border px-3 py-1 flex items-center gap-2">
        <span className="text-term-orange font-bold text-base">{data.ticker}{data.asset_type === "Equity" ? " US" : ""}</span>
        <span className="text-term-white text-xxs">$</span>
        <span className={`text-xs ${pos ? "text-positive" : "text-negative"}`}>
          {pos ? "↑" : "↓"}
        </span>
        <span className={`text-2xl font-bold tabular-nums ${pos ? "text-positive" : "text-term-white"}`}>{data.price.toFixed(2)}</span>
        <span className={`text-sm font-bold tabular-nums ${pos ? "text-positive" : "text-negative"}`}>
          {pos ? "+" : ""}{data.change.toFixed(2)}
        </span>
        {data.prev_close != null && (
          <>
            <span className="text-term-dim text-xxs mx-1">│</span>
            <span className="text-term-muted text-xxs">F{data.prev_close.toFixed(2)} / {data.price.toFixed(2)}Q</span>
            <span className="text-term-muted text-xxs ml-1">1x1</span>
          </>
        )}
      </div>

      {/* ─── OHLC Detail Line ─── */}
      <div className="bg-term-panel border-b border-term-border px-3 py-0.5 flex items-center text-xxs">
        <span className="text-term-green">@</span>
        <span className="text-term-muted ml-1">At {timeStr} w</span>
        <span className="text-term-dim mx-2">│</span>
        <span className="text-term-muted">Vol</span>
        <span className="text-term-white ml-1 tabular-nums">{formatNumber(data.volume)}</span>
        {data.day_open != null && (
          <>
            <span className="text-term-dim mx-2">│</span>
            <span className="text-term-muted">O</span>
            <span className="text-term-white ml-1 tabular-nums">{data.day_open.toFixed(2)}F</span>
          </>
        )}
        {data.day_high != null && (
          <>
            <span className="text-term-muted ml-2">H</span>
            <span className="text-term-white ml-1 tabular-nums">{data.day_high.toFixed(2)}D</span>
          </>
        )}
        {data.day_low != null && (
          <>
            <span className="text-term-muted ml-2">L</span>
            <span className="text-term-white ml-1 tabular-nums">{data.day_low.toFixed(2)}Q</span>
          </>
        )}
        <div className="flex-1" />
        <span className="text-term-muted">Val</span>
        <span className="text-term-white ml-1 tabular-nums">{formatNumber(data.market_cap)}</span>
        <span className="text-term-green text-xs font-bold ml-2">OPEN</span>
      </div>

      {/* ─── Asset Tab Bar ─── */}
      <div className="h-6 bg-term-panel border-b border-term-border flex items-center px-1 gap-0.5">
        <span className="tab-active px-2 py-0.5 text-xxs flex-shrink-0">
          {data.ticker} {data.asset_type || "Equity"}
        </span>
        {(
          [
            { id: "overview", label: "OVERVIEW", key: "0", all: true },
            { id: "chart", label: "CHART", key: "1", all: true },
            { id: "analysis", label: "ANALYSIS", key: "2", all: true },
            { id: "rel_index", label: "REL INDEX", key: "3", all: true },
            { id: "rel_value", label: "REL VALUE", key: "4", all: false },
            { id: "news", label: "NEWS", key: "5", all: true },
            { id: "ownership", label: "OWNERSHIP", key: "6", all: false },
            { id: "ai", label: "AI RESEARCH", key: "7", all: true },
          ] as const
        )
          .filter(({ all }) => all || isEquity)
          .map(({ id, label, key }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`px-2 py-0.5 text-xxs transition-colors flex-shrink-0 ${
              tab === id ? "tab-active" : "tab-inactive"
            }`}
          >
            [{key}] {label}
          </button>
        ))}
        <div className="flex-1" />
        <span className="text-xxs text-term-dim pr-1 flex-shrink-0">
          {data.asset_type || "Equity"}
        </span>
      </div>

      {/* ─── Content ─── */}
      <div className="flex-1 overflow-auto">
        {tab === "overview" && <OverviewTab data={data} chartData={chartData} chartPeriod={chartPeriod} setChartPeriod={setChartPeriod} />}
        {tab === "chart" && <ChartTab data={data} chartData={chartData} chartPeriod={chartPeriod} setChartPeriod={setChartPeriod} />}
        {tab === "analysis" && <AnalysisTab data={data} />}
        {tab === "rel_index" && <RelIndexTab ticker={ticker} data={relIndexData} period={relIndexPeriod} setPeriod={setRelIndexPeriod} />}
        {tab === "rel_value" && (
          <RelValueTab
            ticker={ticker}
            data={data}
            relValueData={relValueData}
            relValuePeriod={relValuePeriod}
            setRelValuePeriod={setRelValuePeriod}
            visiblePeerTickers={visiblePeerTickers}
            setVisiblePeerTickers={setVisiblePeerTickers}
          />
        )}
        {tab === "news" && <NewsTab data={data} ticker={ticker} />}
        {tab === "ownership" && (
          <OwnershipTab
            ticker={ticker}
            data={ownershipData}
            insiderData={insiderData}
            debtData={debtData}
            subTab={ownershipSubTab}
            setSubTab={setOwnershipSubTab}
          />
        )}
        {tab === "ai" && <AITab data={data} />}
      </div>
    </div>
  );
}

/* ─── REL INDEX Tab ─── */
function RelIndexTab({
  ticker,
  data,
  period,
  setPeriod,
}: {
  ticker: string;
  data: RelIndexData | null;
  period: string;
  setPeriod: (p: string) => void;
}) {
  const PERIODS = ["6mo", "1y", "2y", "5y"];
  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-term-orange text-sm mb-1">LOADING REL INDEX...</div>
          <div className="text-term-dim text-xxs">Computing correlation vs S&P 500</div>
        </div>
      </div>
    );
  }
  if ("error" in data) {
    return (
      <div className="p-3 text-term-red text-xs">{String((data as { error?: string }).error)}</div>
    );
  }

  const s = data.stats;
  return (
    <div className="h-full flex flex-col overflow-auto">
      <div className="flex items-center gap-2 px-3 py-1 border-b border-term-border">
        <span className="text-xxs text-term-muted">Period:</span>
        {PERIODS.map((p) => (
          <button
            key={p}
            onClick={() => setPeriod(p)}
            className={`px-2 py-0.5 text-xxs ${
              period === p ? "bg-term-blue text-white font-bold" : "text-term-muted hover:text-term-white bg-term-surface"
            }`}
          >
            {p.toUpperCase()}
          </button>
        ))}
        <span className="text-xxs text-term-dim ml-2">WEEKLY</span>
      </div>
      <div className="flex-1 grid grid-cols-3 gap-0 min-h-0">
        <div className="col-span-2 p-2">
          <RelIndexChart data={data} height={320} />
        </div>
        <div className="border-l border-term-border overflow-auto">
          <div className="terminal-header">Y = {data.ticker} | X = {data.benchmark_name}</div>
          <table className="w-full">
            <tbody>
              {[
                ["Raw BETA", s.raw_beta.toFixed(3)],
                ["Adjusted BETA", s.adjusted_beta.toFixed(3)],
                ["ALPHA (Intercept)", s.alpha.toFixed(3)],
                ["R² (Correlation²)", s.r_sq.toFixed(3)],
                ["R (Correlation)", s.r.toFixed(3)],
                ["Std Dev of Error", s.std_dev_error.toFixed(3)],
                ["Std Error of ALPHA", s.std_err_alpha.toFixed(3)],
                ["Std Error of BETA", s.std_err_beta.toFixed(3)],
                ["t-Test", s.t_test_alpha.toFixed(3)],
                ["Significance", s.significance],
                ["Last T-Value", s.last_t_value.toFixed(3)],
                ["Last P-Value", s.last_p_value.toFixed(3)],
                ["Number of Points", String(s.num_points)],
                ["Last Spread", s.last_spread.toFixed(2)],
                ["Last Ratio", s.last_ratio.toFixed(3)],
              ].map(([label, value]) => (
                <tr key={label} className="border-b border-term-border/30">
                  <td className="py-0.5 px-2 text-xs text-term-muted">{label}</td>
                  <td className="py-0.5 px-2 text-xs text-right tabular-nums text-term-white font-bold">
                    {value}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ─── REL VALUE Tab ─── */
function RelValueTab({
  ticker,
  data,
  relValueData,
  relValuePeriod,
  setRelValuePeriod,
  visiblePeerTickers,
  setVisiblePeerTickers,
}: {
  ticker: string;
  data: AssetData;
  relValueData: RelValueData | null;
  relValuePeriod: string;
  setRelValuePeriod: (p: string) => void;
  visiblePeerTickers: string[];
  setVisiblePeerTickers: (t: string[]) => void;
}) {
  const PERIODS = ["3m", "6m", "1y", "2y", "5y"];
  const chartTickers = relValueData?.chart_series ? Object.keys(relValueData.chart_series) : [];

  const togglePeer = (t: string) => {
    if (visiblePeerTickers.includes(t))
      setVisiblePeerTickers(visiblePeerTickers.filter((x) => x !== t));
    else
      setVisiblePeerTickers([...visiblePeerTickers, t]);
  };

  if (!relValueData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-term-orange text-sm mb-1">LOADING REL VALUE...</div>
          <div className="text-term-dim text-xxs">Fetching peer comparison</div>
        </div>
      </div>
    );
  }

  const tableRows = [relValueData.median, ...relValueData.peers];
  const fmt = (v: number | null | undefined, pct = false) => {
    if (v == null) return "—";
    if (pct) return `${v >= 0 ? "" : ""}${v.toFixed(2)}%`;
    return v.toFixed(2);
  };
  const fmtCap = (v: number | null | undefined) => (v != null ? formatNumber(v) : "—");

  return (
    <div className="h-full flex flex-col overflow-auto">
      <div className="terminal-header border-b border-term-border">
        {data.ticker} US Equity | Relative Value
      </div>
      <div className="text-term-orange text-xs font-bold px-3 py-0.5">{data.ticker}</div>

      {/* Chart + period */}
      <div className="border-b border-term-border p-2">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xxs text-term-muted">Period:</span>
          <div className="flex gap-0.5">
            {PERIODS.map((p) => (
              <button
                key={p}
                onClick={() => setRelValuePeriod(p)}
                className={`px-2 py-0.5 text-xxs ${
                  relValuePeriod === p
                    ? "bg-term-orange text-term-black font-bold"
                    : "text-term-muted hover:text-term-white bg-term-surface"
                }`}
              >
                {p === "3m" ? "3M" : p === "6m" ? "6M" : p === "1y" ? "1Y" : p === "2y" ? "2Y" : "5Y"}
              </button>
            ))}
          </div>
        </div>
        <div className="min-h-[280px] border border-term-border bg-term-black">
          <RelValueChart
            data={relValueData}
            visibleTickers={visiblePeerTickers}
            height={280}
          />
        </div>
        <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1">
          {chartTickers.map((t) => (
            <label key={t} className="inline-flex items-center gap-1 cursor-pointer text-xxs">
              <input
                type="checkbox"
                checked={visiblePeerTickers.includes(t)}
                onChange={() => togglePeer(t)}
                className="rounded border-term-border"
              />
              <span className={t === ticker ? "text-term-orange font-bold" : "text-term-muted"}>
                {t}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Peer comparison table */}
      <div className="flex-1 overflow-auto">
        <div className="terminal-header border-b border-term-border">
          PEER COMPARISON (BI Peers)
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xxs min-w-[800px]">
            <thead>
              <tr className="text-term-dim uppercase border-b border-term-border bg-term-surface">
                <th className="text-left py-1 px-2 font-bold">Name</th>
                <th className="text-right py-1 px-2">Mkt Cap (USD)</th>
                <th className="text-right py-1 px-2">Last Px (USD)</th>
                <th className="text-right py-1 px-2">Chg Pct 1D</th>
                <th className="text-right py-1 px-2">Chg Pct 1M</th>
                <th className="text-right py-1 px-2">Rev - 1 Yr Gr:Y</th>
                <th className="text-right py-1 px-2">EPS - 1 Yr Gr:Y</th>
                <th className="text-right py-1 px-2">P/E</th>
                <th className="text-right py-1 px-2">ROE</th>
                <th className="text-right py-1 px-2">Dvd 12M Yld</th>
              </tr>
            </thead>
            <tbody>
              {tableRows.map((row, idx) => (
                <tr
                  key={row.ticker + idx}
                  className={`border-b border-term-border/50 ${
                    row.ticker === ticker ? "bg-term-orange/10" : row.ticker === "Median" ? "bg-term-surface/50" : ""
                  }`}
                >
                  <td className="py-0.5 px-2 font-bold text-term-white">
                    {row.ticker === "Median" ? "Median" : `${100 + idx}) ${row.name}`}
                  </td>
                  <td className="py-0.5 px-2 text-right tabular-nums text-term-white">{fmtCap(row.market_cap)}</td>
                  <td className="py-0.5 px-2 text-right tabular-nums text-term-white">{row.last_px != null ? row.last_px.toFixed(2) : "—"}</td>
                  <td className="py-0.5 px-2 text-right tabular-nums">
                    {row.chg_pct_1d != null ? (
                      <span className={row.chg_pct_1d >= 0 ? "text-positive" : "text-negative"}>{fmt(row.chg_pct_1d, true)}</span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="py-0.5 px-2 text-right tabular-nums">
                    {row.chg_pct_1m != null ? (
                      <span className={row.chg_pct_1m >= 0 ? "text-positive" : "text-negative"}>{fmt(row.chg_pct_1m, true)}</span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="py-0.5 px-2 text-right tabular-nums">
                    {row.rev_growth_1y != null ? (
                      <span className={row.rev_growth_1y >= 0 ? "text-positive" : "text-negative"}>{fmt(row.rev_growth_1y, true)}</span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="py-0.5 px-2 text-right tabular-nums">
                    {row.eps_growth_1y != null ? (
                      <span className={row.eps_growth_1y >= 0 ? "text-positive" : "text-negative"}>{fmt(row.eps_growth_1y, true)}</span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="py-0.5 px-2 text-right tabular-nums text-term-white">{row.pe != null ? row.pe.toFixed(2) : "—"}</td>
                  <td className="py-0.5 px-2 text-right tabular-nums">
                    {row.roe != null ? (
                      <span className={row.roe >= 0 ? "text-positive" : "text-negative"}>{fmt(row.roe, true)}</span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="py-0.5 px-2 text-right tabular-nums text-term-white">{row.dvd_yield != null ? fmt(row.dvd_yield, true) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ─── OWNERSHIP Tab ─── */
function OwnershipTab({
  ticker,
  data,
  insiderData,
  debtData,
  subTab,
  setSubTab,
}: {
  ticker: string;
  data: OwnershipData | null;
  insiderData: InsiderTransactionsData | null;
  debtData: DebtData | null;
  subTab: "current" | "insider" | "debt";
  setSubTab: (t: "current" | "insider" | "debt") => void;
}) {
  return (
    <div className="h-full flex flex-col overflow-auto">
      <div className="text-term-orange text-xs font-bold px-3 py-1 border-b border-term-border">
        {ticker}
      </div>

      {/* Sub-tab bar */}
      <div className="flex items-center gap-0 px-3 py-1 border-b border-term-border bg-term-panel">
        {([
          { id: "current" as const, label: "1) Current" },
          { id: "insider" as const, label: "2) Insider Transactions" },
          { id: "debt" as const, label: "3) Debt" },
        ]).map(({ id, label }) => (
          <button
            key={id}
            onClick={() => setSubTab(id)}
            className={`px-3 py-1 text-xs font-bold transition-colors ${
              subTab === id
                ? "bg-term-orange text-term-black"
                : "text-term-muted hover:text-term-white"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Sub-tab content */}
      <div className="flex-1 overflow-auto">
        {subTab === "current" && <OwnershipCurrentSubTab ticker={ticker} data={data} />}
        {subTab === "insider" && <OwnershipInsiderSubTab ticker={ticker} data={insiderData} />}
        {subTab === "debt" && <OwnershipDebtSubTab ticker={ticker} data={debtData} />}
      </div>
    </div>
  );
}

function OwnershipCurrentSubTab({ ticker, data }: { ticker: string; data: OwnershipData | null }) {
  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-term-orange text-sm">LOADING OWNERSHIP...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="px-3 py-1 text-xxs text-term-muted border-b border-term-border flex items-center gap-4">
        <span>Ticker <span className="text-term-orange font-bold">{ticker}</span></span>
        {data.shares_outstanding != null && (
          <span>Shrs Out <span className="text-term-white font-bold">{formatNumber(data.shares_outstanding)}</span></span>
        )}
        {data.institutions_pct != null && (
          <span>Inst % Out <span className="text-term-white font-bold">{data.institutions_pct.toFixed(2)}%</span></span>
        )}
        {data.institutions_count != null && (
          <span>Holders <span className="text-term-white font-bold">{data.institutions_count}</span></span>
        )}
        <span>Source <span className="text-term-white font-bold">13F/SEC EDGAR</span></span>
      </div>
      <table className="w-full text-xxs">
        <thead>
          <tr className="text-term-dim uppercase border-b border-term-border bg-term-surface">
            <th className="text-left py-1 px-3 w-8">#</th>
            <th className="text-left py-1 px-2">Holder Name</th>
            <th className="text-right py-1 px-3">Source</th>
          </tr>
        </thead>
        <tbody>
          {data.institutional_holders.length === 0 ? (
            <tr>
              <td colSpan={3} className="py-4 text-term-dim text-center text-xs">
                No institutional holders data available.
              </td>
            </tr>
          ) : (
            data.institutional_holders.map((h, i) => (
              <tr key={`${h.holder}-${i}`} className="border-b border-term-border/30 terminal-row">
                <td className="py-1 px-3 text-term-muted">{i + 1}</td>
                <td className="py-1 px-2 text-term-white font-bold">{h.holder.toUpperCase()}</td>
                <td className="py-1 px-3 text-right text-term-muted">13F</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function OwnershipInsiderSubTab({ ticker, data }: { ticker: string; data: InsiderTransactionsData | null }) {
  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-term-orange text-sm">LOADING INSIDER TRANSACTIONS...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="px-3 py-1 text-xxs text-term-muted border-b border-term-border flex items-center gap-4">
        <span>Ticker <span className="text-term-orange font-bold">{ticker}</span></span>
        <span>Transactions <span className="text-term-white font-bold">{data.transactions}</span></span>
        <span>Buys <span className="text-positive font-bold">{data.buys}</span></span>
        <span>Sells <span className="text-negative font-bold">{data.sells}</span></span>
      </div>
      <table className="w-full text-xxs">
        <thead>
          <tr className="text-term-dim uppercase border-b border-term-border bg-term-surface">
            <th className="text-left py-1 px-3 w-8">#</th>
            <th className="text-left py-1 px-2">Insider Name</th>
            <th className="text-left py-1 px-2">Title</th>
            <th className="text-left py-1 px-2">Trans Date</th>
            <th className="text-right py-1 px-2">Shares</th>
            <th className="text-right py-1 px-3">Price</th>
          </tr>
        </thead>
        <tbody>
          {data.insider_transactions.length === 0 ? (
            <tr>
              <td colSpan={6} className="py-4 text-term-dim text-center text-xs">
                No insider transaction data available.
              </td>
            </tr>
          ) : (
            data.insider_transactions.map((tx, i) => (
              <tr key={`${tx.insider_name}-${i}`} className="border-b border-term-border/30 terminal-row">
                <td className="py-1 px-3 text-term-muted">{i + 1}</td>
                <td className="py-1 px-2 text-term-white font-bold">{tx.insider_name}</td>
                <td className="py-1 px-2 text-term-muted">{tx.title}</td>
                <td className="py-1 px-2 text-term-white">{tx.trans_date}</td>
                <td className={`py-1 px-2 text-right tabular-nums font-bold ${tx.shares >= 0 ? "text-positive" : "text-negative"}`}>
                  {tx.shares.toLocaleString()}
                </td>
                <td className="py-1 px-3 text-right tabular-nums text-term-white">
                  {tx.price != null ? `$${tx.price.toFixed(0)}` : "—"}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function OwnershipDebtSubTab({ ticker, data }: { ticker: string; data: DebtData | null }) {
  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-term-orange text-sm">LOADING DEBT DATA...</div>
      </div>
    );
  }

  const fmtVal = (v: number | null | undefined, isRatio = false) => {
    if (v == null) return "—";
    if (isRatio) return `${v.toFixed(1)}%`;
    if (Math.abs(v) >= 1e12) return `$${(v / 1e12).toFixed(1)}T`;
    if (Math.abs(v) >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
    if (Math.abs(v) >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
    return `$${v.toFixed(0)}`;
  };

  const ratioLabels = ["Debt / Equity Ratio", "Debt / Assets Ratio", "Liabilities / Assets"];

  return (
    <div>
      <table className="w-full text-xs">
        <thead>
          <tr className="text-term-dim uppercase border-b border-term-border bg-term-surface text-xxs">
            <th className="text-left py-1 px-3 font-bold">Line Item</th>
            <th className="text-right py-1 px-3 font-bold">{data.fiscal_year || "Latest"}</th>
          </tr>
        </thead>
        <tbody>
          {data.items.length === 0 ? (
            <tr>
              <td colSpan={2} className="py-4 text-term-dim text-center text-xs">
                No debt data available.
              </td>
            </tr>
          ) : (
            data.items.map((item, i) => {
              const isRatio = ratioLabels.includes(item.label);
              const isBold = ["Total Liabilities", "Total Assets", "Shareholders' Equity"].includes(item.label);
              const isSection = i === 0 || i === 3 || i === 6 || i === 8;
              return (
                <tr
                  key={item.label}
                  className={`border-b border-term-border/30 ${isSection ? "mt-2" : ""}`}
                >
                  <td className={`py-1.5 px-3 ${isBold ? "text-term-orange font-bold" : "text-term-muted"}`}>
                    {item.label}
                  </td>
                  <td className="py-1.5 px-3 text-right tabular-nums text-term-white font-bold">
                    {fmtVal(item.value, isRatio)}
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}

/* ─── Overview Tab ─── */
function OverviewTab({
  data,
  chartData,
  chartPeriod,
  setChartPeriod,
}: {
  data: AssetData;
  chartData: CandleData[];
  chartPeriod: string;
  setChartPeriod: (p: string) => void;
}) {
  return (
    <div className="h-full flex flex-col">
      {/* Company Name + Classification */}
      <div className="px-3 py-1.5 border-b border-term-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="border border-term-border px-2 py-0.5">
            <span className="text-term-white text-sm font-bold">{data.ticker}</span>
          </div>
          <span className="text-term-white font-bold text-xl">{data.name?.toUpperCase()}</span>
        </div>
        {data.classification && (
          <span className="text-term-muted text-xxs">
            Classification <span className="text-term-white font-bold">{data.classification}</span>
          </span>
        )}
      </div>

      {/* AI Summary (Research Primer) */}
      {data.ai_summary && (
        <div className="px-3 py-1.5 border-b border-term-border">
          <div className="text-xxs text-term-orange font-bold mb-0.5">
            6) AI Research Primer | GLOOM &raquo;
          </div>
          <div className="text-xs text-term-text leading-relaxed line-clamp-3">
            {data.ai_summary}
          </div>
        </div>
      )}

      {/* Main 3-column Grid */}
      <div className="flex-1 grid grid-cols-3 min-h-0">
        {/* Left: Chart */}
        <div className="border-r border-term-border flex flex-col">
          <div className="terminal-header flex items-center justify-between">
            <span>8) Price Chart | GP &raquo;</span>
            <div className="flex items-center gap-0.5">
              {PERIODS.map((p) => (
                <button
                  key={p.value}
                  onClick={() => setChartPeriod(p.value)}
                  className={`px-1.5 py-px text-xxs ${
                    chartPeriod === p.value
                      ? "bg-term-blue text-white font-bold"
                      : "text-term-muted hover:text-term-white"
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
          <div className="flex-1 p-0.5">
            <PriceChart data={chartData} height={280} />
          </div>
          {/* Bottom price stats */}
          <div className="border-t border-term-border px-2 py-1 text-xxs space-y-0.5">
            <div className="flex justify-between">
              <span className="text-term-muted">Px/Chg 1D (USD)</span>
              <span className={data.change_pct >= 0 ? "text-positive" : "text-negative"}>
                ${data.price.toFixed(2)}/{data.change_pct >= 0 ? "+" : ""}{data.change_pct.toFixed(2)}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-term-muted">52 Wk H ({data.high_52w ? "USD" : ""})</span>
              <span className="text-term-white">${data.high_52w?.toFixed(2) ?? "N/A"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-term-muted">52 Wk L</span>
              <span className="text-term-white">${data.low_52w?.toFixed(2) ?? "N/A"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-term-muted">YTD Change/%</span>
              <span className="text-term-white">{formatPercent(data.change_pct)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-term-muted">Mkt Cap (USD)</span>
              <span className="text-term-white">{data.market_cap != null ? formatNumber(data.market_cap) : "N/A"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-term-muted">Shrs Out/Float</span>
              <span className="text-term-white">{data.shares_outstanding != null && data.float_shares != null
                ? `${formatNumber(data.shares_outstanding)}/${formatNumber(data.float_shares)}`
                : "N/A"}</span>
            </div>
            {data.short_pct_float != null && (
              <div className="flex justify-between">
                <span className="text-term-muted">SI/% of Float</span>
                <span className="text-term-white">{(data.short_pct_float * 100).toFixed(2)}%</span>
              </div>
            )}
            {data.short_ratio != null && (
              <div className="flex justify-between">
                <span className="text-term-muted">Days to Cover</span>
                <span className="text-term-white">{data.short_ratio.toFixed(1)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Middle: Estimates + Dividend */}
        <div className="border-r border-term-border flex flex-col min-h-0 overflow-auto">
          <div className="border-b border-term-border">
            <div className="terminal-header">9) Estimates | EE &raquo;</div>
            <table className="w-full">
              <tbody>
                {([
                  ["Date (E)", "2025/FY"],
                  ["P/E", data.pe_ratio?.toFixed(2) ?? "N/A"],
                  ["Est P/E", data.forward_pe?.toFixed(2) ?? "N/A"],
                  ["T12M EPS (USD)", data.trailing_eps?.toFixed(2) ?? "N/A"],
                  ["Est EPS", data.forward_eps?.toFixed(2) ?? "N/A"],
                  ["Est PEG", data.peg_ratio?.toFixed(2) ?? "N.A."],
                ] as const).map(([label, value]) => (
                  <tr key={label} className="border-b border-term-border/30">
                    <td className="py-0.5 px-2 text-xs text-term-muted">{label}</td>
                    <td className="py-0.5 px-2 text-xs text-right tabular-nums text-term-white font-bold">{value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="border-b border-term-border">
            <div className="terminal-header">12) Dividend | DVD &raquo;</div>
            <div className="px-2 py-1 text-xs">
              <div className="flex justify-between">
                <span className="text-term-muted">Ind Gross Yield</span>
                <span className="text-term-white font-bold">
                  {data.dividend_yield ? `${(data.dividend_yield * 100).toFixed(2)}%` : "N.A."}
                </span>
              </div>
              <div className="text-term-dim text-xxs mt-0.5">
                {data.dividend_yield ? "Cash dividend active" : "Cash dividend discontinued"}
              </div>
            </div>
          </div>

          {/* Returns + Beta */}
          <div className="px-2 py-1 text-xs space-y-1 border-b border-term-border">
            <div className="flex justify-between">
              <span className="text-term-muted">12M Tot Ret</span>
              <span className="text-term-white font-bold tabular-nums">
                {data.fifty_two_week_change != null ? `${(data.fifty_two_week_change * 100).toFixed(2)}%` : "N/A"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-term-muted">Beta vs SPX</span>
              <span className="text-term-white font-bold tabular-nums">
                {data.beta != null ? data.beta.toFixed(2) : "N/A"}
              </span>
            </div>
          </div>

          {/* Technicals summary */}
          <div className="flex-1 min-h-0 overflow-auto">
            <div className="terminal-header">11) Technicals | TA &raquo;</div>
            {data.indicators ? (
              <table className="w-full">
                <tbody>
                  {([
                    ["RSI (14)", data.indicators.rsi, data.indicators.rsi != null ? (data.indicators.rsi > 70 ? "text-term-red" : data.indicators.rsi < 30 ? "text-term-green" : "text-term-white") : "text-term-dim"],
                    ["MACD", data.indicators.macd, "text-term-white"],
                    ["SMA 20", data.indicators.sma_20, "text-term-white"],
                    ["SMA 50", data.indicators.sma_50, "text-term-white"],
                    ["SMA 200", data.indicators.sma_200, "text-term-white"],
                  ] as const).map(([label, value, color]) => (
                    <tr key={label} className="border-b border-term-border/30">
                      <td className="py-0.5 px-2 text-xs text-term-muted">{label}</td>
                      <td className={`py-0.5 px-2 text-xs text-right tabular-nums font-bold ${color}`}>
                        {value != null ? (value as number).toFixed(2) : "N/A"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-2 text-xxs text-term-dim">N/A</div>
            )}
          </div>
        </div>

        {/* Right: Corporate Info + Management */}
        <div className="flex flex-col min-h-0 overflow-auto">
          {/* Corporate Info */}
          <div className="border-b border-term-border">
            <div className="terminal-header">13) Corporate Info</div>
            <div className="px-2 py-1 text-xs space-y-0.5">
              {data.website && (
                <a href={data.website.startsWith("http") ? data.website : `https://${data.website}`} target="_blank" rel="noopener noreferrer" className="text-term-blue hover:underline block">
                  14) {data.website.replace(/^https?:\/\//, "")}
                </a>
              )}
              {(data.city || data.state) && (
                <div className="text-term-muted">
                  {[data.city, data.state, "US"].filter(Boolean).join(", ")}
                </div>
              )}
              {data.full_time_employees != null && (
                <div className="flex justify-between">
                  <span className="text-term-muted">Empls</span>
                  <span className="text-term-white font-bold">{data.full_time_employees.toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>

          {/* Management */}
          {data.officers && data.officers.length > 0 && (
            <div className="border-b border-term-border">
              <div className="terminal-header">15) Management | MGMT &raquo;</div>
              <div className="px-2 py-1 text-xs space-y-1">
                {data.officers.slice(0, 4).map((off, i) => (
                  <div key={off.name} className="flex justify-between">
                    <span className="text-term-muted">{16 + i}) {off.name}</span>
                    <span className="text-term-white text-xxs">{off.title}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* News Headlines (bottom of overview) */}
          {data.news && data.news.length > 0 && (
            <div className="flex-1 min-h-0 overflow-auto">
              <div className="terminal-header">Latest News</div>
              {data.news.slice(0, 8).map((article, i) => (
                <a
                  key={i}
                  href={article.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-start gap-1.5 px-2 py-1 border-b border-term-border/30 hover:bg-term-surface transition-colors"
                >
                  <span className="text-term-yellow text-xxs font-bold w-5 text-right flex-shrink-0">
                    {900 - i}
                  </span>
                  <span className="text-term-orange text-xxs font-bold flex-shrink-0 w-12 truncate">
                    {article.publisher?.substring(0, 8).toUpperCase()}
                  </span>
                  <span className="text-xxs text-term-white leading-snug line-clamp-1">{article.title}</span>
                </a>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─── Chart Tab ─── */
function ChartTab({
  data,
  chartData,
  chartPeriod,
  setChartPeriod,
}: {
  data: AssetData;
  chartData: CandleData[];
  chartPeriod: string;
  setChartPeriod: (p: string) => void;
}) {
  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center px-3 py-1 border-b border-term-border gap-2">
        <span className="text-xxs text-term-muted">Period:</span>
        {PERIODS.map((p) => (
          <button
            key={p.value}
            onClick={() => setChartPeriod(p.value)}
            className={`px-2 py-0.5 text-xxs ${
              chartPeriod === p.value
                ? "bg-term-blue text-white font-bold"
                : "text-term-muted hover:text-term-white bg-term-surface"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>
      <div className="flex-1 p-1">
        <PriceChart data={chartData} height={500} />
      </div>
    </div>
  );
}

/* ─── Analysis Tab ─── */
function AnalysisTab({ data }: { data: AssetData }) {
  const ind = data.indicators;
  const price = data.price;
  const sma20 = ind?.sma_20;
  const sma50 = ind?.sma_50;
  const sma200 = ind?.sma_200;
  const rsi = ind?.rsi;

  const signals: [string, string, string][] = [];
  if (sma20 && sma50) {
    signals.push([
      "SMA 20/50 Cross",
      sma20 > sma50 ? "BULLISH" : "BEARISH",
      sma20 > sma50 ? "text-positive" : "text-negative",
    ]);
  }
  if (sma50 && sma200) {
    signals.push([
      "SMA 50/200 Cross",
      sma50 > sma200 ? "GOLDEN CROSS" : "DEATH CROSS",
      sma50 > sma200 ? "text-positive" : "text-negative",
    ]);
  }
  if (sma20 && price) {
    signals.push([
      "Price vs SMA 20",
      price > sma20 ? "ABOVE" : "BELOW",
      price > sma20 ? "text-positive" : "text-negative",
    ]);
  }
  if (rsi) {
    signals.push([
      "RSI Signal",
      rsi > 70 ? "OVERBOUGHT" : rsi < 30 ? "OVERSOLD" : "NEUTRAL",
      rsi > 70 ? "text-negative" : rsi < 30 ? "text-positive" : "text-term-yellow",
    ]);
  }
  if (ind?.macd != null && ind?.macd_signal != null) {
    signals.push([
      "MACD Signal",
      ind.macd > ind.macd_signal ? "BULLISH" : "BEARISH",
      ind.macd > ind.macd_signal ? "text-positive" : "text-negative",
    ]);
  }
  if (ind?.bb_upper && ind?.bb_lower && price) {
    const bbPos = price > ind.bb_upper ? "ABOVE UPPER" : price < ind.bb_lower ? "BELOW LOWER" : "WITHIN BANDS";
    const bbColor = price > ind.bb_upper ? "text-negative" : price < ind.bb_lower ? "text-positive" : "text-term-yellow";
    signals.push(["Bollinger Position", bbPos, bbColor]);
  }

  return (
    <div>
      <div className="terminal-header">Technical Analysis Summary | TA &raquo;</div>
      {signals.length > 0 ? (
        <table>
          <thead>
            <tr className="text-xxs text-term-dim uppercase border-b border-term-border">
              <th className="text-left py-1 px-3">Signal</th>
              <th className="text-right py-1 px-3">Reading</th>
            </tr>
          </thead>
          <tbody>
            {signals.map(([label, value, color]) => (
              <tr key={label} className="border-b border-term-border/30">
                <td className="py-1.5 px-3 text-xs text-term-muted">{label}</td>
                <td className={`py-1.5 px-3 text-xs text-right font-bold ${color}`}>{value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="p-3 text-xs text-term-dim">INSUFFICIENT DATA FOR ANALYSIS</div>
      )}
    </div>
  );
}

/* ─── News Tab ─── */
const NEWS_TICKER_TABS = [
  "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "JPM",
  "GC=F", "SI=F", "CL=F", "NG=F",
  "EURUSD=X", "GBPUSD=X", "USDJPY=X",
  "BTC-USD", "ETH-USD",
  "^GSPC", "^DJI", "^IXIC",
];

const NEWS_SHORT_NAMES: Record<string, string> = {
  "GC=F": "GOLD", "SI=F": "SILVER", "CL=F": "OIL", "NG=F": "NATGAS",
  "EURUSD=X": "EUR/USD", "GBPUSD=X": "GBP/USD", "USDJPY=X": "USD/JPY",
  "^GSPC": "SPX", "^DJI": "DOW", "^IXIC": "NDX",
};

const SOURCE_COLORS: Record<string, string> = {
  "CNBC": "text-term-blue",
  "YAHOO": "text-term-orange",
  "BARR": "text-term-orange",
  "BARC": "text-term-orange",
  "INVE": "text-term-green",
  "MARK": "text-term-yellow",
  "KIPL": "text-term-blue",
  "TIPR": "text-term-cyan",
  "TECH": "text-term-green",
  "TRAD": "text-term-yellow",
  "BENZ": "text-term-orange",
  "BUSI": "text-term-blue",
  "YAHO": "text-term-orange",
  "THE": "text-term-muted",
  "MOTL": "text-term-green",
  "FINA": "text-term-cyan",
  "REUT": "text-term-blue",
  "BLOOM": "text-term-orange",
  "WALL": "text-term-blue",
};

function getSourceAbbr(publisher: string): { abbr: string; color: string } {
  if (!publisher) return { abbr: "NEWS", color: "text-term-muted" };
  const upper = publisher.toUpperCase();
  for (const [key, color] of Object.entries(SOURCE_COLORS)) {
    if (upper.includes(key)) return { abbr: key, color };
  }
  return { abbr: upper.substring(0, 4), color: "text-term-muted" };
}

function formatNewsTime(published: string | number): string {
  if (!published) return "";
  let date: Date;
  if (typeof published === "number") {
    date = new Date(published * 1000);
  } else {
    date = new Date(published);
  }
  if (isNaN(date.getTime())) return "";
  const month = date.toLocaleString("en-US", { month: "short" });
  const day = date.getDate();
  const hours = date.getHours().toString().padStart(2, "0");
  const mins = date.getMinutes().toString().padStart(2, "0");
  return `${month} ${day}, ${hours}:${mins}`;
}

function NewsTab({ data, ticker }: { data: AssetData; ticker: string }) {
  const [enhanced, setEnhanced] = useState<NewsEnhanced | null>(null);
  const [loadingNews, setLoadingNews] = useState(true);
  const [refreshCountdown, setRefreshCountdown] = useState(30 * 60);

  useEffect(() => {
    setLoadingNews(true);
    fetchNewsEnhanced(ticker)
      .then(setEnhanced)
      .catch(() => setEnhanced(null))
      .finally(() => setLoadingNews(false));
  }, [ticker]);

  useEffect(() => {
    const id = setInterval(() => {
      setRefreshCountdown((prev) => (prev > 0 ? prev - 1 : 30 * 60));
    }, 1000);
    return () => clearInterval(id);
  }, []);

  const news = enhanced?.articles ?? (Array.isArray(data.news) ? data.news : []);
  const mins = Math.floor(refreshCountdown / 60);
  const secs = refreshCountdown % 60;

  return (
    <div className="h-full flex flex-col">
      {/* Ticker tabs */}
      <div className="flex items-center px-1 py-0.5 border-b border-term-border bg-term-panel overflow-x-auto">
        <span className="text-xxs text-term-dim px-1 flex-shrink-0">QUICK:</span>
        {NEWS_TICKER_TABS.map((t) => (
          <a
            key={t}
            href={`/asset/${t}`}
            className={`px-1.5 py-0.5 text-xxs flex-shrink-0 ${
              t === ticker ? "bg-term-orange text-term-black font-bold" : "text-term-dim hover:text-term-blue-bright"
            }`}
          >
            {NEWS_SHORT_NAMES[t] || t}
          </a>
        ))}
      </div>

      {/* AI Analysis Banner */}
      {enhanced?.ai_analysis && (
        <div className="px-3 py-2 bg-term-surface border-b border-term-border">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xxs font-bold text-term-orange">AI NEWS AGENT</span>
            <span className="text-xxs text-term-dim">|</span>
            <span className="text-xxs text-term-cyan">Sentiment Analysis</span>
          </div>
          <div className="text-xs text-term-text leading-relaxed whitespace-pre-wrap">
            {enhanced.ai_analysis}
          </div>
        </div>
      )}

      {/* Refresh timer */}
      <div className="px-3 py-0.5 text-xxs text-term-dim border-b border-term-border flex items-center justify-between">
        <span>Next refresh in: {mins.toString().padStart(2, "0")}:{secs.toString().padStart(2, "0")}</span>
        {loadingNews && <span className="text-term-orange">FETCHING NEWS...</span>}
      </div>

      {/* News list */}
      <div className="flex-1 overflow-auto">
        {news.length === 0 ? (
          <div className="p-3 text-xs text-term-dim">
            {loadingNews ? "Loading news..." : `NO NEWS AVAILABLE FOR ${data.ticker}`}
          </div>
        ) : (
          news.map((article, i) => {
            const src = getSourceAbbr(article.publisher);
            const timeStr = formatNewsTime(article.published);
            return (
              <a
                key={i}
                href={article.link}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-start gap-2 px-3 py-1 border-b border-term-border/30 hover:bg-term-surface transition-colors"
              >
                <span className="text-term-yellow text-xxs font-bold w-5 text-right flex-shrink-0 tabular-nums">
                  {i + 1}
                </span>
                <span className={`text-xxs font-bold w-10 flex-shrink-0 ${src.color}`}>
                  {src.abbr}
                </span>
                {timeStr && (
                  <span className="text-term-muted text-xxs flex-shrink-0 w-24 tabular-nums">
                    {timeStr}
                  </span>
                )}
                <span className="text-xs text-term-white leading-snug">{article.title}</span>
              </a>
            );
          })
        )}
      </div>
    </div>
  );
}

/* ─── AI Tab ─── */
function AITab({ data }: { data: AssetData }) {
  return (
    <div>
      <div className="terminal-header">AI Deep Analysis | GLOOM &raquo;</div>
      <div className="p-3">
        {data.ai_summary ? (
          <div className="text-sm text-term-text leading-relaxed whitespace-pre-wrap">
            {data.ai_summary}
          </div>
        ) : (
          <div className="text-xs text-term-dim">
            AI analysis unavailable. Set <span className="text-term-yellow">OPENAI_API_KEY</span> in .env to enable deep research.
          </div>
        )}
      </div>
    </div>
  );
}
