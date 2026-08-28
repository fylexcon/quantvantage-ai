from fastapi import APIRouter, HTTPException, Query, Request
from database import get_supabase_service_client
from schemas import SentimentCreate, SentimentRead, SentimentResponse, SentimentSummary
from utils.notifications import send_sentiment_alert
from datetime import datetime, timedelta, timezone
from typing import List
import logging
import asyncio
import torch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sentiment", tags=["Sentiment"])

def _run_inference(model, features: list[float]) -> float:
    """Run model inference with no_grad in eval mode."""
    model.eval()
    with torch.no_grad():
        x = torch.tensor([features], dtype=torch.float32)
        device = next(model.parameters()).device
        x = x.to(device)
        pred = model(x)
        return float(pred.item())

@router.post("", response_model=SentimentResponse, status_code=201)
async def create_sentiment(payload: SentimentCreate, request: Request):
    supabase = get_supabase_service_client()
    row = payload.model_dump(exclude_none=True)
    
    # Extract features for prediction: score, impact_weight (default 1.0), article_count
    # You can customize impact_weight extraction if added to payload later
    features = [payload.score, 1.0, float(payload.article_count)]
    
    model = request.app.state.sentiment_model
    try:
        prediction = await asyncio.to_thread(_run_inference, model, features)
        row["model_prediction"] = prediction
    except Exception as exc:
        logger.error(f"Sentiment inference failed: {exc}")
        row["model_prediction"] = None

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

    # Fire Telegram alert in background — never blocks the response
    asyncio.create_task(send_sentiment_alert(
        ticker=payload.ticker,
        sentiment=payload.sentiment_label,
        score=payload.score,
        summary=str(payload.analysis or ""),
    ))

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
