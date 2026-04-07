"""Tests for scoring models."""

from provenance_armor.models.scoring import CausalVerdict, DominanceResult, LOOScoreSet


class TestLOOScoreSet:
    def test_user_dominates(self):
        """When removing user causes big drop, user influence is high."""
        scores = LOOScoreSet(p_full=-1.0, p_without_user=-5.0, p_without_untrusted=-1.5)
        assert scores.user_influence == 4.0   # -1 - (-5) = 4
        assert scores.untrusted_influence == 0.5  # -1 - (-1.5) = 0.5
        assert scores.dominance_margin < 0  # Negative = user dominates (good)

    def test_untrusted_dominates(self):
        """When removing untrusted causes big drop, untrusted influence is high."""
        scores = LOOScoreSet(p_full=-1.0, p_without_user=-1.2, p_without_untrusted=-5.0)
        assert abs(scores.user_influence - 0.2) < 1e-10
        assert scores.untrusted_influence == 4.0
        assert scores.dominance_margin > 0  # Positive = untrusted dominates (bad)

    def test_frozen(self):
        """LOOScoreSet is immutable."""
        scores = LOOScoreSet(p_full=-1.0, p_without_user=-2.0, p_without_untrusted=-1.5)
        try:
            scores.p_full = -2.0  # type: ignore
            assert False, "Should be frozen"
        except AttributeError:
            pass


class TestDominanceResult:
    def test_safe_verdict(self):
        scores = LOOScoreSet(p_full=-1.0, p_without_user=-5.0, p_without_untrusted=-1.5)
        result = DominanceResult(
            scores=scores,
            verdict=CausalVerdict.SAFE,
            margin_tau=0.5,
            dominant_spans=[],
            explanation="test",
        )
        assert result.verdict == CausalVerdict.SAFE
        assert result.dominant_spans == []
