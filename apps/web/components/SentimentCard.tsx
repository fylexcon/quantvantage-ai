"use client";

import { useEffect, useState } from "react";
import useSWR from "swr";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Newspaper,
  BarChart3,
  Clock,
} from "lucide-react";
import { getSentimentSummary, type SentimentSummary } from "@/lib/api";

interface SentimentCardProps {
  ticker: string;
}

const SENTIMENT_CONFIG: Record<
  string,
  { color: string; bg: string; ring: string; Icon: typeof TrendingUp }
> = {
  Bullish: {
    color: "text-emerald-300",
    bg: "bg-emerald-500/20",
    ring: "ring-emerald-500/40",
    Icon: TrendingUp,
  },
  Bearish: {
    color: "text-red-300",
    bg: "bg-red-500/20",
    ring: "ring-red-500/40",
    Icon: TrendingDown,
  },
  Neutral: {
    color: "text-amber-300",
    bg: "bg-amber-500/20",
    ring: "ring-amber-500/40",
    Icon: Minus,
  },
};

function getSentimentStyle(sentiment: string | null) {
  if (!sentiment) return SENTIMENT_CONFIG.Neutral;
  return SENTIMENT_CONFIG[sentiment] ?? SENTIMENT_CONFIG.Neutral;
}

function formatScore(score: number | null): string {
  if (score === null || score === undefined) return "—";
  return score.toFixed(2);
}

function formatTime(iso: string | null): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
}

/** Skeleton placeholder while loading */
function Skeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-6 w-28 rounded-md bg-white/[0.06]" />
      <div className="h-10 w-36 rounded-md bg-white/[0.06]" />
      <div className="flex gap-6">
        <div className="h-4 w-20 rounded bg-white/[0.06]" />
        <div className="h-4 w-24 rounded bg-white/[0.06]" />
      </div>
    </div>
  );
}

export default function SentimentCard({ ticker }: SentimentCardProps) {
  const {
    data,
    error,
    isLoading,
  } = useSWR<SentimentSummary>(
    [`/api/sentiment/summary`, ticker],
    () => getSentimentSummary(ticker),
    { refreshInterval: 60_000, revalidateOnFocus: true }
  );

  // Cold-start detection: show helper after 4s of loading
  const [showColdStart, setShowColdStart] = useState(false);
  useEffect(() => {
    if (!isLoading) {
      setShowColdStart(false);
      return;
    }
    const timer = setTimeout(() => setShowColdStart(true), 4000);
    return () => clearTimeout(timer);
  }, [isLoading]);

  const style = getSentimentStyle(data?.dominant_sentiment_24h ?? null);
  const SentimentIcon = style.Icon;

  return (
    <div className="card-glass flex flex-col gap-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-400">
          <Newspaper className="h-4 w-4" />
          24h Sentiment
        </div>
        {data && (
          <span className="animate-fade-in text-xs text-slate-500">
            <Clock className="mr-1 inline-block h-3 w-3" />
            {formatTime(data.last_updated)}
          </span>
        )}
      </div>

      {/* Body */}
      {isLoading ? (
        <>
          <Skeleton />
          {showColdStart && (
            <div className="flex items-center gap-2 rounded-lg bg-amber-500/10 px-3 py-2 text-xs text-amber-400 ring-1 ring-amber-500/20">
              <div className="h-2 w-2 animate-pulse rounded-full bg-amber-400" />
              Spinning up backend engine…
            </div>
          )}
        </>
      ) : error ? (
        <div className="rounded-lg bg-red-500/10 px-4 py-3 text-sm text-red-400 ring-1 ring-red-500/20">
          Failed to load sentiment data.
        </div>
      ) : data && data.total_articles === 0 ? (
        <div className="flex flex-col items-center gap-2 py-6 text-center text-sm text-slate-500">
          <Newspaper className="h-8 w-8 text-slate-600" />
          No articles processed in the last 24 hours.
        </div>
      ) : data ? (
        <div className="animate-fade-in space-y-5">
          {/* Dominant Sentiment Badge */}
          <div className="flex items-center gap-3">
            <div
              className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold ring-1 ${style.bg} ${style.color} ${style.ring}`}
            >
              <SentimentIcon className="h-4 w-4" />
              {data.dominant_sentiment_24h ?? "Unknown"}
            </div>
          </div>

          {/* Metrics Row */}
          <div className="grid grid-cols-2 gap-4">
            {/* Average Score */}
            <div className="space-y-1">
              <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                Avg Score
              </p>
              <div className="flex items-baseline gap-1">
                <BarChart3 className="h-4 w-4 text-slate-500" />
                <span className="text-2xl font-bold tabular-nums text-white">
                  {formatScore(data.avg_score_24h)}
                </span>
              </div>
              {/* Mini score bar */}
              {data.avg_score_24h !== null && (
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/[0.06]">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-red-500 via-amber-400 to-emerald-500 transition-all duration-700"
                    style={{
                      width: `${Math.min(100, Math.max(0, (data.avg_score_24h + 1) * 50))}%`,
                    }}
                  />
                </div>
              )}
            </div>

            {/* Total Articles */}
            <div className="space-y-1">
              <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                Articles
              </p>
              <div className="flex items-baseline gap-1">
                <Newspaper className="h-4 w-4 text-slate-500" />
                <span className="text-2xl font-bold tabular-nums text-white">
                  {data.total_articles}
                </span>
              </div>
              <p className="text-xs text-slate-600">processed (24h)</p>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
