"use client";

import { useEffect, useRef } from "react";
import { createChart, ColorType, IChartApi } from "lightweight-charts";
import type { CandleData } from "@/lib/api";

interface PriceChartProps {
  data: CandleData[];
  height?: number;
}

export default function PriceChart({ data, height = 350 }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current || !data.length) return;

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
      data.map((d) => ({
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
      data.map((d) => ({
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
  }, [data, height]);

  if (!data.length) {
    return (
      <div className="flex items-center justify-center bg-term-black border border-term-border text-term-dim text-xxs" style={{ height }}>
        NO CHART DATA AVAILABLE
      </div>
    );
  }

  return <div ref={containerRef} className="border border-term-border overflow-hidden" />;
}
