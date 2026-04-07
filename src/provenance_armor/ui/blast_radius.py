"""Blast Radius Indicator: shell command impact analysis display."""

from __future__ import annotations

from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from provenance_armor._utils.shell_parser import ShellImpact, parse_shell_command


def render_blast_radius(
    raw_command: Optional[str] = None,
    impact_dict: Optional[dict[str, Any]] = None,
    console: Optional[Console] = None,
) -> Panel:
    """Render a blast radius indicator as a Rich Panel.

    Either provide ``raw_command`` (will be parsed) or ``impact_dict``
    (pre-parsed from the pipeline).
    """
    if raw_command:
        impact = parse_shell_command(raw_command)
    elif impact_dict:
        impact = _dict_to_impact(impact_dict)
    else:
        return Panel("[dim]No command to analyze[/dim]", title="Blast Radius")

    table = Table(show_header=True, header_style="bold", expand=True)
    table.add_column("Category", style="bold", width=20)
    table.add_column("Details")
    table.add_column("Risk", width=10, justify="center")

    # Commands
    table.add_row(
        "Commands",
        ", ".join(impact.commands) if impact.commands else "none",
        "",
    )

    # File impact
    if impact.target_paths:
        risk = "[red]HIGH[/red]" if impact.is_destructive else "[yellow]MEDIUM[/yellow]"
        table.add_row(
            "Files",
            "\n".join(impact.target_paths[:10])
            + (f"\n... +{len(impact.target_paths) - 10} more" if len(impact.target_paths) > 10 else ""),
            risk,
        )

    # Network
    if impact.is_network or impact.network_destinations:
        destinations = impact.network_destinations or ["(implicit network access)"]
        table.add_row(
            "Network",
            "\n".join(destinations[:5]),
            "[red]HIGH[/red]",
        )

    # Secrets
    if impact.accesses_secrets or impact.sensitive_paths:
        paths = impact.sensitive_paths or ["(sensitive path access)"]
        table.add_row(
            "Secrets",
            "\n".join(paths[:5]),
            "[red]CRITICAL[/red]",
        )

    # Summary warning
    warnings: list[str] = []
    if impact.is_destructive:
        warnings.append("DESTRUCTIVE operation")
    if impact.is_network:
        warnings.append("NETWORK access")
    if impact.accesses_secrets:
        warnings.append("SECRETS access")
    if impact.piped:
        warnings.append("Piped command chain")

    border = "red bold" if warnings else "green"
    title = "Blast Radius"
    if warnings:
        title += f" [{', '.join(warnings)}]"

    return Panel(table, title=title, border_style=border)


def _dict_to_impact(d: dict[str, Any]) -> ShellImpact:
    """Convert a pipeline-produced dict back to ShellImpact."""
    return ShellImpact(
        raw_command=d.get("raw_command", ""),
        commands=d.get("commands", []),
        is_destructive=d.get("is_destructive", False),
        is_network=d.get("is_network", False),
        accesses_secrets=d.get("accesses_secrets", False),
        target_paths=d.get("target_paths", []),
        network_destinations=d.get("network_destinations", []),
        sensitive_paths=d.get("sensitive_paths", []),
        piped=d.get("piped", False),
    )
