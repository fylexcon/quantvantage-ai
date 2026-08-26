"""Sentiment ingestion and retrieval endpoints.

Receives AI-analyzed financial sentiment from n8n automation,
persists to Supabase, and exposes historical/aggregated queries.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from database import get_supabase_service_client
from models.schemas import SentimentCreate, SentimentRead, SentimentSummary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sentiment", tags=["Sentiment"])


def _compute_headline_hash(analysis: dict[str, Any], ticker: str) -> str:
    """Derive a deterministic hash from the analysis summary + ticker for dedup."""
    summary = analysis.get("summary", "")
    raw = f"{ticker}:{summary}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _parse_timestamp(ts_string: str) -> datetime:
    """Parse an ISO-8601 timestamp string from n8n into a timezone-aware datetime."""
    cleaned = ts_string.strip()
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        # Fallback: strip known n8n suffixes like [UTC] and retry
        for suffix in ("[UTC]", "[GMT]", " UTC", " GMT"):
            if cleaned.endswith(suffix):
                cleaned = cleaned[: -len(suffix)].strip()
                break
        parsed = datetime.fromisoformat(cleaned)

    # Ensure timezone-aware (default to UTC if naive)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


# ---------------------------------------------------------------------------
# POST /api/sentiment — Ingest sentiment from n8n
# ---------------------------------------------------------------------------


@router.post("", response_model=SentimentRead, status_code=201)
async def ingest_sentiment(payload: SentimentCreate) -> Any:
    """Receive and persist an AI-analyzed sentiment payload from n8n."""

    raw_timestamp = _parse_timestamp(payload.timestamp)

    # Auto-generate headline hash for deduplication if not provided
    headline_hash = payload.headline_hash or _compute_headline_hash(
        payload.analysis, payload.ticker
    )

    row: dict[str, Any] = {
        "ticker": payload.ticker,
        "source": payload.source,
        "analysis": payload.analysis,
        "headline_hash": headline_hash,
        "raw_timestamp": raw_timestamp.isoformat(),
    }
    if payload.tenant_id is not None:
        row["tenant_id"] = str(payload.tenant_id)

    try:
        supabase = get_supabase_service_client()

        # Upsert: skip if this headline was already ingested (deduplication)
        result = (
            supabase.table("sentiment_history")
            .upsert(row, on_conflict="headline_hash")
            .execute()
        )
    except Exception as exc:
        logger.error("Supabase write failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=f"Database unavailable: {exc}",
        ) from exc

    if not result.data:
        raise HTTPException(status_code=500, detail="Supabase insert returned no data.")

    inserted = result.data[0]

    logger.info(
        "Sentiment ingested | ticker=%s sentiment=%s score=%s",
        payload.ticker,
        payload.analysis.get("sentiment"),
        payload.analysis.get("score"),
    )

    # Preserve the original debug prints for terminal visibility
    print(f"\n🚀 NEW SENTIMENT RECEIVED FOR {payload.ticker} 🚀")
    print(f"Sentiment: {payload.analysis.get('sentiment')}")
    print(f"Score: {payload.analysis.get('score')}")
    print(f"Summary: {payload.analysis.get('summary')}\n")

    return inserted


# ---------------------------------------------------------------------------
# GET /api/sentiment/{ticker} — Historical sentiment for a ticker
# ---------------------------------------------------------------------------


@router.get("/{ticker}", response_model=list[SentimentRead])
async def get_sentiment_history(
    ticker: str,
    limit: int = Query(default=50, ge=1, le=200),
) -> Any:
    """Fetch historical sentiment rows for a given ticker, newest first."""

    normalized_ticker = ticker.strip().upper()
    supabase = get_supabase_service_client()

    result = (
        supabase.table("sentiment_history")
        .select("*")
        .eq("ticker", normalized_ticker)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    return result.data


# ---------------------------------------------------------------------------
# GET /api/sentiment/{ticker}/summary — Aggregated 24h snapshot
# ---------------------------------------------------------------------------


@router.get("/{ticker}/summary", response_model=SentimentSummary)
async def get_sentiment_summary(ticker: str) -> Any:
    """Return an aggregated sentiment snapshot for the last 24 hours."""

    normalized_ticker = ticker.strip().upper()
    supabase = get_supabase_service_client()

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    result = (
        supabase.table("sentiment_history")
        .select("*")
        .eq("ticker", normalized_ticker)
        .gte("created_at", cutoff)
        .order("created_at", desc=True)
        .execute()
    )

    rows = result.data
    total = len(rows)

    if total == 0:
        return SentimentSummary(
            ticker=normalized_ticker,
            total_articles=0,
            avg_score_24h=None,
            dominant_sentiment_24h=None,
            last_updated=None,
        )

    # Compute average score
    scores = [
        r["analysis"]["score"]
        for r in rows
        if isinstance(r.get("analysis"), dict) and isinstance(r["analysis"].get("score"), (int, float))
    ]
    avg_score = round(sum(scores) / len(scores), 4) if scores else None

    # Compute dominant sentiment
    sentiment_counts: dict[str, int] = {}
    for r in rows:
        s = r.get("analysis", {}).get("sentiment")
        if isinstance(s, str):
            sentiment_counts[s] = sentiment_counts.get(s, 0) + 1
    dominant = max(sentiment_counts, key=sentiment_counts.get) if sentiment_counts else None  # type: ignore[arg-type]

    last_updated_str = rows[0].get("created_at")
    last_updated = datetime.fromisoformat(last_updated_str) if last_updated_str else None

    return SentimentSummary(
        ticker=normalized_ticker,
        total_articles=total,
        avg_score_24h=avg_score,
        dominant_sentiment_24h=dominant,
        last_updated=last_updated,
    )
