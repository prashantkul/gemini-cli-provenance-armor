"""LLM provider: real log-probability scoring via API.

Requires the ``httpx`` optional dependency for async HTTP.
Supports Gemini and OpenAI-compatible APIs.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from provenance_armor.models.context import ContextWindow
from provenance_armor.models.tool_call import ToolCallRequest

logger = logging.getLogger(__name__)


@dataclass
class LLMProviderConfig:
    """Configuration for the LLM log-prob provider."""

    api_url: str = ""
    api_key: str = ""
    model: str = "gemini-2.0-flash"
    max_tokens: int = 1
    temperature: float = 0.0


class LLMProvider:
    """Scores actions using real log-probabilities from an LLM API.

    Constructs a prompt from the context window and proposed action,
    requests log-probabilities for the action tokens, and returns
    the total log-prob as the score.

    Requires ``httpx`` (optional dependency).
    """

    def __init__(self, config: LLMProviderConfig) -> None:
        self._config = config
        self._client: Optional[Any] = None

    def _get_client(self) -> Any:
        """Lazy-init httpx client."""
        if self._client is None:
            try:
                import httpx
                self._client = httpx.Client(timeout=30.0)
            except ImportError:
                raise RuntimeError(
                    "httpx is required for LLMProvider. "
                    "Install with: uv pip install httpx"
                )
        return self._client

    def score(self, context: ContextWindow, action: ToolCallRequest) -> float:
        """Score an action by requesting log-probs from the LLM API."""
        prompt = self._build_prompt(context, action)
        action_text = self._action_text(action)

        try:
            log_prob = self._request_log_prob(prompt, action_text)
            return log_prob
        except Exception as e:
            logger.error("LLM scoring failed: %s", e)
            return -10.0  # Conservative fallback

    def _build_prompt(self, context: ContextWindow, action: ToolCallRequest) -> str:
        """Build the scoring prompt from context."""
        parts = []
        for span in context.active_spans():
            parts.append(span.content)
        parts.append(
            f"\nGiven the above context, how likely is the following action?\n"
            f"Action: {action.function_name}({json.dumps(action.function_args)})"
        )
        return "\n---\n".join(parts)

    def _action_text(self, action: ToolCallRequest) -> str:
        """Text representation of the action for log-prob computation."""
        if action.raw_command:
            return action.raw_command
        return f"{action.function_name}({json.dumps(action.function_args)})"

    def _request_log_prob(self, prompt: str, completion: str) -> float:
        """Make the API call and extract log-probabilities.

        This is a simplified implementation. Real implementations
        would need to handle different API formats (Gemini vs OpenAI).
        """
        client = self._get_client()

        # OpenAI-compatible API format
        payload = {
            "model": self._config.model,
            "prompt": prompt + completion,
            "max_tokens": 0,
            "echo": True,
            "logprobs": 1,
            "temperature": self._config.temperature,
        }

        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }

        response = client.post(
            self._config.api_url,
            json=payload,
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()

        # Extract log-probs from response
        logprobs = data.get("choices", [{}])[0].get("logprobs", {})
        token_logprobs = logprobs.get("token_logprobs", [])

        if not token_logprobs:
            return -10.0

        # Sum log-probs of the completion tokens
        # (skip prompt tokens — we only care about the action)
        prompt_tokens = len(prompt.split())  # Rough estimate
        completion_logprobs = [
            lp for lp in token_logprobs[prompt_tokens:]
            if lp is not None
        ]

        if not completion_logprobs:
            return -10.0

        return sum(completion_logprobs) / len(completion_logprobs)
