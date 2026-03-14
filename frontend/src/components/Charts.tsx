"use client";

import dynamic from "next/dynamic";

export const PriceChart = dynamic(
  () => import("./PriceChart").then((m) => m.default),
  { ssr: false, loading: () => <div className="h-[350px] bg-term-black border border-term-border flex items-center justify-center text-term-dim text-xxs">Loading chart...</div> }
);

export const RelIndexChart = dynamic(
  () => import("./RelIndexChart").then((m) => m.default),
  { ssr: false, loading: () => <div className="h-[320px] bg-term-black border border-term-border flex items-center justify-center text-term-dim text-xxs">Loading chart...</div> }
);

export const EquityCurve = dynamic(
  () => import("./EquityCurve").then((m) => m.default),
  { ssr: false, loading: () => <div className="h-[220px] bg-term-black border border-term-border flex items-center justify-center text-term-dim text-xxs">Loading chart...</div> }
);

export const RelValueChart = dynamic(
  () => import("./RelValueChart").then((m) => m.default),
  { ssr: false, loading: () => <div className="h-[320px] bg-term-black border border-term-border flex items-center justify-center text-term-dim text-xxs">Loading chart...</div> }
);
