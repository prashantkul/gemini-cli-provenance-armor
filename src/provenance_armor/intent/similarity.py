"""Cosine similarity comparison for intent alignment checking."""

from __future__ import annotations

import math
from dataclasses import dataclass

from provenance_armor.intent.embedder import IntentEmbedder


DEFAULT_THRESHOLD = 0.65


@dataclass(frozen=True)
class SimilarityResult:
    """Result of comparing user instruction to a tool call."""

    score: float             # Cosine similarity [0, 1]
    threshold: float         # The threshold used
    aligned: bool            # score >= threshold
    instruction: str
    tool_description: str


class IntentSimilarity:
    """Compares user instruction embeddings against tool call embeddings.

    If cosine similarity < threshold, the tool call may not align
    with what the user actually asked for.
    """

    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        embedder: IntentEmbedder | None = None,
    ) -> None:
        self._threshold = threshold
        self._embedder = embedder or IntentEmbedder()

    def compare(
        self,
        user_instruction: str,
        tool_description: str,
    ) -> SimilarityResult:
        """Compare a user instruction against a tool call description.

        Args:
            user_instruction: The user's original request text.
            tool_description: Formatted as "tool_name(arg1=val1, arg2=val2)".
        """
        vecs = self._embedder.embed_batch([user_instruction, tool_description])
        score = _cosine_similarity(vecs[0], vecs[1])

        return SimilarityResult(
            score=score,
            threshold=self._threshold,
            aligned=score >= self._threshold,
            instruction=user_instruction,
            tool_description=tool_description,
        )


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
