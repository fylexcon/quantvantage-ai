from fastapi import APIRouter, HTTPException, Query
from database import get_supabase_service_client
from schemas import SentimentCreate, SentimentRead, SentimentSummary
from datetime import datetime, timedelta, timezone
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sentiment", tags=["Sentiment"])

@router.post("", response_model=SentimentRead, status_code=201)
async def create_sentiment(payload: SentimentCreate):
    supabase = get_supabase_service_client()
    row = payload.model_dump()
    
    try:
        # Upsert: Handles duplicate dedup_hash gracefully
        result = (
            supabase.table("sentiment_history")
            .upsert(row, on_conflict="dedup_hash")
            .execute()
        )
    except Exception as exc:
        logger.error(f"Supabase error: {exc}")
        raise HTTPException(status_code=500, detail="Database error")
        
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to insert data")
        
    return result.data[0]


@router.get("/{ticker}", response_model=List[SentimentRead])
async def get_sentiment(ticker: str, limit: int = Query(5, ge=1, le=100)):
    supabase = get_supabase_service_client()
    result = (
        supabase.table("sentiment_history")
        .select("*")
        .eq("ticker", ticker.upper())
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


@router.get("/{ticker}/summary", response_model=SentimentSummary)
async def get_sentiment_summary(ticker: str):
    supabase = get_supabase_service_client()
    # 24-hour aggregate stats
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    
    result = (
        supabase.table("sentiment_history")
        .select("*")
        .eq("ticker", ticker.upper())
        .gte("created_at", cutoff)
        .execute()
    )
    
    rows = result.data
    
    if not rows:
        return SentimentSummary(
            ticker=ticker.upper(),
            average_score=0.0,
            dominant_sentiment="neutral",
            total_articles=0
        )
        
    total_articles = sum(r.get("article_count", 0) for r in rows)
    
    avg_score = sum(r.get("score", 0.0) for r in rows) / len(rows)
    
    if avg_score > 0.15:
        dominant_sentiment = "bullish"
    elif avg_score < -0.15:
        dominant_sentiment = "bearish"
    else:
        dominant_sentiment = "neutral"
        
    return SentimentSummary(
        ticker=ticker.upper(),
        average_score=avg_score,
        dominant_sentiment=dominant_sentiment,
        total_articles=total_articles
    )
