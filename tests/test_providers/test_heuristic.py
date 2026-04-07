"""Tests for the heuristic provider."""

from provenance_armor.models.context import ContextWindow, SpanKind
from provenance_armor.models.tool_call import ToolCallRequest
from provenance_armor.providers.heuristic import HeuristicProvider


class TestHeuristicProvider:
    def test_high_overlap_scores_higher(self):
        provider = HeuristicProvider()

        ctx = ContextWindow()
        ctx.add_span(SpanKind.USER_REQUEST, "please delete the temporary files")
        action = ToolCallRequest(
            function_name="run_shell_command",
            raw_command="rm -rf /tmp/files",
        )

        score = provider.score(ctx, action)
        assert score > -10.0  # Some overlap should produce a non-minimum score

    def test_no_overlap_scores_minimum(self):
        provider = HeuristicProvider()

        ctx = ContextWindow()
        ctx.add_span(SpanKind.USER_REQUEST, "quantum entanglement physics")
        action = ToolCallRequest(
            function_name="run_shell_command",
            raw_command="rm -rf /tmp",
        )

        score = provider.score(ctx, action)
        # Very little keyword overlap
        assert score <= -3.0

    def test_empty_context(self):
        provider = HeuristicProvider()
        ctx = ContextWindow()
        action = ToolCallRequest(function_name="test")
        assert provider.score(ctx, action) == -10.0
