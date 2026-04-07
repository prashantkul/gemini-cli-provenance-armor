"""Tests for the LOO scorer."""

from provenance_armor.core.scorer import LOOScorer
from provenance_armor.models.context import ContextWindow, SpanKind
from provenance_armor.models.tool_call import ToolCallRequest
from provenance_armor.providers.mock import MockProvider


class TestLOOScorer:
    def test_safe_scores(self, sample_context, sample_request):
        provider = MockProvider()
        provider.set_safe_scenario()
        scorer = LOOScorer(provider)

        scores = scorer.score(sample_context, sample_request)

        assert scores.p_full == -1.0
        assert scores.p_without_user == -5.0
        assert scores.p_without_untrusted == -1.5
        assert scores.user_influence > scores.untrusted_influence

    def test_attack_scores(self, sample_context, sample_request):
        provider = MockProvider()
        provider.set_attack_scenario()
        scorer = LOOScorer(provider)

        scores = scorer.score(sample_context, sample_request)

        assert scores.p_full == -1.0
        assert scores.p_without_user == -1.2
        assert scores.p_without_untrusted == -5.0
        assert scores.untrusted_influence > scores.user_influence

    def test_three_passes_called(self, sample_context, sample_request):
        """Verify the scorer makes exactly 3 calls to the provider."""
        call_count = 0
        original_score = MockProvider.score

        class CountingProvider(MockProvider):
            def score(self, context, action):
                nonlocal call_count
                call_count += 1
                return original_score(self, context, action)

        scorer = LOOScorer(CountingProvider())
        scorer.score(sample_context, sample_request)
        assert call_count == 3
