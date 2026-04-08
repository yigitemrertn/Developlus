"""
Developlus API — Global Configuration
Tüm ortam değişkenleri Pydantic Settings ile tip-güvenli okunur.
"""
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Uygulama
    app_name: str = "Developlus API"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    # Veritabanı
    database_url: str = "postgresql+asyncpg://developlus_user:password@localhost:5432/developlus"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # JWT
    jwt_secret_key: str = "fallback-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # LiteLLM Proxy
    litellm_proxy_url: str = "http://localhost:4000"
    litellm_master_key: str = "sk-developlus-litellm-master-key"

    # Dashscope (Qwen — direkt bağlantı için yedek)
    dashscope_api_key: str = ""

    # LLM defaults
    default_model: str = "qwen-turbo"
    default_temperature: float = 0.7
    default_max_tokens: int = 4096

    # CORS
    cors_origins: str = "http://localhost,http://localhost:3000"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str) -> str:
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
