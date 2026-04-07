"""Main provenance renderer: composes all UI elements."""

from __future__ import annotations

from typing import Any, Optional

from rich.console import Console

from provenance_armor.models.context import ContextWindow
from provenance_armor.models.scoring import CausalVerdict, DominanceResult
from provenance_armor.models.tool_call import ToolCallRequest
from provenance_armor.ui.blast_radius import render_blast_radius
from provenance_armor.ui.causal_meter import render_causal_meter
from provenance_armor.ui.progressive import render_tool_header, should_checkpoint
from provenance_armor.ui.source_highlight import render_source_highlight


class ProvenanceRenderer:
    """Composes and renders all provenance UI elements.

    This is the main entry point for the UI layer. It combines:
    - Tool call header with risk badge
    - Causal meter (User vs Untrusted influence)
    - Source provenance highlighting
    - Blast radius indicator
    """

    def __init__(self, console: Optional[Console] = None) -> None:
        self._console = console or Console(force_terminal=True)

    def render(
        self,
        request: ToolCallRequest,
        dominance: Optional[DominanceResult] = None,
        blast_radius: Optional[dict[str, Any]] = None,
        context: Optional[ContextWindow] = None,
    ) -> None:
        """Render the full provenance display for a tool call."""
        self._console.print()

        # Header with risk badge
        header = render_tool_header(
            request.function_name,
            request.risk_level,
            request.raw_command,
        )
        self._console.print(header)
        self._console.print()

        # Causal meter (if analysis was performed)
        if dominance:
            meter = render_causal_meter(dominance)
            self._console.print(meter)

            # Source highlighting (if context available)
            if context:
                source_panel = render_source_highlight(dominance, context)
                self._console.print(source_panel)

        # Blast radius (for shell commands)
        if blast_radius or request.raw_command:
            radius_panel = render_blast_radius(
                raw_command=request.raw_command,
                impact_dict=blast_radius,
            )
            self._console.print(radius_panel)

        # Checkpoint warning
        if should_checkpoint(request.risk_level):
            verdict_label = ""
            if dominance:
                verdict_label = f" [{dominance.verdict.value.upper()}]"
            self._console.print(
                f"[bold yellow]Checkpoint: This {request.risk_level.value.upper()} "
                f"action requires confirmation{verdict_label}.[/bold yellow]"
            )
            self._console.print()

    def render_verdict_summary(self, result: DominanceResult) -> None:
        """Render just the verdict summary (for quick display)."""
        style = {
            CausalVerdict.SAFE: "green",
            CausalVerdict.SUSPICIOUS: "yellow",
            CausalVerdict.DOMINATED: "red bold",
            CausalVerdict.INSUFFICIENT_DATA: "dim",
        }.get(result.verdict, "white")

        self._console.print(f"[{style}]{result.explanation}[/{style}]")
