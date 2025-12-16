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
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1, le=65535)
    debug: bool = Field(default=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )

    # ==========================================================================
    # Security
    # ==========================================================================
    secret_key: str = Field(
        default="change-me-in-production",
        min_length=16,
        description="Secret key for signing",
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
        default=False,
        description="Enable Tier 4 semantic features",
    )
    enable_structural_tools: bool = Field(
        default=False,
        description="Enable Tier 5 structural tools",
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
        return not self.debug and self.secret_key != "change-me-in-production"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Settings are loaded once and cached for performance.
    """
    return Settings()
