"""Mock provider for testing — returns configurable scores."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from provenance_armor.models.context import ContextWindow, SpanKind
from provenance_armor.models.tool_call import ToolCallRequest


@dataclass
class MockProvider:
    """Returns predetermined scores for LOO testing.

    By default, simulates a safe scenario where user influence is high
    and untrusted influence is low. Override via constructor args or
    ``set_scores()`` for attack simulation.
    """

    # Scores to return for each context variant
    full_score: float = -1.0       # P(A | U, H, S)
    no_user_score: float = -5.0    # P(A | H, S) — big drop = user was important
    no_untrusted_score: float = -1.5  # P(A | U, H) — small drop = untrusted not important

    # Optional: per-request score overrides
    _overrides: dict[str, dict[str, float]] = field(default_factory=dict)

    def set_attack_scenario(self) -> None:
        """Configure scores to simulate an IPI attack.

        In this scenario, removing the user barely changes the score,
        but removing untrusted data causes a large drop — meaning the
        untrusted data is the dominant cause of the action.
        """
        self.full_score = -1.0
        self.no_user_score = -1.2      # Small drop: user barely matters
        self.no_untrusted_score = -5.0  # Big drop: untrusted was critical

    def set_safe_scenario(self) -> None:
        """Configure scores for a normal, user-driven action."""
        self.full_score = -1.0
        self.no_user_score = -5.0      # Big drop: user is essential
        self.no_untrusted_score = -1.5  # Small drop: untrusted not critical

    def set_scores_for_request(
        self,
        request_id: str,
        full: float,
        no_user: float,
        no_untrusted: float,
    ) -> None:
        """Override scores for a specific request ID."""
        self._overrides[request_id] = {
            "full": full,
            "no_user": no_user,
            "no_untrusted": no_untrusted,
        }

    def score(self, context: ContextWindow, action: ToolCallRequest) -> float:
        """Return the appropriate score based on which spans are masked."""
        override = self._overrides.get(action.request_id)

        has_user = len(context.get_spans(SpanKind.USER_REQUEST)) > 0
        has_untrusted = len(context.get_spans(SpanKind.UNTRUSTED_TOOL)) > 0

        if has_user and has_untrusted:
            return override["full"] if override else self.full_score
        elif not has_user and has_untrusted:
            return override["no_user"] if override else self.no_user_score
        elif has_user and not has_untrusted:
            return override["no_untrusted"] if override else self.no_untrusted_score
        else:
            # Both masked — return a very low score
            return -10.0
