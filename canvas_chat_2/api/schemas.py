"""Pydantic schemas for Canvas Chat API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

MessageRole = Literal["human", "ai", "system"]


class ConversationRead(BaseModel):
    """Conversation payload."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None
    created_at: datetime


class NodeCreate(BaseModel):
    """Request payload for creating a message node.

    :ivar role: Node role.
    :ivar content: Message text.
    :ivar x: Canvas x coordinate.
    :ivar y: Canvas y coordinate.
    :ivar parent_node_id: Optional parent node identifier.
    """

    role: MessageRole
    content: str
    x: float
    y: float
    parent_node_id: str | None = None


class NodeUpdate(BaseModel):
    """Request payload for updating a node."""

    role: MessageRole | None = None
    content: str | None = None
    x: float | None = None
    y: float | None = None


class NodeRead(BaseModel):
    """Message node payload."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: MessageRole
    content: str
    x: float
    y: float
    parent_node_id: str | None
    created_at: datetime


class EdgeCreate(BaseModel):
    """Request payload for creating an edge."""

    source_node_id: str
    target_node_id: str
    label: str | None = None


class EdgeRead(BaseModel):
    """Edge payload."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    source_node_id: str
    target_node_id: str
    label: str | None
    created_at: datetime


class GraphRead(BaseModel):
    """Conversation graph payload."""

    conversation: ConversationRead
    nodes: list[NodeRead]
    edges: list[EdgeRead]


class ProviderConfigRead(BaseModel):
    """Provider configuration payload."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    litellm_model: str
    api_key_env_var: str | None
    api_base: str | None
    is_active: bool


class ProviderConfigUpdate(BaseModel):
    """Request payload for provider updates."""

    litellm_model: str | None = None
    api_key_env_var: str | None = None
    api_base: str | None = None
    is_active: bool | None = None


class ReplyRequest(BaseModel):
    """Request payload to generate an AI reply."""

    provider_id: str | None = None
