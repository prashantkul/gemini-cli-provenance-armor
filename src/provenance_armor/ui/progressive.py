"""Progressive Disclosure: risk level badges and step-by-step approval."""

from __future__ import annotations

from typing import Optional

from rich.text import Text

from provenance_armor.models.tool_call import RiskLevel


# Color mapping for risk levels
RISK_STYLES: dict[RiskLevel, tuple[str, str]] = {
    RiskLevel.CRITICAL: ("white on red", "CRITICAL"),
    RiskLevel.HIGH: ("white on dark_orange", "HIGH"),
    RiskLevel.MEDIUM: ("black on yellow", "MEDIUM"),
    RiskLevel.LOW: ("white on green", "LOW"),
}


def render_risk_badge(risk_level: RiskLevel) -> Text:
    """Render a colored risk level badge."""
    style, label = RISK_STYLES.get(risk_level, ("white", "UNKNOWN"))
    badge = Text()
    badge.append(f" {label} ", style=style)
    return badge


def render_tool_header(
    function_name: str,
    risk_level: RiskLevel,
    raw_command: Optional[str] = None,
) -> Text:
    """Render a tool call header with risk badge."""
    header = Text()
    header.append_text(render_risk_badge(risk_level))
    header.append(f" {function_name}", style="bold")
    if raw_command:
        header.append(f"\n  $ {raw_command}", style="dim italic")
    return header


def should_checkpoint(risk_level: RiskLevel) -> bool:
    """Determine if this risk level requires a checkpoint interrupt."""
    return risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH)
