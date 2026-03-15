"use client";

import { useEffect, useRef, useMemo } from "react";
import { createChart, ColorType, IChartApi } from "lightweight-charts";
import type { CandleData } from "@/lib/api";

/** Generate dummy chart data when real data is empty - always show something */
function getDummyCandles(): CandleData[] {
  const out: CandleData[] = [];
  let base = 100;
  const now = new Date();
  for (let i = 252; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const open = base;
    const change = (i % 5 - 2) * 0.5;
    const close = base * (1 + change / 100);
    const high = Math.max(open, close) * 1.01;
    const low = Math.min(open, close) * 0.99;
    base = close;
    out.push({
      time: d.toISOString().slice(0, 10),
      open: Math.round(open * 100) / 100,
      high: Math.round(high * 100) / 100,
      low: Math.round(low * 100) / 100,
      close: Math.round(close * 100) / 100,
      volume: 50_000_000 + (i % 10) * 5_000_000,
    });
  }
  return out;
}

interface PriceChartProps {
  data: CandleData[];
  height?: number;
}

export default function PriceChart({ data, height = 350 }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const chartData = useMemo(() => (data?.length ? data : getDummyCandles()), [data]);

  useEffect(() => {
    if (!containerRef.current || !chartData.length) return;

    if (chartRef.current) {
      chartRef.current.remove();
    }

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#000000" },
        textColor: "#707088",
        fontFamily: "Consolas, 'SF Mono', monospace",
        fontSize: 10,
      },
      grid: {
        vertLines: { color: "#0c0c1a" },
        horzLines: { color: "#0c0c1a" },
      },
      crosshair: {
        vertLine: { color: "#FF6A00", width: 1, style: 2, labelBackgroundColor: "#FF6A00" },
        horzLine: { color: "#FF6A00", width: 1, style: 2, labelBackgroundColor: "#FF6A00" },
      },
      width: containerRef.current.clientWidth,
      height,
      timeScale: { borderColor: "#1a1a35", timeVisible: false },
      rightPriceScale: { borderColor: "#1a1a35" },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: "#00CC00",
      downColor: "#FF2020",
      borderUpColor: "#00CC00",
      borderDownColor: "#FF2020",
      wickUpColor: "#00CC00",
      wickDownColor: "#FF2020",
    });

    candleSeries.setData(
      chartData.map((d) => ({
        time: d.time as string,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      })) as any
    );

    const volumeSeries = chart.addHistogramSeries({
      color: "#1565C0",
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    });
    volumeSeries.setData(
      chartData.map((d) => ({
        time: d.time as string,
        value: d.volume,
        color: d.close >= d.open ? "rgba(0,204,0,0.2)" : "rgba(255,32,32,0.2)",
      })) as any
    );

    chart.timeScale().fitContent();
    chartRef.current = chart;

    const handleResize = () => {
      if (containerRef.current) chart.applyOptions({ width: containerRef.current.clientWidth });
    };
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartRef.current = null;
    };
  }, [chartData, height]);

  return <div ref={containerRef} className="border border-term-border overflow-hidden" style={{ height }} />;
}
