from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SubscriptionTier(str, Enum):
    starter = "starter"
    growth = "growth"
    enterprise = "enterprise"


class ProfileRole(str, Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class TenantBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    subscription_tier: SubscriptionTier = SubscriptionTier.starter


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    subscription_tier: SubscriptionTier | None = None


class TenantRead(TenantBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileBase(BaseModel):
    tenant_id: UUID
    role: ProfileRole = ProfileRole.member


class UserProfileCreate(UserProfileBase):
    id: UUID


class UserProfileUpdate(BaseModel):
    role: ProfileRole | None = None


class UserProfileRead(UserProfileBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class ApiKeyBase(BaseModel):
    tenant_id: UUID
    is_active: bool = True


class ApiKeyCreate(ApiKeyBase):
    key_hash: str = Field(min_length=32, max_length=255)


class ApiKeyUpdate(BaseModel):
    is_active: bool | None = None


class ApiKeyRead(ApiKeyBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PredictionBase(BaseModel):
    tenant_id: UUID
    ticker: str = Field(min_length=1, max_length=16, pattern=r"^[A-Z0-9.-]+$")
    forecast_data: dict[str, Any]

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().upper()
        return value


class PredictionCreate(PredictionBase):
    pass


class PredictionRead(PredictionBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Prediction API (PyTorch Inference)
# ---------------------------------------------------------------------------


class PredictionRequest(BaseModel):
    """Inbound payload for the prediction endpoint."""

    ticker: str = Field(min_length=1, max_length=16, pattern=r"^[A-Za-z0-9.-]+$")
    days_ahead: int = Field(default=7, ge=1, le=30)

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().upper()
        return value


class PredictionResponse(BaseModel):
    """Outbound payload returned by the prediction endpoint."""

    ticker: str
    current_price: float
    forecasted_prices: list[float]
    confidence_intervals: dict[str, list[float]]
    model_version: str


# ---------------------------------------------------------------------------
# Sentiment History
# ---------------------------------------------------------------------------


class SentimentCreate(BaseModel):
    """Inbound payload shape from n8n automation pipeline."""

    source: str = Field(min_length=1, max_length=255)
    ticker: str = Field(min_length=1, max_length=16, pattern=r"^[A-Z0-9.-]+$")
    analysis: dict[str, Any]
    timestamp: str = Field(description="ISO-8601 timestamp string from n8n")
    tenant_id: UUID | None = None
    headline_hash: str | None = Field(
        default=None,
        max_length=64,
        description="SHA-256 hash of the article headline for deduplication",
    )

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().upper()
        return value


class SentimentRead(BaseModel):
    """Response model for sentiment history rows."""

    id: UUID
    tenant_id: UUID | None
    ticker: str
    source: str
    analysis: dict[str, Any]
    headline_hash: str | None
    raw_timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SentimentSummary(BaseModel):
    """Aggregated sentiment snapshot for a ticker (24-hour window)."""

    ticker: str
    total_articles: int
    avg_score_24h: float | None
    dominant_sentiment_24h: str | None
    last_updated: datetime | None