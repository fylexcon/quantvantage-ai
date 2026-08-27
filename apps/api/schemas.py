from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class SentimentCreate(BaseModel):
    ticker: str
    score: float
    sentiment_label: str
    article_count: int
    dedup_hash: str

class SentimentRead(SentimentCreate):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class SentimentSummary(BaseModel):
    ticker: str
    average_score: float
    dominant_sentiment: str
    total_articles: int
