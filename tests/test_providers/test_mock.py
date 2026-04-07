"""Tests for the mock provider."""

from provenance_armor.models.context import ContextWindow, SpanKind
from provenance_armor.models.tool_call import ToolCallRequest
from provenance_armor.providers.mock import MockProvider


class TestMockProvider:
    def test_safe_scenario(self):
        provider = MockProvider()
        provider.set_safe_scenario()

        ctx = ContextWindow()
        ctx.add_span(SpanKind.USER_REQUEST, "test")
        ctx.add_span(SpanKind.UNTRUSTED_TOOL, "data")
        action = ToolCallRequest(function_name="test")

        full = provider.score(ctx, action)
        no_user = provider.score(ctx.without(SpanKind.USER_REQUEST), action)
        no_untrusted = provider.score(ctx.without(SpanKind.UNTRUSTED_TOOL), action)

        # In safe scenario: removing user causes big drop
        assert (full - no_user) > (full - no_untrusted)

    def test_attack_scenario(self):
        provider = MockProvider()
        provider.set_attack_scenario()

        ctx = ContextWindow()
        ctx.add_span(SpanKind.USER_REQUEST, "test")
        ctx.add_span(SpanKind.UNTRUSTED_TOOL, "data")
        action = ToolCallRequest(function_name="test")

        full = provider.score(ctx, action)
        no_user = provider.score(ctx.without(SpanKind.USER_REQUEST), action)
        no_untrusted = provider.score(ctx.without(SpanKind.UNTRUSTED_TOOL), action)

        # In attack scenario: removing untrusted causes big drop
        assert (full - no_untrusted) > (full - no_user)

    def test_per_request_override(self):
        provider = MockProvider()
        action = ToolCallRequest(function_name="test")
        provider.set_scores_for_request(action.request_id, -2.0, -3.0, -4.0)

        ctx = ContextWindow()
        ctx.add_span(SpanKind.USER_REQUEST, "test")
        ctx.add_span(SpanKind.UNTRUSTED_TOOL, "data")

        assert provider.score(ctx, action) == -2.0

    def test_both_masked(self):
        provider = MockProvider()
        ctx = ContextWindow()
        ctx.add_span(SpanKind.HISTORY, "only history")
        action = ToolCallRequest(function_name="test")
        assert provider.score(ctx, action) == -10.0
