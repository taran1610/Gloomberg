"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

const NAV_ITEMS = [
  { href: "/", label: "DASHBOARD", key: "1" },
  { href: "/chat", label: "AI CHAT", key: "2" },
  { href: "/research", label: "RESEARCH", key: "3" },
  { href: "/strategy", label: "STRATEGY", key: "4" },
  { href: "/pricing", label: "PRICING", key: "5" },
];

const QUICK_TICKERS = [
  "AAPL", "NVDA", "MSFT", "TSLA", "GOOGL", "AMZN", "META",
  "BTC-USD", "GC=F", "SI=F", "CL=F", "EURUSD=X", "^GSPC",
];

export default function TerminalHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [query, setQuery] = useState("");
  const [clock, setClock] = useState("");

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setClock(
        now.toLocaleTimeString("en-US", {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        })
      );
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  const CMD_ALIASES: Record<string, string> = {
    GOLD: "GC=F", SILVER: "SI=F", OIL: "CL=F", CRUDE: "CL=F", BRENT: "BZ=F",
    NATGAS: "NG=F", COPPER: "HG=F", PLATINUM: "PL=F",
    EUR: "EURUSD=X", EURUSD: "EURUSD=X", GBP: "GBPUSD=X", GBPUSD: "GBPUSD=X",
    JPY: "USDJPY=X", USDJPY: "USDJPY=X", AUD: "AUDUSD=X", CAD: "USDCAD=X",
    CHF: "USDCHF=X", DXY: "DX-Y.NYB", DXI: "DX-Y.NYB",
    SPX: "^GSPC", SPY: "^GSPC", DOW: "^DJI", NDX: "^IXIC", VIX: "^VIX",
    BTC: "BTC-USD", BITCOIN: "BTC-USD", ETH: "ETH-USD", SOL: "SOL-USD",
  };

  const handleCommand = (e: React.FormEvent) => {
    e.preventDefault();
    const cmd = query.trim().toUpperCase().replace(/\s+/g, "");
    if (!cmd) return;
    setQuery("");
    if (cmd === "/CHAT" || cmd === "CHAT") router.push("/chat");
    else if (cmd === "/RESEARCH" || cmd === "RESEARCH" || cmd === "DEXTER") router.push("/research");
    else if (cmd === "/STRAT" || cmd === "STRATEGY") router.push("/strategy");
    else if (cmd === "/HOME" || cmd === "HOME" || cmd === "/") router.push("/");
    else if (cmd === "/PRICING" || cmd === "PRICING") router.push("/pricing");
    else {
      const ticker = CMD_ALIASES[cmd] || cmd;
      router.push(`/asset/${encodeURIComponent(ticker)}`);
    }
  };

  const assetMatch = pathname.match(/^\/asset\/(.+)/);
  const currentTicker = assetMatch ? decodeURIComponent(assetMatch[1]).toUpperCase() : null;

  const getTickerLabel = (t: string) => {
    if (t.endsWith("=F")) return `${t} Commodity`;
    if (t.endsWith("=X") || t.includes("NYB")) return `${t} Forex`;
    if (t.startsWith("^")) return `${t} Index`;
    if (t.endsWith("-USD") || t.endsWith("-USDT")) return `${t} Crypto`;
    return `${t} US Equity`;
  };

  const contextText = currentTicker
    ? `${getTickerLabel(currentTicker)} | Overview`
    : pathname === "/chat"
    ? "AI Market Research"
    : pathname === "/research"
    ? "Deep Research | Dexter Agent"
    : pathname === "/strategy"
    ? "Strategy & Backtesting"
    : pathname === "/pricing"
    ? "Plans & Pricing"
    : pathname === "/login"
    ? "Authentication"
    : "Market Dashboard";

  return (
    <div className="flex-shrink-0 relative z-10">
      {/* Red Top Banner */}
      <div className="h-6 bg-[#C41E3A] flex items-center justify-between px-3">
        <span className="text-white font-bold text-sm tracking-wide">GLOOMBERG TERMINAL</span>
        <span className="text-white/90 text-xxs">Financial Analytics Platform</span>
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 bg-white rounded-full pulse" />
          <span className="text-white text-xxs font-bold">LIVE</span>
        </span>
      </div>

      {/* Top Header */}
      <div className="h-8 bg-term-bg border-b border-term-border flex items-center px-3">
        <Link href="/" className="flex items-center gap-1.5 flex-shrink-0 mr-4">
          <span className="text-term-orange font-bold text-lg tracking-wide">
            GLOOMBERG
          </span>
        </Link>

        <span className="text-term-muted text-xxs flex-shrink-0 mr-4">|</span>
        <span className="text-term-white text-xs flex-shrink-0">{contextText}</span>

        <div className="flex-1 flex justify-center px-6">
          <form onSubmit={handleCommand} className="w-full max-w-sm">
            <div className="flex items-center border border-term-border bg-term-black hover:border-term-dim transition-colors">
              <span className="text-term-orange text-xxs px-1.5 opacity-70">&gt;_</span>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ticker / command (AAPL, GC=F, EURUSD=X)"
                className="flex-1 bg-transparent text-term-white text-xs py-0.5 pr-2 placeholder:text-term-dim"
              />
            </div>
          </form>
        </div>

        <div className="flex items-center gap-3 flex-shrink-0">
          {user ? (
            <>
              <span className="text-xxs text-term-dim hidden lg:block">{user.email}</span>
              <span className={`text-xxs font-bold px-1 py-0.5 ${
                user.plan === "pro"
                  ? "bg-term-orange/20 text-term-orange"
                  : "bg-term-surface text-term-muted"
              }`}>
                {user.plan.toUpperCase()}
              </span>
              <button
                onClick={logout}
                className="text-xxs text-term-dim hover:text-term-red transition-colors"
              >
                LOGOUT
              </button>
            </>
          ) : (
            <Link
              href="/login"
              className="text-xxs text-term-orange hover:text-term-orange-dim font-bold transition-colors"
            >
              LOGIN
            </Link>
          )}
          <span className="text-term-muted text-xxs">|</span>
          <span className="w-1.5 h-1.5 bg-term-green pulse flex-shrink-0" />
          <span className="text-term-green text-xxs font-bold">LIVE</span>
          <span className="text-term-yellow text-xs font-bold tabular-nums tracking-wider">
            {clock}
          </span>
        </div>
      </div>

      {/* Navigation Bar */}
      <div className="h-6 bg-term-panel border-b border-term-border flex items-center px-1 overflow-x-auto">
        {NAV_ITEMS.map(({ href, label, key }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-0.5 px-2 py-0.5 text-xxs transition-colors flex-shrink-0 ${
                active ? "tab-active" : "tab-inactive"
              }`}
            >
              <span className="opacity-60">[{key}]</span>
              {label}
            </Link>
          );
        })}

        <span className="text-term-dim text-xxs mx-1 flex-shrink-0">|</span>

        {QUICK_TICKERS.map((t) => {
          const active = pathname === `/asset/${t}`;
          const SHORT_NAMES: Record<string, string> = {
            "GC=F": "GOLD", "SI=F": "SILVER", "CL=F": "OIL",
            "EURUSD=X": "EUR/USD", "^GSPC": "S&P500",
          };
          const label = SHORT_NAMES[t] || t;
          return (
            <Link
              key={t}
              href={`/asset/${t}`}
              className={`px-1.5 py-0.5 text-xxs transition-colors flex-shrink-0 ${
                active ? "tab-active" : "text-term-dim hover:text-term-blue-bright"
              }`}
            >
              {label}
            </Link>
          );
        })}

        <div className="flex-1" />
        <span className="text-xxs text-term-dim flex-shrink-0 pr-1">
          Type any ticker: AAPL · GC=F · EURUSD=X · ^GSPC
        </span>
      </div>
    </div>
  );
}
