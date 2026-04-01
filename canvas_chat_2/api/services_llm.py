"""LiteLLM integration service."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from litellm import completion
from loguru import logger

if TYPE_CHECKING:
    from canvas_chat_2.api.models import ProviderConfig
    from canvas_chat_2.api.schemas import MessageRole


def generate_reply_text(
    history: list[tuple["MessageRole", str]], provider: "ProviderConfig"
) -> str:
    """Generate an AI reply with LiteLLM.

    :param history: Ordered chat history as (role, content) tuples.
    :param provider: Provider configuration to resolve model and credentials.
    :returns: Model-generated assistant text.
    :raises RuntimeError: If the provider is misconfigured or response is empty.
    """

    kwargs: dict[str, str | list[dict[str, str]]] = {
        "model": provider.litellm_model,
        "messages": [{"role": role, "content": content} for role, content in history],
    }
    if provider.api_base:
        kwargs["api_base"] = provider.api_base
    if provider.api_key_env_var:
        api_key = os.getenv(provider.api_key_env_var)
        if not api_key:
            msg = (
                f"Provider {provider.id!r} expects env var "
                f"{provider.api_key_env_var!r}, but it is not set."
            )
            raise RuntimeError(msg)
        kwargs["api_key"] = api_key

    logger.info(
        "Generating reply with provider={} model={}",
        provider.id,
        provider.litellm_model,
    )
    response = completion(**kwargs)
    text = response.choices[0].message.content if response.choices else None
    if not text:
        raise RuntimeError("LiteLLM returned an empty response.")
    return text
