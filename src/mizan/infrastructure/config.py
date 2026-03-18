"""
Application configuration using Pydantic Settings.

Loads configuration from environment variables with validation.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================================
    # Database Configuration
    # ==========================================================================
    database_url: str = Field(
        default="postgresql+asyncpg://mizan:mizan@localhost:5432/mizan",
        description="PostgreSQL connection URL (async)",
    )
    db_pool_size: int = Field(default=10, ge=1, le=100)
    db_max_overflow: int = Field(default=20, ge=0, le=100)
    db_echo: bool = Field(default=False, description="Echo SQL queries")

    # ==========================================================================
    # Redis Configuration
    # ==========================================================================
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    redis_pool_size: int = Field(default=10, ge=1, le=100)
    cache_ttl: int = Field(default=3600, ge=0, description="Cache TTL in seconds")

    # ==========================================================================
    # API Configuration
    # ==========================================================================
    api_host: str = Field(default="0.0.0.0")  # nosec B104
    api_port: int = Field(default=8000, ge=1, le=65535)
    debug: bool = Field(default=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")

    # ==========================================================================
    # Security
    # ==========================================================================
    secret_key: str = Field(
        default="change-me-in-production",
        min_length=16,
        description="Secret key for signing",
    )
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins. Set to ['*'] only for local dev.",
    )
    api_key: str = Field(
        default="",
        description=(
            "API key required for library mutation endpoints (X-API-Key header). "
            "Empty string disables auth — only for local dev."
        ),
    )

    # ==========================================================================
    # Data Sources
    # ==========================================================================
    tanzil_data_path: str = Field(
        default="./data/tanzil",
        description="Path to Tanzil XML files",
    )
    masaq_data_path: str = Field(
        default="./data/masaq",
        description="Path to MASAQ dataset",
    )

    # ==========================================================================
    # Integrity Verification
    # ==========================================================================
    expected_quran_checksum: str = Field(
        default="",
        description="Expected SHA256 of complete Quran text",
    )
    fail_on_integrity_error: bool = Field(
        default=True,
        description="Halt on integrity violation",
    )

    # ==========================================================================
    # Experimental Features
    # ==========================================================================
    enable_semantic_analysis: bool = Field(
        default=True,
        description="Enable Tier 4 semantic features (Library + Embedding Search)",
    )
    enable_structural_tools: bool = Field(
        default=False,
        description="Enable Tier 5 structural tools",
    )

    # ==========================================================================
    # Embedding Configuration (Tier 4 - Semantic Search)
    # ==========================================================================
    embedding_provider: str = Field(
        default="local",
        description="Embedding provider: 'local' (sentence-transformers) or 'gemini'",
    )
    embedding_model: str = Field(
        default="intfloat/multilingual-e5-base",
        description=(
            "Model identifier. For local: HuggingFace model name. "
            "For gemini: 'gemini-embedding-2-preview' or 'text-embedding-004'"
        ),
    )
    embedding_dimension: int = Field(
        default=768,
        ge=64,
        le=4096,
        description="Dimension of embedding vectors (must match the model's output)",
    )
    embedding_batch_size: int = Field(
        default=32,
        ge=1,
        le=512,
        description="Number of texts to embed in a single batch",
    )
    gemini_api_key: str = Field(
        default="",
        description="Google Gemini API key (required when embedding_provider='gemini')",
    )
    embedding_fallback_provider: str = Field(
        default="",
        description=(
            "Fallback embedding provider when primary fails. "
            "Empty string = no fallback. 'local' or 'gemini'. "
            "IMPORTANT: fallback model must produce vectors with the same dimension "
            "as the primary model, otherwise stored vectors will be incompatible."
        ),
    )
    embedding_fallback_model: str = Field(
        default="intfloat/multilingual-e5-base",
        description="Model name for the fallback provider (must match primary dimension).",
    )

    # ==========================================================================
    # Cross-Encoder Re-ranking (Phase 3)
    # ==========================================================================
    enable_reranking: bool = Field(
        default=False,
        description=(
            "Enable cross-encoder re-ranking of search results. "
            "When enabled, top candidates are re-scored by a cross-encoder "
            "model for dramatically improved result quality."
        ),
    )
    reranker_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        description=(
            "Cross-encoder model for re-ranking. Default is ms-marco-MiniLM-L-6-v2 "
            "(~80MB, fast, no custom code). For better multilingual support, use "
            "jinaai/jina-reranker-v2-base-multilingual (requires einops + trust_remote_code)."
        ),
    )
    reranker_top_k: int = Field(
        default=30,
        ge=1,
        le=200,
        description=(
            "Number of top candidates to pass to the cross-encoder for re-ranking. "
            "Higher values improve recall but increase latency."
        ),
    )

    # ==========================================================================
    # Observability — Sentry
    # ==========================================================================
    sentry_dsn: str = Field(
        default="",
        description=(
            "Sentry DSN for error tracking. Empty string disables Sentry (default for local dev)."
        ),
    )
    sentry_environment: str = Field(
        default="development",
        description="Sentry environment tag (e.g. 'production', 'staging', 'development')",
    )
    sentry_traces_sample_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Sentry performance traces sample rate (0.0 to 1.0)",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL uses asyncpg driver."""
        if not v.startswith("postgresql+asyncpg://"):
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug and self.secret_key != "change-me-in-production"  # nosec B105


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Settings are loaded once and cached for performance.
    """
    return Settings()
