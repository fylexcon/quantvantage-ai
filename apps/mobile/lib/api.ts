/**
 * QuantVantage API client — typed fetchers for the FastAPI backend.
 *
 * Uses native fetch with AbortController for timeout handling.
 * Wraps fetchers in @tanstack/react-query hooks for caching & refetching.
 */

import { useQuery } from '@tanstack/react-query';

const API_BASE_URL = 'https://quantvantage-ai.onrender.com';

/** Timeout for Render cold starts (75s) */
const REQUEST_TIMEOUT_MS = 75_000;

// ---------------------------------------------------------------------------
// Shared types (mirrors Pydantic schemas)
// ---------------------------------------------------------------------------

export interface SentimentSummary {
  ticker: string;
  total_articles: number;
  avg_score_24h: number | null;
  dominant_sentiment_24h: string | null;
  last_updated: string | null;
}

export interface SentimentRead {
  id: string;
  tenant_id: string | null;
  ticker: string;
  source: string;
  analysis: {
    sentiment?: string;
    score?: number;
    summary?: string;
    headline?: string;
    [key: string]: unknown;
  };
  headline_hash: string | null;
  raw_timestamp: string;
  created_at: string;
}

export interface PredictionResponse {
  ticker: string;
  current_price: number;
  forecasted_prices: number[];
  confidence_intervals: {
    'upper_1σ': number[];
    'lower_1σ': number[];
    'upper_2σ': number[];
    'lower_2σ': number[];
  };
  model_version: string;
}

// ---------------------------------------------------------------------------
// Core fetcher with timeout
// ---------------------------------------------------------------------------

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...init?.headers,
      },
    });

    if (!res.ok) {
      const body = await res.text().catch(() => '');
      throw new Error(`API ${res.status}: ${body}`);
    }

    return res.json() as Promise<T>;
  } finally {
    clearTimeout(timer);
  }
}

// ---------------------------------------------------------------------------
// Fetcher functions
// ---------------------------------------------------------------------------

/** GET /api/sentiment/{ticker}/summary */
export function getSentimentSummary(ticker: string): Promise<SentimentSummary> {
  return apiFetch<SentimentSummary>(
    `/api/sentiment/${encodeURIComponent(ticker)}/summary`
  );
}

/** GET /api/sentiment/{ticker}?limit=N — recent headlines */
export function getSentimentList(
  ticker: string,
  limit = 5
): Promise<SentimentRead[]> {
  return apiFetch<SentimentRead[]>(
    `/api/sentiment/${encodeURIComponent(ticker)}?limit=${limit}`
  );
}

/** POST /api/predict/{ticker} */
export function postPrediction(
  ticker: string,
  daysAhead = 14
): Promise<PredictionResponse> {
  return apiFetch<PredictionResponse>(
    `/api/predict/${encodeURIComponent(ticker)}`,
    {
      method: 'POST',
      body: JSON.stringify({ ticker, days_ahead: daysAhead }),
    }
  );
}

// ---------------------------------------------------------------------------
// React Query hooks
// ---------------------------------------------------------------------------

export function useSentimentSummary(ticker: string) {
  return useQuery({
    queryKey: ['sentiment-summary', ticker],
    queryFn: () => getSentimentSummary(ticker),
    staleTime: 60_000,
    retry: 2,
  });
}

export function useSentimentList(ticker: string, limit = 5) {
  return useQuery({
    queryKey: ['sentiment-list', ticker, limit],
    queryFn: () => getSentimentList(ticker, limit),
    staleTime: 60_000,
    retry: 2,
  });
}

export function usePredict(ticker: string, daysAhead = 14) {
  return useQuery({
    queryKey: ['prediction', ticker, daysAhead],
    queryFn: () => postPrediction(ticker, daysAhead),
    staleTime: 120_000,
    retry: 1,
  });
}
