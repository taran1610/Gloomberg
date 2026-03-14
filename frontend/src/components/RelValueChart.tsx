"use client";

import { useEffect, useRef, useMemo } from "react";
import { createChart, ColorType, IChartApi } from "lightweight-charts";
import type { RelValueData } from "@/lib/api";

const PEER_COLORS = [
  "#E6E600",
  "#00CC88",
  "#FF8C00",
  "#AA66FF",
  "#00BFFF",
  "#FF6B6B",
  "#4ECDC4",
  "#FFE66D",
];

interface RelValueChartProps {
  data: RelValueData | null;
  visibleTickers: string[];
  height?: number;
}

export default function RelValueChart({
  data,
  visibleTickers,
  height = 320,
}: RelValueChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const apiRef = useRef<IChartApi | null>(null);

  const seriesByTicker = useMemo(() => {
    if (!data?.chart_series) return [];
    return visibleTickers
      .filter((t) => data.chart_series[t]?.length)
      .map((t) => ({ ticker: t, points: data.chart_series[t] }));
  }, [data, visibleTickers]);

  useEffect(() => {
    if (!chartRef.current || seriesByTicker.length === 0) {
      if (apiRef.current) {
        apiRef.current.remove();
        apiRef.current = null;
      }
      return;
    }

    if (apiRef.current) apiRef.current.remove();

    const chart = createChart(chartRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#000000" },
        textColor: "#707088",
        fontFamily: "Consolas, monospace",
        fontSize: 10,
      },
      grid: { vertLines: { color: "#0c0c1a" }, horzLines: { color: "#0c0c1a" } },
      width: chartRef.current.clientWidth,
      height,
      timeScale: { borderColor: "#1a1a35" },
      rightPriceScale: { borderColor: "#1a1a35" },
    });

    seriesByTicker.forEach(({ ticker, points }, i) => {
      const color = PEER_COLORS[i % PEER_COLORS.length];
      const series = chart.addLineSeries({
        color,
        lineWidth: 2,
        title: ticker,
      });
      series.setData(
        points.map((p) => ({ time: p.date as string, value: p.value })) as any
      );
    });

    chart.timeScale().fitContent();
    apiRef.current = chart;

    const handleResize = () => {
      if (chartRef.current) chart.applyOptions({ width: chartRef.current.clientWidth });
    };
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      apiRef.current = null;
    };
  }, [seriesByTicker, height]);

  if (!data) return null;
  if (seriesByTicker.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-term-black border border-term-border text-term-dim text-xxs"
        style={{ height }}
      >
        No chart data. Select peers above.
      </div>
    );
  }

  return <div ref={chartRef} className="overflow-hidden" />;
}
