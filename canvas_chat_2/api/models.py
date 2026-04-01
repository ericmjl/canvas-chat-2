"""SQLAlchemy models for Canvas Chat API."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from canvas_chat_2.api.db import Base


def _uuid_str() -> str:
    """Return a UUID string for primary keys.

    :returns: Random UUID string.
    """

    return str(uuid4())


def _utc_now() -> datetime:
    """Return the current UTC timestamp.

    :returns: Timezone-aware UTC datetime.
    """

    return datetime.now(timezone.utc)


class Conversation(Base):
    """Conversation root entity."""

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid_str)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )


class MessageNode(Base):
    """Graph node representing one message."""

    __tablename__ = "message_nodes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid_str)
    conversation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("conversations.id"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    parent_node_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("message_nodes.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )


class MessageEdge(Base):
    """Graph edge linking two message nodes."""

    __tablename__ = "message_edges"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid_str)
    conversation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("conversations.id"), index=True, nullable=False
    )
    source_node_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("message_nodes.id"), nullable=False
    )
    target_node_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("message_nodes.id"), nullable=False
    )
    label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )


class ProviderConfig(Base):
    """Provider + model configuration for LiteLLM routing."""

    __tablename__ = "provider_configs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    litellm_model: Mapped[str] = mapped_column(String(128), nullable=False)
    api_key_env_var: Mapped[str | None] = mapped_column(String(128), nullable=True)
    api_base: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
