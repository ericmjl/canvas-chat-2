"""Unit tests for LiteLLM service helpers."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from canvas_chat_2.api.services_llm import generate_reply_text


@dataclass
class _Message:
    """Stub message payload for mocked LiteLLM responses."""

    content: str


@dataclass
class _Choice:
    """Stub choice payload for mocked LiteLLM responses."""

    message: _Message


@dataclass
class _Response:
    """Stub response object with LiteLLM-like choices."""

    choices: list[_Choice]


@dataclass
class _ProviderStub:
    """Minimal provider config shape for service unit tests."""

    id: str
    litellm_model: str
    api_key_env_var: str | None = None
    api_base: str | None = None


def test_generate_reply_text_uses_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return the assistant text from LiteLLM completion output."""

    captured: dict[str, object] = {}

    def fake_completion(**kwargs: object) -> _Response:
        """Capture completion call kwargs for assertions."""

        captured.update(kwargs)
        return _Response(choices=[_Choice(message=_Message(content="Hi from model"))])

    monkeypatch.setattr("canvas_chat_2.api.services_llm.completion", fake_completion)

    provider = _ProviderStub(id="default", litellm_model="openai/gpt-4o-mini")
    result = generate_reply_text(
        history=[("system", "Be concise"), ("human", "Say hi")],
        provider=provider,  # type: ignore[arg-type]
    )

    assert result == "Hi from model"
    assert captured["model"] == "openai/gpt-4o-mini"
    assert captured["messages"] == [
        {"role": "system", "content": "Be concise"},
        {"role": "human", "content": "Say hi"},
    ]


def test_generate_reply_text_raises_for_missing_env_key() -> None:
    """Raise a helpful error when the configured API key env var is missing."""

    provider = _ProviderStub(
        id="openai",
        litellm_model="openai/gpt-4o-mini",
        api_key_env_var="MISSING_API_KEY_FOR_TEST",
    )

    with pytest.raises(RuntimeError, match="MISSING_API_KEY_FOR_TEST"):
        generate_reply_text(
            history=[("human", "Hello")],
            provider=provider,  # type: ignore[arg-type]
        )
