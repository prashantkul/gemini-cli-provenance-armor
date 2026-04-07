"""Heuristic provider: keyword/pattern-based scoring without an LLM.

Uses TF-IDF-style weighting between context spans and the proposed
action to estimate how much each context component contributes.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from provenance_armor.models.context import ContextWindow
from provenance_armor.models.tool_call import ToolCallRequest


class HeuristicProvider:
    """Scores actions based on keyword overlap with active context spans.

    Computes a simple TF-based similarity between the action description
    (function name + args) and the active context text. Returns a
    log-probability-like score in [-10, 0] range.
    """

    def score(self, context: ContextWindow, action: ToolCallRequest) -> float:
        """Return a heuristic log-prob-like score for the action given context."""
        context_text = context.active_text()
        action_text = self._action_to_text(action)

        if not context_text or not action_text:
            return -10.0

        context_tokens = _tokenize(context_text)
        action_tokens = _tokenize(action_text)

        if not context_tokens or not action_tokens:
            return -10.0

        # Compute term overlap
        context_tf = Counter(context_tokens)
        action_tf = Counter(action_tokens)

        overlap = sum(
            min(context_tf[t], action_tf[t])
            for t in action_tf
            if t in context_tf
        )
        total_action = sum(action_tf.values())

        # Overlap ratio: what fraction of action terms appear in context
        ratio = overlap / total_action if total_action > 0 else 0.0

        # Convert to log-prob-like scale [-10, 0]
        # ratio=1.0 → -0.5 (very likely), ratio=0.0 → -10.0 (very unlikely)
        if ratio <= 0:
            return -10.0
        return max(-10.0, math.log(ratio + 0.01))

    def _action_to_text(self, action: ToolCallRequest) -> str:
        """Convert a tool call into a text representation for matching."""
        parts = [action.function_name]
        if action.raw_command:
            parts.append(action.raw_command)
        for key, value in action.function_args.items():
            parts.append(f"{key} {value}")
        return " ".join(parts)


def _tokenize(text: str) -> list[str]:
    """Simple word tokenizer."""
    return re.findall(r"[a-z][a-z0-9_]+", text.lower())
