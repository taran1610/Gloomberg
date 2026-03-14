"use client";

import type { SectorPerformance } from "@/lib/api";

interface MarketHeatmapProps {
  sectors: SectorPerformance[];
}

function getHeatColor(pct: number): string {
  if (pct >= 2) return "bg-green-600 text-white";
  if (pct >= 1) return "bg-green-800 text-green-200";
  if (pct >= 0.25) return "bg-green-900/60 text-green-300";
  if (pct > 0) return "bg-green-950/40 text-green-400";
  if (pct === 0) return "bg-term-surface text-term-muted";
  if (pct > -0.25) return "bg-red-950/40 text-red-400";
  if (pct > -1) return "bg-red-900/60 text-red-300";
  if (pct > -2) return "bg-red-800 text-red-200";
  return "bg-red-600 text-white";
}

export default function MarketHeatmap({ sectors }: MarketHeatmapProps) {
  if (!sectors.length) return null;

  return (
    <div className="grid grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-px bg-term-border">
      {sectors.map((s) => (
        <div
          key={s.name}
          className={`p-2 text-center cursor-default ${getHeatColor(s.change_pct)}`}
        >
          <div className="text-xxs font-bold truncate">{s.name}</div>
          <div className="text-sm font-bold mt-0.5">
            {s.change_pct >= 0 ? "+" : ""}
            {s.change_pct.toFixed(2)}%
          </div>
        </div>
      ))}
    </div>
  );
}
