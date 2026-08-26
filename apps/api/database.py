from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from supabase import Client, create_client


class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    supabase_service_key: str = ""

    model_config = SettingsConfigDict(
        env_file=(".env", "apps/api/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_supabase_client() -> Client:
    """Anon-key client (respects RLS) for frontend-proxied requests."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)


@lru_cache
def get_supabase_service_client() -> Client:
    """Service-role client (bypasses RLS) for trusted backend writes."""
    settings = get_settings()
    key = settings.supabase_service_key or settings.supabase_key
    return create_client(settings.supabase_url, key)