"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  fetchDashboard,
  formatPercent,
  formatNumber,
  type DashboardData,
} from "@/lib/api";
import MarketHeatmap from "@/components/MarketHeatmap";

/** Fallback data when API fails - always show something */
const DUMMY_DASHBOARD: DashboardData = {
  indices: [
    { name: "S&P 500", ticker: "^GSPC", price: 5820, change: 12.5, change_pct: 0.22 },
    { name: "Dow Jones", ticker: "^DJI", price: 45200, change: -45, change_pct: -0.1 },
    { name: "NASDAQ", ticker: "^IXIC", price: 18250, change: 85, change_pct: 0.47 },
  ],
  gainers: [
    { ticker: "NVDA", name: "NVIDIA", price: 142.5, change_pct: 2.45 },
    { ticker: "AAPL", name: "Apple", price: 228.3, change_pct: 1.82 },
  ],
  losers: [
    { ticker: "TSLA", name: "Tesla", price: 245, change_pct: -0.95 },
    { ticker: "AMD", name: "AMD", price: 128.4, change_pct: -0.72 },
  ],
  sectors: [
    { name: "Technology", change_pct: 0.85 },
    { name: "Financials", change_pct: 0.32 },
  ],
  crypto: [
    { ticker: "BTC-USD", name: "Bitcoin", price: 98000, change_pct: 0.5 },
    { ticker: "ETH-USD", name: "Ethereum", price: 3650, change_pct: -0.2 },
  ],
  commodities: [
    { ticker: "GC=F", name: "Gold", price: 2650, change_pct: 0.15 },
    { ticker: "CL=F", name: "Crude Oil", price: 78.5, change_pct: -0.3 },
  ],
  forex: [
    { ticker: "EURUSD=X", name: "EUR/USD", price: 1.085, change_pct: 0.05 },
    { ticker: "USDJPY=X", name: "USD/JPY", price: 149.5, change_pct: -0.12 },
  ],
  vix: 15.5,
  ai_summary: null,
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  const loadDashboard = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await fetchDashboard();
      setData(result);
      setLastUpdated(new Date().toLocaleTimeString("en-US", { hour12: false }));
    } catch (e: any) {
      setError(e.message || "Failed to connect to backend");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
    const interval = setInterval(loadDashboard, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-term-orange text-sm mb-2">LOADING MARKET DATA...</div>
          <div className="text-term-dim text-xs">Connecting to data feeds</div>
          <div className="text-term-muted text-xxs mt-3 max-w-xs mx-auto">
            First load can take 30–60s if the backend is waking up (Render free tier). If it hangs, click RETRY after a minute.
          </div>
        </div>
      </div>
    );
  }

  // When API fails, use dummy data so user always sees something
  const displayData = data ?? DUMMY_DASHBOARD;
  const isOffline = !!error && !data;

  const indices = Array.isArray(displayData?.indices) ? displayData.indices : [];
  const gainers = Array.isArray(displayData?.gainers) ? displayData.gainers : [];
  const losers = Array.isArray(displayData?.losers) ? displayData.losers : [];
  const sectors = Array.isArray(displayData?.sectors) ? displayData.sectors : [];
  const crypto = Array.isArray(displayData?.crypto) ? displayData.crypto : [];
  const commodities = Array.isArray(displayData?.commodities) ? displayData.commodities : [];
  const forex = Array.isArray(displayData?.forex) ? displayData.forex : [];

  return (
    <div className="h-full flex flex-col">
      {/* Title Bar */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-term-bg border-b border-term-border">
        <div className="flex items-center gap-3">
          <span className="text-term-orange font-bold text-sm">MARKET DASHBOARD</span>
          <span className="text-term-dim text-xxs">{isOffline ? "OFFLINE — SAMPLE DATA" : "GLOOMBERG MAIN"}</span>
          {isOffline && (
            <button onClick={loadDashboard} className="px-2 py-0.5 bg-term-orange text-term-black text-xxs font-bold">
              RETRY
            </button>
          )}
        </div>
        <div className="flex items-center gap-4">
          {displayData?.vix != null && (
            <div className="flex items-center gap-2">
              <span className="text-term-muted text-xs">VIX</span>
              <span
                className={`text-sm font-bold ${
                  displayData.vix > 30
                    ? "text-term-red"
                    : displayData.vix > 20
                    ? "text-term-yellow"
                    : "text-term-green"
                }`}
              >
                {displayData.vix.toFixed(2)}
              </span>
              <span className="text-xxs text-term-dim">
                {displayData.vix > 30 ? "HIGH VOL" : displayData.vix > 20 ? "ELEVATED" : "LOW VOL"}
              </span>
            </div>
          )}
          <span className="text-xxs text-term-dim">
            UPDATED {lastUpdated}
          </span>
          <button
            onClick={loadDashboard}
            disabled={loading}
            className="text-xxs text-term-muted hover:text-term-orange disabled:opacity-50"
          >
            [REFRESH]
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="flex-1 overflow-auto">
        <div className="grid grid-cols-2" style={{ gridTemplateRows: "auto auto auto auto" }}>

          {/* 1) Global Indices */}
          <div className="border-r border-b border-term-border flex flex-col">
            <div className="terminal-header">1) Global Indices | IDX &raquo;</div>
            <div className="flex-1 overflow-auto">
              <table>
                <thead>
                  <tr className="text-xxs text-term-dim uppercase">
                    <th className="text-left py-1 px-2">Index</th>
                    <th className="text-right py-1 px-2">Last</th>
                    <th className="text-right py-1 px-2">Chg</th>
                    <th className="text-right py-1 px-2">Chg%</th>
                  </tr>
                </thead>
                <tbody>
                  {indices.map((idx) => (
                    <tr key={idx.ticker} className="terminal-row">
                      <td className="py-1 px-2 text-term-white text-xs font-bold">
                        {idx.name}
                      </td>
                      <td className="py-1 px-2 text-right text-xs tabular-nums text-term-white">
                        {formatNumber(idx.price)}
                      </td>
                      <td className={`py-1 px-2 text-right text-xs tabular-nums ${idx.change >= 0 ? "text-positive" : "text-negative"}`}>
                        {idx.change >= 0 ? "+" : ""}{idx.change.toFixed(2)}
                      </td>
                      <td className={`py-1 px-2 text-right text-xs tabular-nums font-bold ${idx.change_pct >= 0 ? "text-positive" : "text-negative"}`}>
                        {formatPercent(idx.change_pct)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 2) Sector Heatmap */}
          <div className="border-b border-term-border flex flex-col">
            <div className="terminal-header">2) Sector Performance | SEC &raquo;</div>
            <div className="flex-1 overflow-auto p-2">
              <MarketHeatmap sectors={sectors} />
            </div>
          </div>

          {/* 3) Top Gainers */}
          <div className="border-r border-b border-term-border flex flex-col">
            <div className="terminal-header">
              3) Top Gainers | <span className="text-term-green">GP</span> &raquo;
            </div>
            <div className="flex-1 overflow-auto">
              <table>
                <thead>
                  <tr className="text-xxs text-term-dim uppercase">
                    <th className="text-left py-1 px-2">Ticker</th>
                    <th className="text-left py-1 px-2">Name</th>
                    <th className="text-right py-1 px-2">Price</th>
                    <th className="text-right py-1 px-2">Chg%</th>
                  </tr>
                </thead>
                <tbody>
                  {gainers.map((g) => (
                    <tr key={g.ticker} className="terminal-row">
                      <td className="py-1 px-2">
                        <Link
                          href={`/asset/${g.ticker}`}
                          className="text-term-blue text-xs font-bold hover:text-term-cyan"
                        >
                          {g.ticker}
                        </Link>
                      </td>
                      <td className="py-1 px-2 text-xs text-term-muted truncate max-w-[120px]">
                        {g.name}
                      </td>
                      <td className="py-1 px-2 text-right text-xs tabular-nums text-term-white">
                        {g.price.toFixed(2)}
                      </td>
                      <td className="py-1 px-2 text-right text-xs tabular-nums font-bold text-positive">
                        {formatPercent(g.change_pct)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 4) Top Losers */}
          <div className="border-b border-term-border flex flex-col">
            <div className="terminal-header">
              4) Top Losers | <span className="text-term-red">LP</span> &raquo;
            </div>
            <div className="flex-1 overflow-auto">
              <table>
                <thead>
                  <tr className="text-xxs text-term-dim uppercase">
                    <th className="text-left py-1 px-2">Ticker</th>
                    <th className="text-left py-1 px-2">Name</th>
                    <th className="text-right py-1 px-2">Price</th>
                    <th className="text-right py-1 px-2">Chg%</th>
                  </tr>
                </thead>
                <tbody>
                  {losers.map((l) => (
                    <tr key={l.ticker} className="terminal-row">
                      <td className="py-1 px-2">
                        <Link
                          href={`/asset/${l.ticker}`}
                          className="text-term-blue text-xs font-bold hover:text-term-cyan"
                        >
                          {l.ticker}
                        </Link>
                      </td>
                      <td className="py-1 px-2 text-xs text-term-muted truncate max-w-[120px]">
                        {l.name}
                      </td>
                      <td className="py-1 px-2 text-right text-xs tabular-nums text-term-white">
                        {l.price.toFixed(2)}
                      </td>
                      <td className="py-1 px-2 text-right text-xs tabular-nums font-bold text-negative">
                        {formatPercent(l.change_pct)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 5) Crypto Markets */}
          <div className="border-r border-b border-term-border flex flex-col">
            <div className="terminal-header">
              5) Crypto Markets | <span className="text-term-yellow">CRY</span> &raquo;
            </div>
            <div className="flex-1 overflow-auto">
              <table>
                <thead>
                  <tr className="text-xxs text-term-dim uppercase">
                    <th className="text-left py-1 px-2">Asset</th>
                    <th className="text-right py-1 px-2">Price</th>
                    <th className="text-right py-1 px-2">Chg%</th>
                  </tr>
                </thead>
                <tbody>
                  {crypto.map((c) => (
                    <tr key={c.ticker} className="terminal-row">
                      <td className="py-1 px-2">
                        <Link
                          href={`/asset/${c.ticker}`}
                          className="text-term-yellow text-xs font-bold hover:text-term-cyan"
                        >
                          {c.name}
                        </Link>
                      </td>
                      <td className="py-1 px-2 text-right text-xs tabular-nums text-term-white">
                        ${formatNumber(c.price)}
                      </td>
                      <td className={`py-1 px-2 text-right text-xs tabular-nums font-bold ${c.change_pct >= 0 ? "text-positive" : "text-negative"}`}>
                        {formatPercent(c.change_pct)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 6) Commodities */}
          <div className="border-b border-term-border flex flex-col">
            <div className="terminal-header">
              6) Commodities | <span className="text-term-orange">CMD</span> &raquo;
            </div>
            <div className="flex-1 overflow-auto">
              <table>
                <thead>
                  <tr className="text-xxs text-term-dim uppercase">
                    <th className="text-left py-1 px-2">Asset</th>
                    <th className="text-right py-1 px-2">Price</th>
                    <th className="text-right py-1 px-2">Chg%</th>
                  </tr>
                </thead>
                <tbody>
                  {commodities.map((c) => (
                    <tr key={c.ticker} className="terminal-row">
                      <td className="py-1 px-2">
                        <Link
                          href={`/asset/${c.ticker}`}
                          className="text-term-orange text-xs font-bold hover:text-term-cyan"
                        >
                          {c.name}
                        </Link>
                      </td>
                      <td className="py-1 px-2 text-right text-xs tabular-nums text-term-white">
                        ${c.price.toFixed(2)}
                      </td>
                      <td className={`py-1 px-2 text-right text-xs tabular-nums font-bold ${c.change_pct >= 0 ? "text-positive" : "text-negative"}`}>
                        {formatPercent(c.change_pct)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 7) Forex */}
          <div className="border-r border-term-border flex flex-col">
            <div className="terminal-header">
              7) Forex | <span className="text-term-cyan">FX</span> &raquo;
            </div>
            <div className="flex-1 overflow-auto">
              <table>
                <thead>
                  <tr className="text-xxs text-term-dim uppercase">
                    <th className="text-left py-1 px-2">Pair</th>
                    <th className="text-right py-1 px-2">Rate</th>
                    <th className="text-right py-1 px-2">Chg%</th>
                  </tr>
                </thead>
                <tbody>
                  {forex.map((f) => (
                    <tr key={f.ticker} className="terminal-row">
                      <td className="py-1 px-2">
                        <Link
                          href={`/asset/${f.ticker}`}
                          className="text-term-cyan text-xs font-bold hover:text-term-blue-bright"
                        >
                          {f.name}
                        </Link>
                      </td>
                      <td className="py-1 px-2 text-right text-xs tabular-nums text-term-white">
                        {f.price.toFixed(4)}
                      </td>
                      <td className={`py-1 px-2 text-right text-xs tabular-nums font-bold ${f.change_pct >= 0 ? "text-positive" : "text-negative"}`}>
                        {formatPercent(f.change_pct)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 8) Terminal Info + AI Summary */}
          <div className="flex flex-col">
            <div className="terminal-header">8) Terminal | SYS &raquo;</div>
            <div className="flex-1 p-3 text-xs space-y-2">
              {displayData?.ai_summary && (
                <div className="bg-term-surface border border-term-border p-2 mb-2">
                  <div className="text-term-orange text-xxs font-bold mb-0.5">AI MARKET AGENT</div>
                  <div className="text-term-text text-xxs leading-relaxed">{displayData.ai_summary}</div>
                </div>
              )}
              <div>
                <div className="text-term-orange font-bold mb-0.5">GLOOMBERG TERMINAL v0.2.0</div>
                <div className="text-term-dim">AI-Powered Financial Research</div>
              </div>
              <div className="border-t border-term-border pt-1.5">
                <div className="text-term-muted text-xxs uppercase mb-0.5">Quick Search</div>
                <div className="space-y-0.5">
                  <div className="flex gap-2">
                    <span className="text-term-yellow w-16">AAPL</span>
                    <span className="text-term-dim">Stocks</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-term-yellow w-16">GC=F</span>
                    <span className="text-term-dim">Gold Futures</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-term-yellow w-16">EURUSD=X</span>
                    <span className="text-term-dim">Forex Pairs</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-term-yellow w-16">BTC-USD</span>
                    <span className="text-term-dim">Crypto</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-term-yellow w-16">^GSPC</span>
                    <span className="text-term-dim">Indices</span>
                  </div>
                </div>
              </div>
              <div className="border-t border-term-border pt-1.5">
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-term-green pulse" />
                  <span className="text-term-green text-xxs">ALL MARKETS LIVE</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
