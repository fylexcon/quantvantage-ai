"use client";

import { useEffect, useState } from "react";
import useSWR from "swr";
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import { LineChart as LineChartIcon, TrendingUp } from "lucide-react";
import {
  postPrediction,
  toChartData,
  type PredictionResponse,
  type ForecastDataPoint,
} from "@/lib/api";

interface ForecastChartProps {
  ticker: string;
  daysAhead?: number;
}

/** Skeleton placeholder */
function ChartSkeleton({ showColdStart }: { showColdStart: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16">
      <div className="relative h-12 w-12">
        <div className="absolute inset-0 animate-ping rounded-full bg-emerald-500/20" />
        <div className="relative flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10">
          <LineChartIcon className="h-6 w-6 animate-pulse text-emerald-400" />
        </div>
      </div>
      <p className="text-sm text-slate-500">Running forecast model…</p>
      {showColdStart && (
        <div className="flex items-center gap-2 rounded-lg bg-amber-500/10 px-3 py-2 text-xs text-amber-400 ring-1 ring-amber-500/20">
          <div className="h-2 w-2 animate-pulse rounded-full bg-amber-400" />
          Spinning up backend engine…
        </div>
      )}
    </div>
  );
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: {
    dataKey?: string | number;
    value?: number | number[] | string;
    [key: string]: unknown;
  }[];
  label?: string;
}

/** Custom tooltip */
function ChartTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const p = payload.find((e) => e.dataKey === "price");
  const b1 = payload.find((e) => e.dataKey === "band_1σ");
  return (
    <div className="rounded-xl border border-white/[0.08] bg-slate-900/95 px-4 py-3 shadow-2xl backdrop-blur-sm">
      <p className="mb-1 text-xs font-medium text-slate-400">{label}</p>
      {p && (
        <p className="text-base font-bold text-white">
          {new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(Number(p.value))}
        </p>
      )}
      {b1 && Array.isArray(b1.value) && (
        <p className="mt-1 text-xs text-slate-500">
          1σ: {new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(Number(b1.value[0]))} – {new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(Number(b1.value[1]))}
        </p>
      )}
    </div>
  );
}

export default function ForecastChart({
  ticker,
  daysAhead = 14,
}: ForecastChartProps) {
  const {
    data: rawData,
    error,
    isLoading,
  } = useSWR<PredictionResponse>(
    ["/api/predict", ticker, daysAhead],
    () => postPrediction(ticker, daysAhead),
    { revalidateOnFocus: false, dedupingInterval: 120_000 }
  );

  // Cold-start handling
  const [showColdStart, setShowColdStart] = useState(false);
  useEffect(() => {
    if (!isLoading) {
      setShowColdStart(false);
      return;
    }
    const t = setTimeout(() => setShowColdStart(true), 4000);
    return () => clearTimeout(t);
  }, [isLoading]);

  const chartData: ForecastDataPoint[] = rawData ? toChartData(rawData) : [];
  const currentPrice = rawData?.current_price ?? 0;

  return (
    <div className="card-glass flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-400">
          <TrendingUp className="h-4 w-4" />
          {daysAhead}-Day Price Forecast
        </div>
        {rawData && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">
              {rawData.model_version}
            </span>
            <span className="rounded-md bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-400 ring-1 ring-emerald-500/20">
              ${currentPrice.toFixed(2)}
            </span>
          </div>
        )}
      </div>

      {/* Chart */}
      {isLoading ? (
        <ChartSkeleton showColdStart={showColdStart} />
      ) : error ? (
        <div className="flex flex-col items-center gap-2 py-12 text-center">
          <LineChartIcon className="h-8 w-8 text-red-400/60" />
          <p className="text-sm text-red-400">
            Failed to load forecast for {ticker}.
          </p>
          <p className="text-xs text-slate-600">
            The prediction model may not be available for this asset.
          </p>
        </div>
      ) : (
        <div className="animate-fade-in">
          <ResponsiveContainer width="100%" height={340}>
            <ComposedChart
              data={chartData}
              margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
            >
              <defs>
                {/* 2σ band gradient */}
                <linearGradient id="grad2σ" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.08} />
                  <stop offset="100%" stopColor="#06b6d4" stopOpacity={0.02} />
                </linearGradient>
                {/* 1σ band gradient */}
                <linearGradient id="grad1σ" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity={0.2} />
                  <stop offset="100%" stopColor="#10b981" stopOpacity={0.05} />
                </linearGradient>
                {/* Price line gradient */}
                <linearGradient id="gradLine" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#10b981" />
                  <stop offset="100%" stopColor="#06b6d4" />
                </linearGradient>
              </defs>

              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255,255,255,0.04)"
                vertical={false}
              />

              <XAxis
                dataKey="day"
                tick={{ fill: "#64748b", fontSize: 11 }}
                axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: "#64748b", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(v)}
                domain={["auto", "auto"]}
                width={65}
              />

              <Tooltip content={<ChartTooltip />} />

              {/* 2σ confidence band */}
              <Area
                type="monotone"
                dataKey="band_2σ"
                fill="url(#grad2σ)"
                stroke="none"
                isAnimationActive
                animationDuration={800}
              />

              {/* 1σ confidence band */}
              <Area
                type="monotone"
                dataKey="band_1σ"
                fill="url(#grad1σ)"
                stroke="none"
                isAnimationActive
                animationDuration={800}
              />

              {/* Current price reference line */}
              <ReferenceLine
                y={currentPrice}
                stroke="#f59e0b"
                strokeDasharray="6 4"
                strokeOpacity={0.5}
                label={{
                  value: `Current $${currentPrice}`,
                  position: "insideTopRight",
                  fill: "#f59e0b",
                  fontSize: 11,
                }}
              />

              {/* Forecasted price line */}
              <Line
                type="monotone"
                dataKey="price"
                stroke="url(#gradLine)"
                strokeWidth={2.5}
                dot={{ r: 3, fill: "#10b981", stroke: "#0f172a", strokeWidth: 2 }}
                activeDot={{
                  r: 5,
                  fill: "#10b981",
                  stroke: "#0f172a",
                  strokeWidth: 2,
                }}
                isAnimationActive
                animationDuration={1000}
              />
            </ComposedChart>
          </ResponsiveContainer>

          {/* Legend */}
          <div className="mt-3 flex flex-wrap items-center justify-center gap-4 text-xs text-slate-500">
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-0.5 w-4 rounded bg-gradient-to-r from-emerald-500 to-cyan-500" />
              Forecast
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-sm bg-emerald-500/20" />
              1σ Band
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-sm bg-cyan-500/10" />
              2σ Band
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-0.5 w-4 border-t-2 border-dashed border-amber-500/50" />
              Current Price
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
