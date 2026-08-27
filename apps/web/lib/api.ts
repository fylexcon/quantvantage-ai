/**
 * QuantVantage API client — typed fetchers for the FastAPI backend.
 *
 * Falls back to http://localhost:8000 when NEXT_PUBLIC_API_URL is not set.
 */

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
    "upper_1σ": number[];
    "lower_1σ": number[];
    "upper_2σ": number[];
    "lower_2σ": number[];
  };
  model_version: string;
}

// ---------------------------------------------------------------------------
// Recharts-ready coordinate type
// ---------------------------------------------------------------------------

export interface ForecastDataPoint {
  day: string;
  price: number;
  lower_1: number;
  upper_1: number;
  lower_2: number;
  upper_2: number;
  /** Confidence band rendered as [lower, upper] for Recharts Area */
  band_1σ: [number, number];
  band_2σ: [number, number];
}

// ---------------------------------------------------------------------------
// Data transformation
// ---------------------------------------------------------------------------

/**
 * Maps parallel arrays from the API into an array of coordinate objects
 * that Recharts can consume directly.
 */
export function toChartData(res: PredictionResponse): ForecastDataPoint[] {
  return res.forecasted_prices.map((price, i) => ({
    day: `+${i + 1}d`,
    price: round2(price),
    lower_1: round2(res.confidence_intervals["lower_1σ"][i]),
    upper_1: round2(res.confidence_intervals["upper_1σ"][i]),
    lower_2: round2(res.confidence_intervals["lower_2σ"][i]),
    upper_2: round2(res.confidence_intervals["upper_2σ"][i]),
    band_1σ: [
      round2(res.confidence_intervals["lower_1σ"][i]),
      round2(res.confidence_intervals["upper_1σ"][i]),
    ],
    band_2σ: [
      round2(res.confidence_intervals["lower_2σ"][i]),
      round2(res.confidence_intervals["upper_2σ"][i]),
    ],
  }));
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}

// ---------------------------------------------------------------------------
// Fetcher functions
// ---------------------------------------------------------------------------

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body}`);
  }

  return res.json() as Promise<T>;
}

/**
 * GET /api/sentiment/{ticker}/summary
 */
export function getSentimentSummary(
  ticker: string
): Promise<SentimentSummary> {
  return apiFetch<SentimentSummary>(
    `/api/sentiment/${encodeURIComponent(ticker)}/summary`
  );
}

/**
 * GET /api/sentiment/{ticker}?limit=N — recent headlines
 */
export function getSentimentHistory(
  ticker: string,
  limit = 5
): Promise<SentimentRead[]> {
  return apiFetch<SentimentRead[]>(
    `/api/sentiment/${encodeURIComponent(ticker)}?limit=${limit}`
  );
}

/**
 * POST /api/predict/{ticker}
 */
export function postPrediction(
  ticker: string,
  daysAhead = 14
): Promise<PredictionResponse> {
  return apiFetch<PredictionResponse>(
    `/api/predict/${encodeURIComponent(ticker)}`,
    {
      method: "POST",
      body: JSON.stringify({ ticker, days_ahead: daysAhead }),
    }
  );
}
