from __future__ import annotations

import os
from typing import Any, Dict


class LLMClient:
    """
    Minimal LLM client supporting OpenAI. Extendable to other providers.
    """

    def __init__(self, model: str | None = None) -> None:
        self.provider = os.getenv("LLM_PROVIDER", "openai")
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        if self.provider == "openai":
            from openai import OpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY is required for LLM generation.")
            self._client = OpenAI(api_key=api_key)
        else:
            raise RuntimeError(f"Unsupported LLM provider: {self.provider}")

    def generate_chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 800, temperature: float = 0.3) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
