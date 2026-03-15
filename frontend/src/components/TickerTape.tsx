"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchDashboard, type DashboardData } from "@/lib/api";

interface TapeItem {
  ticker: string;
  label: string;
  price: number;
  change: number;
  pct: number;
}

/** Fallback when API fails - always show something */
const DUMMY_TAPE: TapeItem[] = [
  { ticker: "^GSPC", label: "S&P 500", price: 5820, change: 12, pct: 0.22 },
  { ticker: "^DJI", label: "Dow Jones", price: 45200, change: -45, pct: -0.1 },
  { ticker: "AAPL", label: "AAPL", price: 228, change: 2, pct: 0.9 },
  { ticker: "NVDA", label: "NVDA", price: 142, change: 3, pct: 2.1 },
  { ticker: "GC=F", label: "Gold", price: 2650, change: 4, pct: 0.15 },
  { ticker: "EURUSD=X", label: "EUR/USD", price: 1.085, change: 0, pct: 0.05 },
  { ticker: "BTC-USD", label: "Bitcoin", price: 98000, change: 500, pct: 0.5 },
  { ticker: "ETH-USD", label: "Ethereum", price: 3650, change: -10, pct: -0.2 },
];

export default function TickerTape() {
  const [items, setItems] = useState<TapeItem[]>(DUMMY_TAPE);

  useEffect(() => {
    const load = async () => {
      try {
        const data: DashboardData = await fetchDashboard();
        const tape: TapeItem[] = [];
        const indices = Array.isArray(data?.indices) ? data.indices : [];
        const gainers = Array.isArray(data?.gainers) ? data.gainers.slice(0, 6) : [];
        const crypto = Array.isArray(data?.crypto) ? data.crypto : [];
        const commodities = Array.isArray(data?.commodities) ? data.commodities : [];
        const forex = Array.isArray(data?.forex) ? data.forex : [];

        indices.forEach((idx) =>
          tape.push({
            ticker: idx.ticker,
            label: idx.name,
            price: idx.price,
            change: idx.change,
            pct: idx.change_pct,
          })
        );
        gainers.forEach((g) =>
          tape.push({
            ticker: g.ticker,
            label: g.ticker,
            price: g.price,
            change: 0,
            pct: g.change_pct,
          })
        );
        commodities.forEach((c) =>
          tape.push({
            ticker: c.ticker,
            label: c.name,
            price: c.price,
            change: 0,
            pct: c.change_pct,
          })
        );
        forex.slice(0, 4).forEach((f) =>
          tape.push({
            ticker: f.ticker,
            label: f.name,
            price: f.price,
            change: 0,
            pct: f.change_pct,
          })
        );
        crypto.forEach((c) =>
          tape.push({
            ticker: c.ticker,
            label: c.name,
            price: c.price,
            change: 0,
            pct: c.change_pct,
          })
        );

        // Only use real data if we have items with non-zero prices
        const hasValidData = tape.some((t) => t.price > 0);
        setItems(hasValidData && tape.length > 0 ? tape : DUMMY_TAPE);
      } catch {
        setItems(DUMMY_TAPE);
      }
    };
    load();
    const id = setInterval(load, 5 * 60 * 1000);
    return () => clearInterval(id);
  }, []);

  const renderItem = (item: TapeItem, i: number) => {
    const positive = item.pct >= 0;
    return (
      <span key={`${item.ticker}-${i}`} className="inline-flex items-center gap-1 mx-3 flex-shrink-0">
        <Link
          href={`/asset/${item.ticker}`}
          className="text-term-yellow text-xxs font-bold hover:text-term-orange"
        >
          {item.label}
        </Link>
        <span className="text-term-white text-xxs tabular-nums">
          {item.price > 1000
            ? item.price.toLocaleString("en-US", { maximumFractionDigits: 0 })
            : item.price.toFixed(2)}
        </span>
        <span className={`text-xxs tabular-nums font-bold ${positive ? "text-positive" : "text-negative"}`}>
          {positive ? "+" : ""}{item.pct.toFixed(2)}%
        </span>
        <span className="text-term-dim text-xxs mx-1">│</span>
      </span>
    );
  };

  return (
    <div className="h-5 bg-term-panel border-t border-term-border flex items-center overflow-hidden relative">
      <div className="ticker-scroll flex whitespace-nowrap">
        {items.map((item, i) => renderItem(item, i))}
        {items.map((item, i) => renderItem(item, i + items.length))}
      </div>
    </div>
  );
}
