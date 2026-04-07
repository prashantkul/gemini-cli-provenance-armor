"""Provenance tagging for MCP data sources."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MCPProvenance:
    """Metadata tag for data received from an MCP server."""

    server_name: str
    endpoint: str
    timestamp: Optional[float] = None


def tag_mcp_data(data: str, server_name: str, endpoint: str = "") -> str:
    """Wrap MCP data in provenance XML tags for span isolation.

    The Causal Armor decomposer recognizes these tags and creates
    separate untrusted spans for each MCP source.
    """
    return (
        f'<mcp_source name="{server_name}" endpoint="{endpoint}">'
        f"{data}"
        f"</mcp_source>"
    )


def extract_mcp_tags(text: str) -> list[tuple[str, str, str]]:
    """Extract all MCP provenance tags from text.

    Returns list of (server_name, endpoint, content) tuples.
    """
    pattern = re.compile(
        r'<mcp_source\s+name="([^"]+)"(?:\s+endpoint="([^"]*)")?\s*>(.*?)</mcp_source>',
        re.DOTALL,
    )
    results: list[tuple[str, str, str]] = []
    for match in pattern.finditer(text):
        results.append((match.group(1), match.group(2) or "", match.group(3)))
    return results
