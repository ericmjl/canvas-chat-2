"""Integration tests for the Canvas Chat FastAPI API."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from canvas_chat_2.api import db as api_db
from canvas_chat_2.api.main import create_app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Create a test client backed by an isolated SQLite database.

    :param tmp_path: pytest-provided temporary path fixture.
    :param monkeypatch: pytest monkeypatch fixture.
    :yields TestClient: FastAPI TestClient bound to an isolated SQLite file.
    """

    db_path = tmp_path / "canvas_chat_test.db"
    test_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    test_session_local = sessionmaker(
        bind=test_engine, autoflush=False, autocommit=False
    )
    monkeypatch.setattr(api_db, "engine", test_engine)
    monkeypatch.setattr(api_db, "SessionLocal", test_session_local)

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    test_engine.dispose()


def test_graph_crud_and_reply(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise graph CRUD and AI reply generation flow."""

    monkeypatch.setattr(
        "canvas_chat_2.api.routes_chat.generate_reply_text",
        lambda history, provider: "Generated reply",
    )

    graph_resp = client.get("/conversations/default/graph")
    assert graph_resp.status_code == 200
    graph = graph_resp.json()
    assert graph["conversation"]["id"] == "default"
    assert graph["nodes"] == []
    assert graph["edges"] == []

    node_resp = client.post(
        "/conversations/default/nodes",
        json={"role": "human", "content": "Hello", "x": 10.0, "y": 20.0},
    )
    assert node_resp.status_code == 201
    source_node = node_resp.json()

    # @spec CCHAT-AUTOREPLY-001, CCHAT-AUTOREPLY-002
    graph_after_human = client.get("/conversations/default/graph")
    assert graph_after_human.status_code == 200
    payload_after_human = graph_after_human.json()
    assert len(payload_after_human["nodes"]) == 2
    assert len(payload_after_human["edges"]) == 1
    auto_reply_node = next(
        node for node in payload_after_human["nodes"] if node["id"] != source_node["id"]
    )
    auto_reply_edge = payload_after_human["edges"][0]
    assert auto_reply_node["role"] == "ai"
    assert auto_reply_node["parent_node_id"] == source_node["id"]
    assert auto_reply_edge["source_node_id"] == source_node["id"]
    assert auto_reply_edge["target_node_id"] == auto_reply_node["id"]
    assert auto_reply_edge["label"] == "auto-reply"

    patch_resp = client.patch(
        f"/nodes/{source_node['id']}",
        json={"content": "Hello world", "x": 50.0, "y": 60.0},
    )
    assert patch_resp.status_code == 200
    patched_node = patch_resp.json()
    assert patched_node["content"] == "Hello world"
    assert patched_node["x"] == 50.0
    assert patched_node["y"] == 60.0

    target_resp = client.post(
        "/conversations/default/nodes",
        json={"role": "system", "content": "Instructions", "x": 300.0, "y": 60.0},
    )
    assert target_resp.status_code == 201
    target_node = target_resp.json()

    edge_resp = client.post(
        "/conversations/default/edges",
        json={"source_node_id": source_node["id"], "target_node_id": target_node["id"]},
    )
    assert edge_resp.status_code == 201
    created_edge = edge_resp.json()

    reply_resp = client.post(
        f"/nodes/{source_node['id']}/reply",
        json={"provider_id": "default"},
    )
    assert reply_resp.status_code == 201
    reply_node = reply_resp.json()
    assert reply_node["role"] == "ai"
    assert reply_node["parent_node_id"] == source_node["id"]
    assert reply_node["content"] == "Generated reply"

    graph_after_reply = client.get("/conversations/default/graph")
    assert graph_after_reply.status_code == 200
    graph_payload = graph_after_reply.json()
    assert len(graph_payload["nodes"]) == 4
    assert len(graph_payload["edges"]) == 3

    delete_resp = client.delete(f"/edges/{created_edge['id']}")
    assert delete_resp.status_code == 204

    graph_after_delete = client.get("/conversations/default/graph")
    assert graph_after_delete.status_code == 200
    assert len(graph_after_delete.json()["edges"]) == 2


def test_blank_human_message_does_not_create_canned_reply(client: TestClient) -> None:
    """Ensure canned auto-reply is only created for non-empty human messages."""

    # @spec CCHAT-AUTOREPLY-003
    node_resp = client.post(
        "/conversations/default/nodes",
        json={"role": "human", "content": "   ", "x": 10.0, "y": 20.0},
    )
    assert node_resp.status_code == 201
    created_node = node_resp.json()

    graph_resp = client.get("/conversations/default/graph")
    assert graph_resp.status_code == 200
    payload = graph_resp.json()
    assert len(payload["nodes"]) == 1
    assert payload["nodes"][0]["id"] == created_node["id"]
    assert len(payload["edges"]) == 0


def test_provider_management(client: TestClient) -> None:
    """Validate listing and updating provider configurations."""

    providers_resp = client.get("/providers")
    assert providers_resp.status_code == 200
    providers = providers_resp.json()
    assert any(provider["id"] == "default" for provider in providers)

    put_resp = client.put(
        "/providers/local-ollama",
        json={
            "litellm_model": "ollama/llama3.1",
            "api_base": "http://127.0.0.1:11434",
            "is_active": True,
        },
    )
    assert put_resp.status_code == 200
    updated = put_resp.json()
    assert updated["id"] == "local-ollama"
    assert updated["is_active"] is True

    providers_resp_2 = client.get("/providers")
    assert providers_resp_2.status_code == 200
    providers_2 = providers_resp_2.json()
    default_provider = next(p for p in providers_2 if p["id"] == "default")
    local_provider = next(p for p in providers_2 if p["id"] == "local-ollama")
    assert default_provider["is_active"] is False
    assert local_provider["is_active"] is True
