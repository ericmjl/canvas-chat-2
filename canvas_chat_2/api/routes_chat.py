"""Chat and provider routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from canvas_chat_2.api.db import get_db
from canvas_chat_2.api.models import MessageEdge, MessageNode, ProviderConfig
from canvas_chat_2.api.schemas import (
    NodeRead,
    ProviderConfigRead,
    ProviderConfigUpdate,
    ReplyRequest,
)
from canvas_chat_2.api.services_llm import generate_reply_text

router = APIRouter()


def _resolve_provider(db: Session, provider_id: str | None) -> ProviderConfig:
    """Resolve provider by id or active provider.

    :param db: Database session.
    :param provider_id: Optional explicit provider identifier.
    :returns: Resolved provider configuration.
    :raises HTTPException: If no provider can be resolved.
    """

    if provider_id is not None:
        provider = db.get(ProviderConfig, provider_id)
    else:
        provider = db.scalar(
            select(ProviderConfig).where(ProviderConfig.is_active.is_(True))
        )
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No provider configuration available.",
        )
    return provider


def _node_history(db: Session, node: MessageNode) -> list[tuple[str, str]]:
    """Build ordered node ancestry as a chat history.

    :param db: Database session.
    :param node: Starting node for ancestry traversal.
    :returns: Ordered `(role, content)` tuples from root to node.
    """

    history: list[tuple[str, str]] = []
    current = node
    while current is not None:
        history.append((current.role, current.content))
        if current.parent_node_id is None:
            break
        parent = db.get(MessageNode, current.parent_node_id)
        if parent is None:
            break
        current = parent
    history.reverse()
    return history


@router.get("/providers", response_model=list[ProviderConfigRead])
def list_providers(db: Session = Depends(get_db)) -> list[ProviderConfig]:
    """List all provider configurations."""

    return list(db.scalars(select(ProviderConfig).order_by(ProviderConfig.id)))


@router.put("/providers/{provider_id}", response_model=ProviderConfigRead)
def upsert_provider(
    provider_id: str, payload: ProviderConfigUpdate, db: Session = Depends(get_db)
) -> ProviderConfig:
    """Create or update one provider configuration."""

    provider = db.get(ProviderConfig, provider_id)
    if provider is None:
        if payload.litellm_model is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="litellm_model is required when creating a provider.",
            )
        provider = ProviderConfig(id=provider_id, litellm_model=payload.litellm_model)
        db.add(provider)

    if payload.litellm_model is not None:
        provider.litellm_model = payload.litellm_model
    if payload.api_key_env_var is not None:
        provider.api_key_env_var = payload.api_key_env_var
    if payload.api_base is not None:
        provider.api_base = payload.api_base
    if payload.is_active is not None:
        provider.is_active = payload.is_active
        if payload.is_active:
            others = list(
                db.scalars(
                    select(ProviderConfig).where(ProviderConfig.id != provider_id)
                )
            )
            for other in others:
                other.is_active = False

    db.commit()
    db.refresh(provider)
    return provider


@router.post(
    "/nodes/{node_id}/reply",
    response_model=NodeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_reply_node(
    node_id: str, payload: ReplyRequest, db: Session = Depends(get_db)
) -> MessageNode:
    """Generate an AI reply and append it as a child node."""

    source_node = db.get(MessageNode, node_id)
    if source_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Source node not found."
        )

    provider = _resolve_provider(db, payload.provider_id)
    history = _node_history(db, source_node)
    try:
        reply_text = generate_reply_text(history=history, provider=provider)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    child_node = MessageNode(
        conversation_id=source_node.conversation_id,
        role="ai",
        content=reply_text,
        x=source_node.x + 280.0,
        y=source_node.y + 40.0,
        parent_node_id=source_node.id,
    )
    db.add(child_node)
    db.flush()

    edge = MessageEdge(
        conversation_id=source_node.conversation_id,
        source_node_id=source_node.id,
        target_node_id=child_node.id,
        label="reply",
    )
    db.add(edge)
    db.commit()
    db.refresh(child_node)
    return child_node
