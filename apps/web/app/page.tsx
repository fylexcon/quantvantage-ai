"use client";

import { useState } from "react";
import DashboardHeader from "@/components/DashboardHeader";
import SentimentCard from "@/components/SentimentCard";
import ForecastChart from "@/components/ForecastChart";
import RecentNewsFeed from "@/components/RecentNewsFeed";

export default function Home() {
  const [ticker, setTicker] = useState("AAPL");

  return (
    <main className="mx-auto min-h-screen max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <DashboardHeader selectedTicker={ticker} onTickerChange={setTicker} />

      {/* Dashboard Grid */}
      <div className="mt-8 grid gap-6 stagger lg:grid-cols-3">
        {/* Left column — Sentiment */}
        <div className="flex flex-col gap-6 lg:col-span-1 animate-fade-in">
          <SentimentCard ticker={ticker} />
          <RecentNewsFeed ticker={ticker} />
        </div>

        {/* Right column — Forecast chart */}
        <div className="lg:col-span-2 animate-fade-in">
          <ForecastChart ticker={ticker} daysAhead={14} />
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-12 border-t border-white/[0.04] pt-6 text-center text-xs text-slate-600">
        QuantVantage AI · Real-time sentiment & PyTorch forecasting ·{" "}
        <span className="text-slate-500">{ticker}</span>
      </footer>
    </main>
  );
}