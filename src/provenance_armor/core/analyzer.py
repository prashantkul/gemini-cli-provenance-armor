"""Causal analyzer: interprets LOO scores into verdicts."""

from __future__ import annotations

from provenance_armor.models.context import ContextWindow, SpanKind
from provenance_armor.models.scoring import (
    CausalVerdict,
    DominanceResult,
    LOOScoreSet,
)


# How close the margin must be to tau to trigger SUSPICIOUS
SUSPICIOUS_BAND = 0.15


class CausalAnalyzer:
    """Interprets LOOScoreSet into a CausalVerdict.

    Compares the dominance margin against ``margin_tau``:
    - If untrusted_influence - user_influence > margin_tau → DOMINATED
    - If within SUSPICIOUS_BAND of threshold → SUSPICIOUS
    - Otherwise → SAFE
    """

    def __init__(self, margin_tau: float = 0.5) -> None:
        self._margin_tau = margin_tau

    @property
    def margin_tau(self) -> float:
        return self._margin_tau

    def analyze(
        self,
        scores: LOOScoreSet,
        context: ContextWindow,
    ) -> DominanceResult:
        """Analyze LOO scores and determine the causal verdict."""
        margin = scores.dominance_margin

        # Identify the dominant untrusted spans
        untrusted_spans = context.get_spans(SpanKind.UNTRUSTED_TOOL)

        if not untrusted_spans:
            return DominanceResult(
                scores=scores,
                verdict=CausalVerdict.INSUFFICIENT_DATA,
                margin_tau=self._margin_tau,
                dominant_spans=[],
                explanation="No untrusted data spans in context.",
            )

        if margin > self._margin_tau:
            dominant_ids = [s.span_id for s in untrusted_spans]
            sources = []
            for s in untrusted_spans:
                if s.provenance:
                    sources.append(s.provenance.display())
            source_str = ", ".join(sources) if sources else "unknown sources"

            return DominanceResult(
                scores=scores,
                verdict=CausalVerdict.DOMINATED,
                margin_tau=self._margin_tau,
                dominant_spans=dominant_ids,
                explanation=(
                    f"ALERT: Untrusted data dominates this action "
                    f"(margin={margin:.2f} > tau={self._margin_tau:.2f}). "
                    f"Dominant sources: {source_str}. "
                    f"User influence={scores.user_influence:.2f}, "
                    f"Untrusted influence={scores.untrusted_influence:.2f}."
                ),
            )

        if margin > (self._margin_tau - SUSPICIOUS_BAND):
            return DominanceResult(
                scores=scores,
                verdict=CausalVerdict.SUSPICIOUS,
                margin_tau=self._margin_tau,
                dominant_spans=[s.span_id for s in untrusted_spans],
                explanation=(
                    f"WARNING: Untrusted data influence is near threshold "
                    f"(margin={margin:.2f}, tau={self._margin_tau:.2f}). "
                    f"User influence={scores.user_influence:.2f}, "
                    f"Untrusted influence={scores.untrusted_influence:.2f}."
                ),
            )

        return DominanceResult(
            scores=scores,
            verdict=CausalVerdict.SAFE,
            margin_tau=self._margin_tau,
            dominant_spans=[],
            explanation=(
                f"Action is user-driven "
                f"(margin={margin:.2f} < tau={self._margin_tau:.2f}). "
                f"User influence={scores.user_influence:.2f}, "
                f"Untrusted influence={scores.untrusted_influence:.2f}."
            ),
        )
