"use client";

import { Activity } from "lucide-react";

const TICKERS = ["AAPL", "IONQ", "BTC-USD", "ETH-USD", "SOL-USD"] as const;

interface DashboardHeaderProps {
  selectedTicker: string;
  onTickerChange: (ticker: string) => void;
}

export default function DashboardHeader({
  selectedTicker,
  onTickerChange,
}: DashboardHeaderProps) {
  return (
    <header className="relative flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 shadow-lg shadow-emerald-500/20">
          <Activity className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="bg-gradient-to-r from-white to-slate-400 bg-clip-text text-2xl font-bold tracking-tight text-transparent">
            QuantVantage AI
          </h1>
          <p className="text-xs text-slate-500">
            Real-time sentiment & price forecasting
          </p>
        </div>
      </div>

      {/* Ticker Selector */}
      <nav className="flex flex-wrap gap-2" aria-label="Asset selector">
        {TICKERS.map((t) => {
          const isActive = t === selectedTicker;
          return (
            <button
              key={t}
              onClick={() => onTickerChange(t)}
              className={`
                rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200
                ${
                  isActive
                    ? "bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 text-emerald-400 ring-1 ring-emerald-500/40 shadow-lg shadow-emerald-500/10"
                    : "bg-white/[0.04] text-slate-400 ring-1 ring-white/[0.06] hover:bg-white/[0.08] hover:text-slate-200"
                }
              `}
            >
              {t}
            </button>
          );
        })}
      </nav>
    </header>
  );
}
