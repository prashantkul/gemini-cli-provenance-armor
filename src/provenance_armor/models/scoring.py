"""Scoring models for Leave-One-Out causal analysis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CausalVerdict(Enum):
    """Outcome of causal dominance analysis."""

    SAFE = "safe"                        # User request dominates
    SUSPICIOUS = "suspicious"            # Margin is close to threshold
    DOMINATED = "dominated"              # Untrusted data dominates
    INSUFFICIENT_DATA = "insufficient"   # Not enough context to judge


@dataclass(frozen=True)
class LOOScoreSet:
    """The three log-probability values from Leave-One-Out scoring.

    Each value represents log P(action | context_variant):
    - ``p_full``: full context (U + H + S)
    - ``p_without_user``: user request removed (H + S only)
    - ``p_without_untrusted``: untrusted data removed (U + H only)
    """

    p_full: float
    p_without_user: float
    p_without_untrusted: float

    @property
    def user_influence(self) -> float:
        """How much removing the user request drops the score."""
        return self.p_full - self.p_without_user

    @property
    def untrusted_influence(self) -> float:
        """How much removing untrusted data drops the score."""
        return self.p_full - self.p_without_untrusted

    @property
    def dominance_margin(self) -> float:
        """Positive = untrusted dominates (bad). Negative = user dominates (good)."""
        return self.untrusted_influence - self.user_influence


@dataclass(frozen=True)
class DominanceResult:
    """Full result of causal dominance analysis."""

    scores: LOOScoreSet
    verdict: CausalVerdict
    margin_tau: float                  # The threshold that was used
    dominant_spans: list[str]          # span_ids of dominating untrusted spans
    explanation: str                   # Human-readable summary
