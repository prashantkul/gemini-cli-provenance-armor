"""Tests for the redaction engine."""

from provenance_armor.redaction.engine import RedactionEngine


class TestRedactionEngine:
    def test_full_pipeline(self):
        engine = RedactionEngine(enable_ner=False, enable_delta=False, enable_env=False)
        text = "My AWS key is AKIAIOSFODNN7EXAMPLE and email is test@example.com"
        result = engine.scan(text)

        assert result.has_redactions
        assert "[REDACTED_AWS_KEY]" in result.redacted_text
        assert "[REDACTED_EMAIL]" in result.redacted_text
        assert "AKIAIOSFODNN7EXAMPLE" not in result.redacted_text

    def test_no_redaction_on_clean_text(self):
        engine = RedactionEngine(enable_ner=False, enable_delta=False, enable_env=False)
        text = "This is perfectly clean content."
        result = engine.scan(text)
        assert not result.has_redactions
        assert result.redacted_text == text

    def test_delta_masking_skips_unchanged(self):
        engine = RedactionEngine(enable_ner=False, enable_env=False)
        text = "Secret: AKIAIOSFODNN7EXAMPLE"

        # First scan
        result1 = engine.scan(text, source_uri="/test/file.txt")
        assert result1.has_redactions

        # Second scan with same content — delta mask should skip
        result2 = engine.scan(text, source_uri="/test/file.txt")
        assert not result2.has_redactions  # Skipped due to delta

    def test_overlapping_hits_resolved(self):
        engine = RedactionEngine(enable_ner=False, enable_delta=False, enable_env=False)
        # This text might match multiple patterns at overlapping positions
        text = "Key: sk-proj-AKIAIOSFODNN7EXAMPLE1234567890"
        result = engine.scan(text)
        # Should not crash with overlapping redactions
        assert isinstance(result.redacted_text, str)
