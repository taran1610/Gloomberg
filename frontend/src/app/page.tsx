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

  if (error && !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-term-red text-sm mb-2">CONNECTION ERROR</div>
          <div className="text-term-dim text-xs mb-3">{error}</div>
          <button
            onClick={loadDashboard}
            className="px-3 py-1 bg-term-orange text-term-black text-xs font-bold hover:bg-term-orange-dim"
          >
            RETRY
          </button>
        </div>
      </div>
    );
  }

  const indices = Array.isArray(data?.indices) ? data.indices : [];
  const gainers = Array.isArray(data?.gainers) ? data.gainers : [];
  const losers = Array.isArray(data?.losers) ? data.losers : [];
  const sectors = Array.isArray(data?.sectors) ? data.sectors : [];
  const crypto = Array.isArray(data?.crypto) ? data.crypto : [];
  const commodities = Array.isArray(data?.commodities) ? data.commodities : [];
  const forex = Array.isArray(data?.forex) ? data.forex : [];

  return (
    <div className="h-full flex flex-col">
      {/* Title Bar */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-term-bg border-b border-term-border">
        <div className="flex items-center gap-3">
          <span className="text-term-orange font-bold text-sm">MARKET DASHBOARD</span>
          <span className="text-term-dim text-xxs">GLOOMBERG MAIN</span>
        </div>
        <div className="flex items-center gap-4">
          {data?.vix != null && (
            <div className="flex items-center gap-2">
              <span className="text-term-muted text-xs">VIX</span>
              <span
                className={`text-sm font-bold ${
                  data.vix > 30
                    ? "text-term-red"
                    : data.vix > 20
                    ? "text-term-yellow"
                    : "text-term-green"
                }`}
              >
                {data.vix.toFixed(2)}
              </span>
              <span className="text-xxs text-term-dim">
                {data.vix > 30 ? "HIGH VOL" : data.vix > 20 ? "ELEVATED" : "LOW VOL"}
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
              {data?.ai_summary && (
                <div className="bg-term-surface border border-term-border p-2 mb-2">
                  <div className="text-term-orange text-xxs font-bold mb-0.5">AI MARKET AGENT</div>
                  <div className="text-term-text text-xxs leading-relaxed">{data.ai_summary}</div>
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
