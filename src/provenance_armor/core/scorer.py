"""Leave-One-Out (LOO) scorer for causal attribution."""

from __future__ import annotations

from provenance_armor.models.context import ContextWindow, SpanKind
from provenance_armor.models.scoring import LOOScoreSet
from provenance_armor.models.tool_call import ToolCallRequest
from provenance_armor.providers.base import LogProbProvider


class LOOScorer:
    """Performs Leave-One-Out scoring using a pluggable LogProbProvider.

    Runs three scoring passes:
    1. Full context (U + H + S) → P(A | U, H, S)
    2. Without user request (H + S) → P(A | H, S)
    3. Without untrusted data (U + H) → P(A | U, H)

    The difference between these scores reveals which context component
    is the dominant "cause" of the proposed action.
    """

    def __init__(self, provider: LogProbProvider) -> None:
        self._provider = provider

    def score(
        self,
        context: ContextWindow,
        action: ToolCallRequest,
    ) -> LOOScoreSet:
        """Run the three LOO scoring passes synchronously."""
        p_full = self._provider.score(context, action)
        p_no_user = self._provider.score(
            context.without(SpanKind.USER_REQUEST), action
        )
        p_no_untrusted = self._provider.score(
            context.without(SpanKind.UNTRUSTED_TOOL), action
        )

        return LOOScoreSet(
            p_full=p_full,
            p_without_user=p_no_user,
            p_without_untrusted=p_no_untrusted,
        )
