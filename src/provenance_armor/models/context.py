"""Context window and span models for causal decomposition."""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class SpanKind(Enum):
    """Classification of a context span's origin."""

    USER_REQUEST = auto()    # U: the human's instruction
    HISTORY = auto()         # H: conversation history
    UNTRUSTED_TOOL = auto()  # S: file contents, web fetches, MCP data


@dataclass(frozen=True)
class Provenance:
    """Where a context span originated from."""

    source_type: str   # "file", "web", "mcp", "user_input"
    source_uri: str    # "/path/to/README.md", "https://...", "mcp://jira"
    line_start: Optional[int] = None
    line_end: Optional[int] = None

    def display(self) -> str:
        """Human-readable provenance string."""
        loc = self.source_uri
        if self.line_start is not None:
            loc += f":L{self.line_start}"
            if self.line_end is not None and self.line_end != self.line_start:
                loc += f"-L{self.line_end}"
        return f"[{self.source_type}] {loc}"


@dataclass
class ContextSpan:
    """A single segment of the context window."""

    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    kind: SpanKind = SpanKind.HISTORY
    content: str = ""
    provenance: Optional[Provenance] = None
    is_masked: bool = False  # True when this span is "left out" for LOO


@dataclass
class ContextWindow:
    """The full context decomposed into typed spans.

    The core data structure for causal analysis. Supports Leave-One-Out
    operations via the ``without()`` method, which returns a copy with
    specified span kinds masked.
    """

    spans: list[ContextSpan] = field(default_factory=list)

    def add_span(
        self,
        kind: SpanKind,
        content: str,
        provenance: Optional[Provenance] = None,
    ) -> ContextSpan:
        """Create and append a new span, returning it."""
        span = ContextSpan(kind=kind, content=content, provenance=provenance)
        self.spans.append(span)
        return span

    def without(self, kind: SpanKind) -> ContextWindow:
        """Return a deep copy with all spans of the given kind masked."""
        new = copy.deepcopy(self)
        for span in new.spans:
            if span.kind == kind:
                span.is_masked = True
        return new

    def get_spans(self, kind: SpanKind) -> list[ContextSpan]:
        """Return unmasked spans of the given kind."""
        return [s for s in self.spans if s.kind == kind and not s.is_masked]

    def active_spans(self) -> list[ContextSpan]:
        """Return all unmasked spans."""
        return [s for s in self.spans if not s.is_masked]

    def active_text(self) -> str:
        """Concatenate all unmasked spans into a single string."""
        return "\n".join(s.content for s in self.active_spans())

    def span_by_id(self, span_id: str) -> Optional[ContextSpan]:
        """Look up a span by ID."""
        for s in self.spans:
            if s.span_id == span_id:
                return s
        return None
