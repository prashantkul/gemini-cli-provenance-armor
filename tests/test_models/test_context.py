"""Tests for context models."""

from provenance_armor.models.context import (
    ContextSpan,
    ContextWindow,
    Provenance,
    SpanKind,
)


class TestContextWindow:
    def test_add_span(self):
        window = ContextWindow()
        span = window.add_span(SpanKind.USER_REQUEST, "hello")
        assert span.kind == SpanKind.USER_REQUEST
        assert span.content == "hello"
        assert len(window.spans) == 1

    def test_without_creates_copy(self):
        window = ContextWindow()
        window.add_span(SpanKind.USER_REQUEST, "user text")
        window.add_span(SpanKind.UNTRUSTED_TOOL, "tool text")

        masked = window.without(SpanKind.USER_REQUEST)

        # Original unmodified
        assert not window.spans[0].is_masked
        # Copy has user spans masked
        assert masked.spans[0].is_masked
        assert not masked.spans[1].is_masked

    def test_get_spans_filters_masked(self):
        window = ContextWindow()
        window.add_span(SpanKind.USER_REQUEST, "user")
        window.add_span(SpanKind.UNTRUSTED_TOOL, "tool")
        window.add_span(SpanKind.HISTORY, "hist")

        assert len(window.get_spans(SpanKind.USER_REQUEST)) == 1
        assert len(window.get_spans(SpanKind.UNTRUSTED_TOOL)) == 1

        masked = window.without(SpanKind.USER_REQUEST)
        assert len(masked.get_spans(SpanKind.USER_REQUEST)) == 0
        assert len(masked.get_spans(SpanKind.UNTRUSTED_TOOL)) == 1

    def test_active_text(self):
        window = ContextWindow()
        window.add_span(SpanKind.USER_REQUEST, "hello")
        window.add_span(SpanKind.UNTRUSTED_TOOL, "world")

        assert window.active_text() == "hello\nworld"

        masked = window.without(SpanKind.USER_REQUEST)
        assert masked.active_text() == "world"

    def test_span_by_id(self):
        window = ContextWindow()
        span = window.add_span(SpanKind.USER_REQUEST, "test")
        found = window.span_by_id(span.span_id)
        assert found is span
        assert window.span_by_id("nonexistent") is None


class TestProvenance:
    def test_display_with_lines(self):
        p = Provenance("file", "/path/readme.md", line_start=42, line_end=50)
        assert p.display() == "[file] /path/readme.md:L42-L50"

    def test_display_single_line(self):
        p = Provenance("file", "/path/readme.md", line_start=42)
        assert p.display() == "[file] /path/readme.md:L42"

    def test_display_no_lines(self):
        p = Provenance("mcp", "mcp://jira")
        assert p.display() == "[mcp] mcp://jira"
