from __future__ import annotations

import os
from types import SimpleNamespace

from tier2.llm_client import LLMClient


def get_llm():
    """
    Provide a simple LLM interface with an invoke(prompt) method.
    Uses the existing LLMClient configuration and model selection.
    """
    try:
        client = LLMClient(model=os.getenv("LLM_MODEL"))
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: Failed to initialize LLMClient in get_llm: {exc}")

        class _UnavailableLLM:
            def invoke(self, prompt: str):  # pragma: no cover - fallback path
                raise RuntimeError(f"LLM unavailable: {exc}")  # noqa: B904

        return _UnavailableLLM()

    class _LLMWrap:
        def __init__(self, inner_client: LLMClient):
            self._inner_client = inner_client

        def invoke(self, prompt: str):
            content = self._inner_client.generate_chat(
                system_prompt="You are a professional business writer. Provide clear, structured content with no caveats.",
                user_prompt=prompt,
                max_tokens=900,
                temperature=0.4,
            )
            return SimpleNamespace(content=content)

    return _LLMWrap(client)
