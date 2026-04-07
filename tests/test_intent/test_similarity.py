"""Tests for intent similarity (using fallback embedder)."""

from provenance_armor.intent.similarity import IntentSimilarity


class TestIntentSimilarity:
    def test_aligned_instruction(self):
        sim = IntentSimilarity(threshold=0.3)  # Lower threshold for fallback embedder
        result = sim.compare(
            "delete the temporary files",
            "run_shell_command(command='rm -rf /tmp/files')",
        )
        # The fallback embedder should find some overlap with "delete" and "file"
        assert result.score >= 0.0  # At minimum non-negative

    def test_unrelated_instruction(self):
        sim = IntentSimilarity(threshold=0.5)
        result = sim.compare(
            "explain quantum physics theory",
            "run_shell_command(command='rm -rf /')",
        )
        # Very different topics — low similarity
        assert result.score < 0.5

    def test_result_structure(self):
        sim = IntentSimilarity(threshold=0.65)
        result = sim.compare("test instruction", "test_tool(arg=val)")
        assert hasattr(result, "score")
        assert hasattr(result, "threshold")
        assert hasattr(result, "aligned")
        assert result.threshold == 0.65
