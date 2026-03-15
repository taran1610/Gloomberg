"use client";

import { useState } from "react";
import {
  runBacktest,
  generateStrategy,
  UpgradeRequiredError,
  AuthRequiredError,
  type BacktestResult,
  type StrategyResult,
} from "@/lib/api";
import { EquityCurve } from "@/components/Charts";
import { useAuth } from "@/lib/auth";
import UpgradeModal from "@/components/UpgradeModal";

const STRATEGIES = [
  {
    id: "ma_crossover",
    name: "MA CROSSOVER",
    desc: "Buy fast MA > slow MA, sell on cross below",
    params: [
      { key: "fast_period", label: "Fast Period", default: 20 },
      { key: "slow_period", label: "Slow Period", default: 50 },
    ],
  },
  {
    id: "momentum",
    name: "RSI MOMENTUM",
    desc: "Buy RSI > oversold, sell RSI > overbought",
    params: [
      { key: "rsi_buy", label: "RSI Buy", default: 30 },
      { key: "rsi_sell", label: "RSI Sell", default: 70 },
    ],
  },
  {
    id: "mean_reversion",
    name: "BOLLINGER MEAN REV",
    desc: "Buy at lower BB, sell at upper BB",
    params: [],
  },
];

const PERIODS = ["6mo", "1y", "2y", "5y"];

export default function StrategyPage() {
  const { user, refresh } = useAuth();
  const [ticker, setTicker] = useState("AAPL");
  const [selectedStrategy, setSelectedStrategy] = useState("ma_crossover");
  const [period, setPeriod] = useState("2y");
  const [params, setParams] = useState<Record<string, number>>({});
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [strategyResult, setStrategyResult] = useState<StrategyResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [riskTolerance, setRiskTolerance] = useState("moderate");
  const [error, setError] = useState("");
  const [upgradeMsg, setUpgradeMsg] = useState("");

  const currentStrategy = STRATEGIES.find((s) => s.id === selectedStrategy)!;

  const handleBacktest = async () => {
    setLoading(true);
    setError("");
    setBacktestResult(null);
    try {
      const p: Record<string, number> = {};
      currentStrategy.params.forEach((param) => {
        p[param.key] = params[param.key] ?? param.default;
      });
      const result = await runBacktest(ticker.toUpperCase(), selectedStrategy, p, period);
      setBacktestResult(result);
      if (user) refresh();
    } catch (e: any) {
      if (e instanceof UpgradeRequiredError) {
        setUpgradeMsg(e.message);
      } else {
        setError(e.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!user) {
      setUpgradeMsg("Sign up and upgrade to Pro to use the AI Strategy Generator.");
      return;
    }
    if (user.plan !== "pro") {
      setUpgradeMsg("AI Strategy Generator is a Pro feature. Upgrade to unlock.");
      return;
    }

    setAiLoading(true);
    setError("");
    setStrategyResult(null);
    try {
      const result = await generateStrategy(ticker.toUpperCase(), riskTolerance);
      setStrategyResult(result);
      if (result.backtest) setBacktestResult(result.backtest);
      if (user) refresh();
    } catch (e: any) {
      if (e instanceof UpgradeRequiredError || e instanceof AuthRequiredError) {
        setUpgradeMsg(e.message);
      } else {
        setError(e.message);
      }
    } finally {
      setAiLoading(false);
    }
  };

  const m = backtestResult?.metrics;
  const canGenerate = user?.plan === "pro";

  return (
    <div className="h-full flex flex-col">
      {upgradeMsg && (
        <UpgradeModal message={upgradeMsg} onClose={() => setUpgradeMsg("")} />
      )}

      {/* Title */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-term-bg border-b border-term-border">
        <div className="flex items-center gap-3">
          <span className="text-term-orange font-bold text-sm">STRATEGY LAB</span>
          <span className="text-term-dim text-xxs">BACKTEST ENGINE</span>
        </div>
        {user && (
          <span className="text-xxs text-term-muted">
            {user.usage.backtests} / {user.limits.backtests_per_day} BACKTESTS TODAY
          </span>
        )}
      </div>

      <div className="flex-1 overflow-auto">
        <div className="grid grid-cols-12 h-full">
          {/* Left: Config Panel (3 cols) */}
          <div className="col-span-3 border-r border-term-border flex flex-col overflow-auto">
            {/* Ticker */}
            <div className="border-b border-term-border p-2">
              <div className="text-xxs text-term-muted uppercase mb-1">Ticker</div>
              <input
                type="text"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                className="w-full bg-term-black border border-term-border text-term-white text-sm px-2 py-1 focus:border-term-orange"
              />
            </div>

            {/* Strategy */}
            <div className="border-b border-term-border p-2">
              <div className="text-xxs text-term-muted uppercase mb-1">Strategy</div>
              {STRATEGIES.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setSelectedStrategy(s.id)}
                  className={`w-full text-left px-2 py-1.5 mb-0.5 text-xs border transition-colors ${
                    selectedStrategy === s.id
                      ? "bg-term-orange/10 border-term-orange text-term-orange"
                      : "bg-term-black border-term-border text-term-muted hover:text-term-white"
                  }`}
                >
                  <div className="font-bold">{s.name}</div>
                  <div className="text-xxs opacity-70 mt-0.5">{s.desc}</div>
                </button>
              ))}
            </div>

            {/* Params */}
            {currentStrategy.params.length > 0 && (
              <div className="border-b border-term-border p-2">
                <div className="text-xxs text-term-muted uppercase mb-1">Parameters</div>
                {currentStrategy.params.map((p) => (
                  <div key={p.key} className="mb-1.5">
                    <div className="text-xxs text-term-dim">{p.label}</div>
                    <input
                      type="number"
                      value={params[p.key] ?? p.default}
                      onChange={(e) =>
                        setParams((prev) => ({
                          ...prev,
                          [p.key]: parseInt(e.target.value) || p.default,
                        }))
                      }
                      className="w-full bg-term-black border border-term-border text-term-white text-xs px-2 py-1 focus:border-term-orange"
                    />
                  </div>
                ))}
              </div>
            )}

            {/* Period */}
            <div className="border-b border-term-border p-2">
              <div className="text-xxs text-term-muted uppercase mb-1">Period</div>
              <div className="grid grid-cols-4 gap-0.5">
                {PERIODS.map((p) => (
                  <button
                    key={p}
                    onClick={() => setPeriod(p)}
                    className={`py-1 text-xxs font-bold ${
                      period === p
                        ? "bg-term-orange text-term-black"
                        : "bg-term-surface text-term-muted hover:text-term-white"
                    }`}
                  >
                    {p.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            {/* Run Backtest */}
            <div className="p-2">
              <button
                onClick={handleBacktest}
                disabled={loading || !ticker}
                className="w-full py-2 bg-term-blue text-term-black text-xs font-bold hover:opacity-80 disabled:opacity-30"
              >
                {loading ? "RUNNING..." : "RUN BACKTEST"}
              </button>
            </div>

            {/* AI Generate */}
            <div className="border-t border-term-border p-2">
              <div className="text-xxs text-term-muted uppercase mb-1">Risk Tolerance</div>
              <div className="grid grid-cols-3 gap-0.5 mb-2">
                {["conservative", "moderate", "aggressive"].map((r) => (
                  <button
                    key={r}
                    onClick={() => setRiskTolerance(r)}
                    className={`py-1 text-xxs uppercase ${
                      riskTolerance === r
                        ? "bg-term-orange text-term-black font-bold"
                        : "bg-term-surface text-term-muted hover:text-term-white"
                    }`}
                  >
                    {r.slice(0, 4)}
                  </button>
                ))}
              </div>
              <button
                onClick={handleGenerate}
                disabled={aiLoading || !ticker}
                className={`w-full py-2 text-xs font-bold transition-colors disabled:opacity-30 ${
                  canGenerate
                    ? "bg-term-orange text-term-black hover:bg-term-orange-dim"
                    : "bg-term-surface text-term-muted border border-term-border hover:border-term-orange/30"
                }`}
              >
                {aiLoading ? "GENERATING..." : (
                  <>
                    AI GENERATE
                    {!canGenerate && (
                      <span className="ml-1.5 text-xxs bg-term-orange/20 text-term-orange px-1 py-0.5">
                        PRO
                      </span>
                    )}
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Right: Results (9 cols) */}
          <div className="col-span-9 flex flex-col overflow-auto">
            {error && (
              <div className="px-3 py-2 bg-term-red/10 border-b border-term-red/30 text-term-red text-xs flex items-center justify-between gap-2">
                <span>ERROR: {error}</span>
                <button
                  onClick={handleBacktest}
                  disabled={loading}
                  className="px-2 py-1 bg-term-orange text-term-black text-xxs font-bold hover:opacity-80 shrink-0 disabled:opacity-50"
                >
                  RETRY
                </button>
              </div>
            )}

            {/* AI Strategy Output */}
            {strategyResult && (
              <div className="border-b border-term-border">
                <div className="terminal-header">AI Strategy | GLOOM &raquo;</div>
                <div className="p-2">
                  <div className="text-term-orange font-bold text-xs mb-1">
                    {strategyResult.strategy_name}
                  </div>
                  <div className="text-xxs text-term-muted mb-2">
                    {strategyResult.description}
                  </div>
                  <div className="space-y-0.5">
                    {strategyResult.rules.map((rule, i) => (
                      <div key={i} className="text-xs">
                        <span className="text-term-yellow mr-1">{i + 1}.</span>
                        <span className="text-term-text">{rule}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Metrics */}
            {m && (
              <div className="border-b border-term-border">
                <div className="terminal-header">Performance Metrics | PM &raquo;</div>
                <div className="grid grid-cols-4 gap-px bg-term-border">
                  {[
                    ["TOTAL RETURN", `${m.total_return >= 0 ? "+" : ""}${m.total_return.toFixed(2)}%`, m.total_return >= 0],
                    ["ANNUAL RETURN", `${m.annual_return >= 0 ? "+" : ""}${m.annual_return.toFixed(2)}%`, m.annual_return >= 0],
                    ["SHARPE RATIO", m.sharpe_ratio.toFixed(2), m.sharpe_ratio >= 1],
                    ["MAX DRAWDOWN", `${m.max_drawdown.toFixed(2)}%`, m.max_drawdown > -20],
                    ["WIN RATE", `${m.win_rate.toFixed(1)}%`, m.win_rate >= 50],
                    ["TRADES", m.num_trades.toString(), true],
                    ["PROFIT FACTOR", m.profit_factor.toFixed(2), m.profit_factor >= 1],
                    ["STRATEGY", backtestResult?.strategy.replace("_", " ").toUpperCase() ?? "--", true],
                  ].map(([label, value, positive]) => (
                    <div key={label as string} className="bg-term-bg p-2">
                      <div className="text-xxs text-term-muted">{label}</div>
                      <div className={`text-lg font-bold tabular-nums ${positive ? "text-positive" : "text-negative"}`}>
                        {value}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Equity Curve */}
            {backtestResult && backtestResult.equity_curve.length > 0 && (
              <div className="border-b border-term-border">
                <div className="terminal-header">Equity Curve | EC &raquo;</div>
                <div className="p-1">
                  <EquityCurve data={backtestResult.equity_curve} height={220} />
                </div>
              </div>
            )}

            {/* Trade History */}
            {backtestResult && backtestResult.trades.length > 0 && (
              <div className="flex-1">
                <div className="terminal-header">
                  Trade History | TH &raquo;
                  <span className="text-term-muted font-normal ml-2">
                    {backtestResult.trades.length} trades
                  </span>
                </div>
                <div className="overflow-auto max-h-[300px]">
                  <table>
                    <thead className="sticky top-0 bg-term-panel">
                      <tr className="text-xxs text-term-dim uppercase border-b border-term-border">
                        <th className="text-left py-1 px-2">#</th>
                        <th className="text-left py-1 px-2">Date</th>
                        <th className="text-left py-1 px-2">Side</th>
                        <th className="text-right py-1 px-2">Price</th>
                        <th className="text-right py-1 px-2">Shares</th>
                        <th className="text-right py-1 px-2">P&L</th>
                      </tr>
                    </thead>
                    <tbody>
                      {backtestResult.trades.map((t, i) => (
                        <tr key={i} className="terminal-row text-xs">
                          <td className="py-1 px-2 text-term-dim tabular-nums">{i + 1}</td>
                          <td className="py-1 px-2 tabular-nums">{t.date}</td>
                          <td className="py-1 px-2">
                            <span className={t.type === "BUY" ? "text-positive font-bold" : "text-negative font-bold"}>
                              {t.type}
                            </span>
                          </td>
                          <td className="py-1 px-2 text-right tabular-nums text-term-white">
                            {t.price.toFixed(2)}
                          </td>
                          <td className="py-1 px-2 text-right tabular-nums text-term-muted">
                            {t.shares.toFixed(2)}
                          </td>
                          <td className={`py-1 px-2 text-right tabular-nums font-bold ${
                            t.pnl != null ? (t.pnl >= 0 ? "text-positive" : "text-negative") : "text-term-dim"
                          }`}>
                            {t.pnl != null ? `${t.pnl >= 0 ? "+" : ""}${t.pnl.toFixed(2)}` : "--"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Empty State */}
            {!backtestResult && !strategyResult && !error && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-term-orange text-sm mb-2">STRATEGY BACKTESTER</div>
                  <div className="text-term-dim text-xs max-w-sm">
                    Select a strategy and click <span className="text-term-blue font-bold">RUN BACKTEST</span>,
                    or use <span className="text-term-orange font-bold">AI GENERATE</span>{" "}
                    <span className="text-xxs bg-term-orange/20 text-term-orange px-1 py-0.5">PRO</span>{" "}
                    for automated strategy creation.
                  </div>
                  <div className="text-term-muted text-xxs mt-2 max-w-sm">
                    If RUN BACKTEST fails, the backend may be cold starting. Wait 1 min and try again, or try a different ticker (e.g. AAPL, SPY).
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
