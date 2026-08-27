"use client";

import { useEffect, useState } from "react";
import useSWR from "swr";
import { Rss, ExternalLink } from "lucide-react";
import { getSentimentHistory, type SentimentRead } from "@/lib/api";

interface RecentNewsFeedProps {
  ticker: string;
}

const SENTIMENT_BADGE: Record<string, { color: string; bg: string }> = {
  Bullish: { color: "text-emerald-300 font-bold", bg: "bg-emerald-500/20" },
  Bearish: { color: "text-red-300 font-bold", bg: "bg-red-500/20" },
  Neutral: { color: "text-amber-300 font-bold", bg: "bg-amber-500/20" },
};

function getBadgeStyle(sentiment: string | undefined) {
  if (!sentiment) return { color: "text-slate-400", bg: "bg-slate-500/15" };
  return SENTIMENT_BADGE[sentiment] ?? { color: "text-slate-400", bg: "bg-slate-500/15" };
}

function timeAgo(iso: string): string {
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60_000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
  } catch {
    return "";
  }
}

export default function RecentNewsFeed({ ticker }: RecentNewsFeedProps) {
  const {
    data,
    error,
    isLoading,
  } = useSWR<SentimentRead[]>(
    [`/api/sentiment/history`, ticker],
    () => getSentimentHistory(ticker, 5),
    { refreshInterval: 60_000 }
  );

  // Cold-start
  const [showColdStart, setShowColdStart] = useState(false);
  useEffect(() => {
    if (!isLoading) { setShowColdStart(false); return; }
    const t = setTimeout(() => setShowColdStart(true), 4000);
    return () => clearTimeout(t);
  }, [isLoading]);

  return (
    <div className="card-glass flex flex-col gap-4">
      <div className="flex items-center gap-2 text-sm font-medium text-slate-400">
        <Rss className="h-4 w-4" />
        Recent News
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse space-y-2">
              <div className="h-4 w-3/4 rounded bg-white/[0.06]" />
              <div className="h-3 w-1/2 rounded bg-white/[0.04]" />
            </div>
          ))}
          {showColdStart && (
            <div className="flex items-center gap-2 rounded-lg bg-amber-500/10 px-3 py-2 text-xs text-amber-400 ring-1 ring-amber-500/20">
              <div className="h-2 w-2 animate-pulse rounded-full bg-amber-400" />
              Spinning up backend engine…
            </div>
          )}
        </div>
      ) : error ? (
        <p className="text-sm text-red-400">Failed to load news feed.</p>
      ) : !data || data.length === 0 ? (
        <p className="py-6 text-center text-sm text-slate-600">
          No recent headlines for {ticker}.
        </p>
      ) : (
        <ul className="animate-fade-in divide-y divide-white/[0.04]">
          {data.map((item) => {
            const sentiment = item.analysis?.sentiment;
            const summary = item.analysis?.summary;
            const score = item.analysis?.score;
            const badge = getBadgeStyle(sentiment);

            return (
              <li
                key={item.id}
                className="group flex items-start gap-3 py-3 first:pt-0 last:pb-0"
              >
                {/* Sentiment badge dot */}
                <div className="mt-1.5 flex-shrink-0">
                  <div
                    className={`h-2 w-2 rounded-full ${
                      sentiment === "Bullish"
                        ? "bg-emerald-400"
                        : sentiment === "Bearish"
                        ? "bg-red-400"
                        : "bg-amber-400"
                    }`}
                  />
                </div>

                <div className="min-w-0 flex-1">
                  {/* Summary */}
                  <p className="line-clamp-2 text-sm leading-snug text-slate-300 group-hover:text-white transition-colors">
                    {summary || "No summary available."}
                  </p>

                  {/* Meta row */}
                  <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs">
                    {/* Sentiment badge */}
                    <span
                      className={`rounded-full px-2 py-0.5 font-medium ${badge.bg} ${badge.color}`}
                    >
                      {sentiment ?? "Unknown"}
                    </span>

                    {/* Score */}
                    {typeof score === "number" && (
                      <span className="text-slate-500 tabular-nums">
                        {score.toFixed(2)}
                      </span>
                    )}

                    {/* Source */}
                    <span className="flex items-center gap-1 text-slate-600">
                      <ExternalLink className="h-3 w-3" />
                      {item.source}
                    </span>

                    {/* Time */}
                    <span className="text-slate-600">
                      {timeAgo(item.created_at)}
                    </span>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
