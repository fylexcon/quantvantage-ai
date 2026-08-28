from fastapi import APIRouter, HTTPException, Query, Request
from database import get_supabase_service_client
from schemas import SentimentCreate, SentimentRead, SentimentResponse, SentimentSummary
from utils.notifications import send_sentiment_alert
from datetime import datetime, timedelta, timezone
from typing import List
from collections import Counter
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
    score = payload.analysis.get("score", 0.0)
    article_count = payload.analysis.get("article_count", 1)
    features = [score, 1.0, float(article_count)]
    
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
        sentiment=payload.analysis.get("sentiment", "neutral"),
        score=payload.analysis.get("score", 0.0),
        summary=str(payload.analysis.get("summary", "")),
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
        .limit(20)
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
        
    valid_scores = []
    total_articles = 0
    sentiment_list = []
    
    for r in rows:
        analysis = r.get("analysis") or {}
        
        score = r.get("score")
        if score is None:
            score = analysis.get("score", 0.0)
        valid_scores.append(float(score))
        
        ac = r.get("article_count")
        if ac is None:
            ac = analysis.get("article_count", 1)
        total_articles += int(ac)
        
        sentiment = r.get("sentiment_label")
        if not sentiment:
            sentiment = analysis.get("sentiment", "neutral")
        sentiment_list.append(sentiment.capitalize())

    avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    sentiment_counts = Counter(sentiment_list)
    dominant_sentiment = sentiment_counts.most_common(1)[0][0] if sentiment_counts else "Neutral"
        
    return SentimentSummary(
        ticker=ticker.upper(),
        avg_score_24h=avg_score,
        dominant_sentiment_24h=dominant_sentiment,
        total_articles=total_articles,
        last_updated=datetime.now(timezone.utc)
    )
