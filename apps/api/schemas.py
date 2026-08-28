from datetime import datetime
from uuid import UUID
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict

class SentimentCreate(BaseModel):
    ticker: str
    score: Optional[float] = None
    sentiment_label: Optional[str] = None
    article_count: Optional[int] = None
    dedup_hash: Optional[str] = None
    
    # New fields for flexibility and batch processing compatibility
    model_prediction: Optional[float] = None
    tenant_id: Optional[Union[UUID, str]] = None
    analysis: Optional[dict] = None
    headline_hash: Optional[str] = None
    raw_timestamp: Optional[str] = None

class SentimentRead(SentimentCreate):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class SentimentResponse(SentimentRead):
    pass

class SentimentSummary(BaseModel):
    ticker: str
    total_articles: int
    avg_score_24h: Optional[float] = None
    dominant_sentiment_24h: Optional[str] = None
    last_updated: Optional[datetime] = None
