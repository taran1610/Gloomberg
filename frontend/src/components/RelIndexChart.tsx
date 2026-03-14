"use client";

import { useEffect, useRef } from "react";
import { createChart, ColorType, IChartApi } from "lightweight-charts";
import type { RelIndexData } from "@/lib/api";

interface RelIndexChartProps {
  data: RelIndexData;
  height?: number;
}

export default function RelIndexChart({ data, height = 400 }: RelIndexChartProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  const scatter = data.scatter || [];
  const overlay = data.overlay || [];
  const stats = "stats" in data ? data.stats : null;

  useEffect(() => {
    if (!overlayRef.current || overlay.length < 2) {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
      return;
    }

    if (chartRef.current) {
      chartRef.current.remove();
    }

    const chart = createChart(overlayRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#000000" },
        textColor: "#707088",
        fontFamily: "Consolas, monospace",
        fontSize: 10,
      },
      grid: { vertLines: { color: "#0c0c1a" }, horzLines: { color: "#0c0c1a" } },
      width: overlayRef.current.clientWidth,
      height,
      timeScale: { borderColor: "#1a1a35" },
      rightPriceScale: { borderColor: "#1a1a35" },
    });

    const tickerSeries = chart.addLineSeries({
      color: "#FF8C00",
      lineWidth: 2,
      title: `${data.ticker} (Base 100)`,
    });
    tickerSeries.setData(
      overlay.map((o) => ({ time: o.date as string, value: o.ticker })) as any
    );

    const benchSeries = chart.addLineSeries({
      color: "#EAEAEA",
      lineWidth: 2,
      lineStyle: 2,
      title: `${data.benchmark} (Base 100)`,
    });
    benchSeries.setData(
      overlay.map((o) => ({ time: o.date as string, value: o.benchmark })) as any
    );

    chart.timeScale().fitContent();
    chartRef.current = chart;

    const handleResize = () => {
      if (overlayRef.current) chart.applyOptions({ width: overlayRef.current.clientWidth });
    };
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartRef.current = null;
    };
  }, [data, overlay, height]);

  if (!data.scatter?.length && !overlay.length) {
    const err = "error" in data ? (data as { error?: string }).error : null;
    return (
      <div
        className="flex items-center justify-center bg-term-black border border-term-border text-term-dim text-xxs"
        style={{ height }}
      >
        {err || "NO REL INDEX DATA"}
      </div>
    );
  }

  const xMin = scatter.length ? Math.min(...scatter.map((p) => p.x)) : -10;
  const xMax = scatter.length ? Math.max(...scatter.map((p) => p.x)) : 10;
  const yMin = scatter.length ? Math.min(...scatter.map((p) => p.y)) : -20;
  const yMax = scatter.length ? Math.max(...scatter.map((p) => p.y)) : 20;
  const xRange = Math.max(xMax - xMin, 0.1);
  const yRange = Math.max(yMax - yMin, 0.1);
  const pad = 40;
  const w = 400;
  const h = 280;

  const toX = (x: number) => pad + ((x - xMin) / xRange) * (w - 2 * pad);
  const toY = (y: number) => h - pad - ((y - yMin) / yRange) * (h - 2 * pad);

  return (
    <div className="flex flex-col gap-2">
      {/* Scatter Plot */}
      {scatter.length > 0 && (
        <div className="border border-term-border p-2 bg-term-black">
          <div className="text-xxs text-term-orange font-bold mb-1">
            {data.ticker} % Change vs {data.benchmark} % Change
          </div>
          <div className="text-xxs text-term-white mb-1">{data.equation}</div>
          <svg width="100%" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="xMidYMid meet">
            {stats && (
              <line
                x1={toX(xMin)}
                y1={toY(stats.alpha + stats.raw_beta * xMin)}
                x2={toX(xMax)}
                y2={toY(stats.alpha + stats.raw_beta * xMax)}
                stroke="#FF2020"
                strokeWidth={1.5}
              />
            )}
            {scatter.map((p, i) => (
              <circle
                key={i}
                cx={toX(p.x)}
                cy={toY(p.y)}
                r={3}
                fill="#FFD600"
                opacity={0.8}
              />
            ))}
            <text x={10} y={h - 5} fill="#707088" fontSize="9">
              SPX % Chg
            </text>
            <text x={w - 60} y={15} fill="#707088" fontSize="9">
              {data.ticker} % Chg
            </text>
          </svg>
        </div>
      )}

      {/* Normalized Price Overlay */}
      {overlay.length > 0 && (
        <div className="border border-term-border">
          <div className="terminal-header">
            NORMALIZED PRICE OVERLAY (Base 100) | Weekly {data.period.toUpperCase()} | {data.start_date} - {data.end_date}
          </div>
          <div ref={overlayRef} className="overflow-hidden" />
        </div>
      )}
    </div>
  );
}
