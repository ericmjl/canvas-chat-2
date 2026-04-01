"""Configuration for the Canvas Chat API."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the API server.

    :ivar model_config: Pydantic settings model configuration.
    :ivar database_url: SQLAlchemy database URL.
    :ivar cors_origins: Allowed CORS origins for the frontend.
    :ivar default_provider_id: Provider identifier used for default routing.
    :ivar default_litellm_model: LiteLLM model string (provider/model format).
    :ivar enable_canned_autoreply: Enable canned AI replies for human messages.
    :ivar canned_autoreply_text: Canned AI reply text when auto-reply is enabled.
    """

    model_config = SettingsConfigDict(
        env_prefix="CANVAS_CHAT_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    database_url: str = "sqlite:///./canvas_chat_2.db"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:4173",
            "http://localhost:3000",
        ]
    )
    default_provider_id: str = "default"
    default_litellm_model: str = "openai/gpt-4o-mini"
    enable_canned_autoreply: bool = True
    canned_autoreply_text: str = (
        "Canned AI reply: thanks for the message. "
        "Configure a provider to get model-generated responses."
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache API settings.

    :returns: Parsed settings.
    """

    return Settings()
