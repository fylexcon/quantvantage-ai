"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { useSentimentData } from "@/lib/useSentimentData";

interface SentimentChartProps {
  ticker: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    value: number;
    name?: string;
    color?: string;
    dataKey?: string;
    payload: unknown;
  }>;
  label?: string;
}

const CustomTooltip = ({
  active,
  payload,
  label,
}: CustomTooltipProps) => {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-slate-900/95 px-4 py-3 shadow-2xl backdrop-blur-sm">
        <p className="mb-1 text-xs font-medium text-slate-400">
          {label ? new Date(label).toLocaleDateString() : ""}
        </p>
        {payload.map((entry, index) => (
          <p
            key={index}
            className="text-sm font-medium"
            style={{ color: entry.color }}
          >
            {entry.name}: {entry.value?.toFixed(2)}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function SentimentChart({ ticker }: SentimentChartProps) {
  const { data, loading, error } = useSentimentData(ticker);

  if (loading) {
    return (
      <div className="card-glass flex h-96 w-full flex-col items-center justify-center p-4">
        <p className="text-sm text-slate-500 animate-pulse">Loading sentiment data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-96 w-full flex-col items-center justify-center rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-red-400 shadow-sm">
        <p className="text-sm font-medium">Error loading data</p>
        <p className="text-xs">{error.message}</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="card-glass flex h-96 w-full flex-col items-center justify-center p-4">
        <p className="text-sm text-slate-500">No sentiment data available for {ticker}.</p>
      </div>
    );
  }

  return (
    <div className="card-glass flex h-96 w-full flex-col p-4">
      <h3 className="mb-4 text-sm font-medium text-slate-400">
        AI Sentiment vs Model Prediction
      </h3>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{
              top: 5,
              right: 20,
              left: 0,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
            <XAxis
              dataKey="created_at"
              tickFormatter={(val) => new Date(val).toLocaleDateString()}
              tick={{ fill: "#64748b", fontSize: 12 }}
              tickMargin={10}
              tickLine={false}
              axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
            />
            <YAxis
              tick={{ fill: "#64748b", fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(val) => val.toFixed(1)}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend iconType="circle" wrapperStyle={{ fontSize: '12px' }} />
            <Line
              type="monotone"
              dataKey="score"
              name="AI Sentiment"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="model_prediction"
              name="Model Prediction"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
