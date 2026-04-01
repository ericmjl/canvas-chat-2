"""Graph CRUD routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from canvas_chat_2.api.db import get_db
from canvas_chat_2.api.models import Conversation, MessageEdge, MessageNode
from canvas_chat_2.api.schemas import (
    EdgeCreate,
    EdgeRead,
    GraphRead,
    NodeCreate,
    NodeRead,
    NodeUpdate,
)
from canvas_chat_2.api.settings import get_settings

router = APIRouter()
settings = get_settings()


def _get_or_create_conversation(db: Session, conversation_id: str) -> Conversation:
    """Load a conversation by id or create it if absent.

    :param db: Database session.
    :param conversation_id: Conversation identifier.
    :returns: Existing or newly created conversation.
    """

    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        conversation = Conversation(id=conversation_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    return conversation


@router.get("/conversations/{conversation_id}/graph", response_model=GraphRead)
def get_graph(conversation_id: str, db: Session = Depends(get_db)) -> GraphRead:
    """Return nodes and edges for a conversation graph."""

    conversation = _get_or_create_conversation(db, conversation_id)
    nodes = list(
        db.scalars(
            select(MessageNode).where(MessageNode.conversation_id == conversation_id)
        )
    )
    edges = list(
        db.scalars(
            select(MessageEdge).where(MessageEdge.conversation_id == conversation_id)
        )
    )
    return GraphRead(conversation=conversation, nodes=nodes, edges=edges)


@router.post(
    "/conversations/{conversation_id}/nodes",
    response_model=NodeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_node(
    conversation_id: str, payload: NodeCreate, db: Session = Depends(get_db)
) -> MessageNode:
    """Create a message node in a conversation."""

    _get_or_create_conversation(db, conversation_id)
    if payload.parent_node_id:
        parent = db.get(MessageNode, payload.parent_node_id)
        if parent is None or parent.conversation_id != conversation_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent node not found in this conversation.",
            )

    node = MessageNode(
        conversation_id=conversation_id,
        role=payload.role,
        content=payload.content,
        x=payload.x,
        y=payload.y,
        parent_node_id=payload.parent_node_id,
    )
    db.add(node)
    db.flush()

    # @spec CCHAT-AUTOREPLY-001, CCHAT-AUTOREPLY-002
    if (
        settings.enable_canned_autoreply
        and payload.role == "human"
        and payload.content.strip() != ""
    ):
        reply_node = MessageNode(
            conversation_id=conversation_id,
            role="ai",
            content=settings.canned_autoreply_text,
            x=payload.x + 280.0,
            y=payload.y + 40.0,
            parent_node_id=node.id,
        )
        db.add(reply_node)
        db.flush()
        db.add(
            MessageEdge(
                conversation_id=conversation_id,
                source_node_id=node.id,
                target_node_id=reply_node.id,
                label="auto-reply",
            )
        )

    db.commit()
    db.refresh(node)
    return node


@router.patch("/nodes/{node_id}", response_model=NodeRead)
def update_node(
    node_id: str, payload: NodeUpdate, db: Session = Depends(get_db)
) -> MessageNode:
    """Patch mutable node fields."""

    node = db.get(MessageNode, node_id)
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Node not found."
        )

    if payload.role is not None:
        node.role = payload.role
    if payload.content is not None:
        node.content = payload.content
    if payload.x is not None:
        node.x = payload.x
    if payload.y is not None:
        node.y = payload.y

    db.commit()
    db.refresh(node)
    return node


@router.post(
    "/conversations/{conversation_id}/edges",
    response_model=EdgeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_edge(
    conversation_id: str, payload: EdgeCreate, db: Session = Depends(get_db)
) -> MessageEdge:
    """Create an edge between two nodes."""

    _get_or_create_conversation(db, conversation_id)
    source = db.get(MessageNode, payload.source_node_id)
    target = db.get(MessageNode, payload.target_node_id)
    if source is None or target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source or target node does not exist.",
        )
    if (
        source.conversation_id != conversation_id
        or target.conversation_id != conversation_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Edges can only connect nodes from the same conversation.",
        )

    edge = MessageEdge(
        conversation_id=conversation_id,
        source_node_id=payload.source_node_id,
        target_node_id=payload.target_node_id,
        label=payload.label,
    )
    db.add(edge)
    db.commit()
    db.refresh(edge)
    return edge


@router.delete("/edges/{edge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_edge(edge_id: str, db: Session = Depends(get_db)) -> None:
    """Delete one edge by identifier."""

    edge = db.get(MessageEdge, edge_id)
    if edge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Edge not found."
        )
    db.delete(edge)
    db.commit()
