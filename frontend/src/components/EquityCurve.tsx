"use client";

import { useEffect, useRef } from "react";
import { createChart, ColorType, IChartApi } from "lightweight-charts";
import type { EquityCurvePoint } from "@/lib/api";

interface EquityCurveProps {
  data: EquityCurvePoint[];
  height?: number;
}

export default function EquityCurve({ data, height = 250 }: EquityCurveProps) {
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
        textColor: "#808080",
        fontFamily: "Consolas, 'SF Mono', monospace",
        fontSize: 10,
      },
      grid: {
        vertLines: { color: "#111122" },
        horzLines: { color: "#111122" },
      },
      width: containerRef.current.clientWidth,
      height,
      timeScale: { borderColor: "#1e1e3a" },
      rightPriceScale: { borderColor: "#1e1e3a" },
    });

    const finalValue = data[data.length - 1]?.value ?? 0;
    const startValue = data[0]?.value ?? 0;
    const isPositive = finalValue >= startValue;

    const series = chart.addAreaSeries({
      lineColor: isPositive ? "#00C805" : "#FF3333",
      topColor: isPositive ? "rgba(0,200,5,0.2)" : "rgba(255,51,51,0.2)",
      bottomColor: "transparent",
      lineWidth: 2,
    });

    series.setData(
      data.map((d) => ({ time: d.date as string, value: d.value })) as any
    );
    chart.timeScale().fitContent();
    chartRef.current = chart;

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
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
      <div
        className="flex items-center justify-center bg-term-black border border-term-border text-term-dim text-xs"
        style={{ height }}
      >
        NO EQUITY DATA
      </div>
    );
  }

  return (
    <div ref={containerRef} className="border border-term-border overflow-hidden" />
  );
}
