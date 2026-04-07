"""Tests for the causal analyzer."""

from provenance_armor.core.analyzer import CausalAnalyzer
from provenance_armor.models.scoring import CausalVerdict, LOOScoreSet


class TestCausalAnalyzer:
    def test_safe_verdict(self, sample_context):
        analyzer = CausalAnalyzer(margin_tau=0.5)
        # User influence = 4.0, untrusted influence = 0.5 → margin = -3.5
        scores = LOOScoreSet(p_full=-1.0, p_without_user=-5.0, p_without_untrusted=-1.5)
        result = analyzer.analyze(scores, sample_context)
        assert result.verdict == CausalVerdict.SAFE

    def test_dominated_verdict(self, sample_context):
        analyzer = CausalAnalyzer(margin_tau=0.5)
        # User influence = 0.2, untrusted influence = 4.0 → margin = 3.8
        scores = LOOScoreSet(p_full=-1.0, p_without_user=-1.2, p_without_untrusted=-5.0)
        result = analyzer.analyze(scores, sample_context)
        assert result.verdict == CausalVerdict.DOMINATED
        assert len(result.dominant_spans) > 0

    def test_suspicious_verdict(self, sample_context):
        analyzer = CausalAnalyzer(margin_tau=0.5)
        # Margin just below threshold: 0.45 (within SUSPICIOUS_BAND of 0.15)
        scores = LOOScoreSet(p_full=-1.0, p_without_user=-1.6, p_without_untrusted=-2.05)
        result = analyzer.analyze(scores, sample_context)
        assert result.verdict == CausalVerdict.SUSPICIOUS

    def test_insufficient_data(self):
        """Empty context should return INSUFFICIENT_DATA."""
        from provenance_armor.models.context import ContextWindow
        analyzer = CausalAnalyzer()
        scores = LOOScoreSet(p_full=-1.0, p_without_user=-1.0, p_without_untrusted=-1.0)
        result = analyzer.analyze(scores, ContextWindow())
        assert result.verdict == CausalVerdict.INSUFFICIENT_DATA

    def test_custom_margin_tau(self, sample_context):
        analyzer = CausalAnalyzer(margin_tau=10.0)  # Very high threshold
        # Even a strong untrusted influence won't trigger with high tau
        scores = LOOScoreSet(p_full=-1.0, p_without_user=-1.2, p_without_untrusted=-5.0)
        result = analyzer.analyze(scores, sample_context)
        assert result.verdict == CausalVerdict.SAFE
