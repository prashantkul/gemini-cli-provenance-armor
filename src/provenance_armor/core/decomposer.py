"""Context decomposition: splits raw messages into typed ContextSpans."""

from __future__ import annotations

import re
from typing import Any, Optional

from provenance_armor.models.context import (
    ContextSpan,
    ContextWindow,
    Provenance,
    SpanKind,
)

# XML-style tags used for provenance tagging in MCP data
MCP_TAG_PATTERN = re.compile(
    r'<mcp_source\s+name="([^"]+)">(.*?)</mcp_source>',
    re.DOTALL,
)
FILE_TAG_PATTERN = re.compile(
    r'<file_content\s+path="([^"]+)"(?:\s+lines="(\d+)-(\d+)")?>(.*?)</file_content>',
    re.DOTALL,
)


class ContextDecomposer:
    """Breaks raw conversation messages into a typed ContextWindow.

    Supports multiple decomposition strategies:
    - **positional**: first user message = U, tool results = S, rest = H
    - **tagged**: looks for XML-style tags (<mcp_source>, <file_content>)
    - **explicit**: caller pre-provides ContextSpans directly
    """

    def decompose(self, messages: list[dict[str, Any]]) -> ContextWindow:
        """Decompose a list of conversation messages into a ContextWindow.

        Expected message format::

            {"role": "user"|"model"|"tool", "content": str, ...}

        Optional fields: ``source_uri``, ``line_start``, ``line_end``.
        """
        window = ContextWindow()
        user_seen = False

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user" and not user_seen:
                # First user message is the primary instruction (U)
                window.add_span(
                    kind=SpanKind.USER_REQUEST,
                    content=content,
                    provenance=Provenance(
                        source_type="user_input",
                        source_uri="user_prompt",
                    ),
                )
                user_seen = True

            elif role == "tool":
                # Tool results are untrusted (S)
                self._decompose_tool_result(window, msg)

            else:
                # Everything else is history (H)
                window.add_span(
                    kind=SpanKind.HISTORY,
                    content=content,
                    provenance=Provenance(
                        source_type="history",
                        source_uri=f"message:{role}",
                    ),
                )

        return window

    def _decompose_tool_result(
        self,
        window: ContextWindow,
        msg: dict[str, Any],
    ) -> None:
        """Decompose a tool result message, extracting tagged spans."""
        content = msg.get("content", "")
        source_uri = msg.get("source_uri", "tool_output")

        # Try to extract MCP-tagged spans
        mcp_matches = MCP_TAG_PATTERN.findall(content)
        for name, body in mcp_matches:
            window.add_span(
                kind=SpanKind.UNTRUSTED_TOOL,
                content=body.strip(),
                provenance=Provenance(
                    source_type="mcp",
                    source_uri=f"mcp://{name}",
                ),
            )

        # Try to extract file-tagged spans
        file_matches = FILE_TAG_PATTERN.findall(content)
        for path, line_start, line_end, body in file_matches:
            window.add_span(
                kind=SpanKind.UNTRUSTED_TOOL,
                content=body.strip(),
                provenance=Provenance(
                    source_type="file",
                    source_uri=path,
                    line_start=int(line_start) if line_start else None,
                    line_end=int(line_end) if line_end else None,
                ),
            )

        # If no tagged spans found, treat the whole content as untrusted
        if not mcp_matches and not file_matches:
            window.add_span(
                kind=SpanKind.UNTRUSTED_TOOL,
                content=content,
                provenance=Provenance(
                    source_type="tool",
                    source_uri=source_uri,
                ),
            )

    def from_explicit(
        self,
        user_request: str,
        untrusted_data: list[tuple[str, str]],
        history: Optional[list[str]] = None,
    ) -> ContextWindow:
        """Build a ContextWindow from explicit components.

        Args:
            user_request: The user's instruction text.
            untrusted_data: List of (source_uri, content) tuples.
            history: Optional list of history text segments.
        """
        window = ContextWindow()

        window.add_span(
            kind=SpanKind.USER_REQUEST,
            content=user_request,
            provenance=Provenance(
                source_type="user_input",
                source_uri="user_prompt",
            ),
        )

        for uri, content in untrusted_data:
            source_type = "file" if "/" in uri else "tool"
            window.add_span(
                kind=SpanKind.UNTRUSTED_TOOL,
                content=content,
                provenance=Provenance(
                    source_type=source_type,
                    source_uri=uri,
                ),
            )

        for text in (history or []):
            window.add_span(
                kind=SpanKind.HISTORY,
                content=text,
                provenance=Provenance(
                    source_type="history",
                    source_uri="conversation",
                ),
            )

        return window
