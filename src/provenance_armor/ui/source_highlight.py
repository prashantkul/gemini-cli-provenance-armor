"""Causal Source Highlighting: show provenance of dominant spans."""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from provenance_armor.models.context import ContextWindow, SpanKind
from provenance_armor.models.scoring import CausalVerdict, DominanceResult


def render_source_highlight(
    result: DominanceResult,
    context: ContextWindow,
    console: Optional[Console] = None,
) -> Panel:
    """Render the provenance sources that are driving a tool call.

    For DOMINATED verdicts, highlights the exact file:line of the
    injecting content in red/orange.
    """
    content = Text()

    if result.verdict == CausalVerdict.DOMINATED:
        content.append("INJECTION DETECTED\n", style="bold red")
        content.append("The following sources are driving this action:\n\n", style="red")
    elif result.verdict == CausalVerdict.SUSPICIOUS:
        content.append("SUSPICIOUS SOURCES\n", style="bold yellow")
        content.append("These sources have unusually high influence:\n\n", style="yellow")
    else:
        content.append("Source Provenance\n", style="bold green")
        content.append("Action is primarily user-driven.\n\n", style="green")

    # Show dominant untrusted spans
    dominant_ids = set(result.dominant_spans)
    for span in context.get_spans(SpanKind.UNTRUSTED_TOOL):
        is_dominant = span.span_id in dominant_ids
        style = "bold red" if is_dominant else "dim"
        marker = ">>>" if is_dominant else "   "

        if span.provenance:
            loc = span.provenance.display()
        else:
            loc = f"span:{span.span_id}"

        content.append(f"  {marker} ", style=style)
        content.append(loc, style=style)

        # Show a snippet of the content
        snippet = span.content[:80].replace("\n", " ")
        if len(span.content) > 80:
            snippet += "..."
        content.append(f"\n      {snippet}\n", style="dim")

    # Show user request source
    user_spans = context.get_spans(SpanKind.USER_REQUEST)
    if user_spans:
        content.append("\n  User Request:\n", style="bold green")
        for span in user_spans:
            snippet = span.content[:100].replace("\n", " ")
            content.append(f"      {snippet}\n", style="green")

    border = {
        CausalVerdict.SAFE: "green",
        CausalVerdict.SUSPICIOUS: "yellow",
        CausalVerdict.DOMINATED: "red bold",
        CausalVerdict.INSUFFICIENT_DATA: "dim",
    }.get(result.verdict, "white")

    return Panel(content, title="Source Provenance", border_style=border)
