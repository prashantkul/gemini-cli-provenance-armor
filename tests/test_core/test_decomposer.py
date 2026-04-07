"""Tests for the context decomposer."""

from provenance_armor.core.decomposer import ContextDecomposer
from provenance_armor.models.context import SpanKind


class TestContextDecomposer:
    def test_decompose_basic_messages(self):
        decomposer = ContextDecomposer()
        messages = [
            {"role": "user", "content": "Please list files"},
            {"role": "model", "content": "I'll list them for you"},
            {"role": "tool", "content": "file1.txt\nfile2.txt"},
        ]
        window = decomposer.decompose(messages)

        user_spans = window.get_spans(SpanKind.USER_REQUEST)
        assert len(user_spans) == 1
        assert user_spans[0].content == "Please list files"

        tool_spans = window.get_spans(SpanKind.UNTRUSTED_TOOL)
        assert len(tool_spans) == 1

        history_spans = window.get_spans(SpanKind.HISTORY)
        assert len(history_spans) == 1

    def test_decompose_mcp_tagged(self):
        decomposer = ContextDecomposer()
        messages = [
            {"role": "user", "content": "Check Jira"},
            {
                "role": "tool",
                "content": '<mcp_source name="jira_server">Bug #123: Fix login</mcp_source>',
            },
        ]
        window = decomposer.decompose(messages)

        tool_spans = window.get_spans(SpanKind.UNTRUSTED_TOOL)
        assert len(tool_spans) == 1
        assert tool_spans[0].provenance.source_type == "mcp"
        assert "jira_server" in tool_spans[0].provenance.source_uri

    def test_decompose_file_tagged(self):
        decomposer = ContextDecomposer()
        messages = [
            {"role": "user", "content": "Read the readme"},
            {
                "role": "tool",
                "content": '<file_content path="/workspace/README.md" lines="1-10">Hello World</file_content>',
            },
        ]
        window = decomposer.decompose(messages)

        tool_spans = window.get_spans(SpanKind.UNTRUSTED_TOOL)
        assert len(tool_spans) == 1
        assert tool_spans[0].provenance.source_uri == "/workspace/README.md"
        assert tool_spans[0].provenance.line_start == 1
        assert tool_spans[0].provenance.line_end == 10

    def test_from_explicit(self):
        decomposer = ContextDecomposer()
        window = decomposer.from_explicit(
            user_request="Do something",
            untrusted_data=[("/file.txt", "content")],
            history=["previous message"],
        )

        assert len(window.get_spans(SpanKind.USER_REQUEST)) == 1
        assert len(window.get_spans(SpanKind.UNTRUSTED_TOOL)) == 1
        assert len(window.get_spans(SpanKind.HISTORY)) == 1
