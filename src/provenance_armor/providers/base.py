"""Base protocol for log-probability providers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from provenance_armor.models.context import ContextWindow
from provenance_armor.models.tool_call import ToolCallRequest


@runtime_checkable
class LogProbProvider(Protocol):
    """Pluggable backend that returns a log-probability score for
    a proposed action given a context window.

    Implementations:
      - MockProvider:      returns configurable scores (testing)
      - HeuristicProvider: keyword overlap scoring (no LLM needed)
      - LLMProvider:       real log-prob via API (Gemini/OpenAI)
    """

    def score(self, context: ContextWindow, action: ToolCallRequest) -> float:
        """Return log P(action | context).

        The context may have certain spans masked (removed) to enable
        Leave-One-Out computation. The provider scores the action
        against whatever spans are currently present.
        """
        ...
