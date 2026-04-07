"""Causal Meter: visual bar showing User vs Untrusted data influence."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from provenance_armor.models.scoring import CausalVerdict, DominanceResult


BAR_WIDTH = 40


def render_causal_meter(
    result: DominanceResult,
    console: Optional[Console] = None,
) -> Panel:
    """Render a causal influence meter as a Rich Panel.

    Shows a horizontal bar with User influence (green) on the left
    and Untrusted influence (red/orange) on the right.
    """
    scores = result.scores

    # Normalize influences to positive values for display
    user_inf = max(0.0, scores.user_influence)
    untrusted_inf = max(0.0, scores.untrusted_influence)
    total = user_inf + untrusted_inf

    if total == 0:
        user_pct = 0.5
    else:
        user_pct = user_inf / total

    user_chars = int(BAR_WIDTH * user_pct)
    untrusted_chars = BAR_WIDTH - user_chars

    # Build the bar
    bar = Text()
    bar.append("U " , style="bold green")
    bar.append("█" * user_chars, style="green")
    bar.append("█" * untrusted_chars, style="red" if result.verdict == CausalVerdict.DOMINATED else "yellow")
    bar.append(" S", style="bold red" if result.verdict == CausalVerdict.DOMINATED else "bold yellow")

    # Percentage labels
    info = Text()
    info.append(f"  User: {user_pct * 100:.0f}%", style="green")
    info.append(f"  |  Untrusted: {(1 - user_pct) * 100:.0f}%",
                style="red" if result.verdict == CausalVerdict.DOMINATED else "yellow")

    content = Text()
    content.append_text(bar)
    content.append("\n")
    content.append_text(info)

    # Panel style based on verdict
    border_style = {
        CausalVerdict.SAFE: "green",
        CausalVerdict.SUSPICIOUS: "yellow",
        CausalVerdict.DOMINATED: "red bold",
        CausalVerdict.INSUFFICIENT_DATA: "dim",
    }.get(result.verdict, "white")

    title = f"Causal Meter [{result.verdict.value.upper()}]"

    return Panel(content, title=title, border_style=border_style)


# Optional type for import
from typing import Optional
