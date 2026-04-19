"""
scimsim.llm
===========
Unified LLM interface supporting Anthropic and OpenAI.
"""

from __future__ import annotations
import json
import re
from typing import Any


class LLMClient:
    """Thin wrapper around Anthropic / OpenAI that returns plain text."""

    def __init__(self, provider: str, api_key: str, model: str):
        self.provider = provider.lower()
        self.model = model
        self._client = self._build_client(api_key)

    def _build_client(self, api_key: str) -> Any:
        if self.provider == "anthropic":
            try:
                import anthropic
                return anthropic.Anthropic(api_key=api_key)
            except ImportError:
                raise ImportError(
                    "Install the Anthropic SDK:  pip install anthropic"
                )
        elif self.provider == "openai":
            try:
                import openai
                return openai.OpenAI(api_key=api_key)
            except ImportError:
                raise ImportError(
                    "Install the OpenAI SDK:  pip install openai"
                )
        else:
            raise ValueError(f"Unknown provider: {self.provider!r}. Use 'anthropic' or 'openai'.")

    def complete(self, system: str, user: str, max_tokens: int = 1200) -> str:
        """Return the model's text response."""
        if self.provider == "anthropic":
            msg = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return msg.content[0].text

        else:  # openai
            resp = self._client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
            )
            return resp.choices[0].message.content

    def complete_json(self, system: str, user: str, max_tokens: int = 1200) -> dict | list:
        """Return parsed JSON. Retries once on parse failure."""
        system_json = system + "\n\nRespond with valid JSON only. No markdown fences, no explanation."
        for attempt in range(3):
            raw = self.complete(system_json, user, max_tokens)
            # strip accidental ```json ... ``` fences
            cleaned = re.sub(r"^```[a-z]*\n?", "", raw.strip())
            cleaned = re.sub(r"\n?```$", "", cleaned.strip())
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                if attempt == 2:
                    raise ValueError(
                        f"LLM returned non-JSON after 3 attempts.\nRaw:\n{raw}"
                    )
        return {}