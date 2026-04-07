"""MCP Security Gateway: tag, sanitize, and validate external data."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from provenance_armor.mcp.tagger import tag_mcp_data
from provenance_armor.mcp.whitelist import MCPWhitelist

logger = logging.getLogger(__name__)

# Heuristic patterns for imperative instructions in MCP data
INSTRUCTION_PATTERNS = [
    re.compile(r"(?i)\b(you\s+should|you\s+must|please\s+run|execute|perform)\b"),
    re.compile(r"(?i)\b(ignore\s+previous|disregard|override)\b"),
    re.compile(r"(?i)\b(run\s+the\s+following|do\s+the\s+following)\b"),
    re.compile(r"(?i)\b(as\s+an?\s+AI|as\s+a\s+language\s+model)\b"),
    re.compile(r"(?i)\b(system\s*:\s*|assistant\s*:\s*|human\s*:\s*)"),
]


@dataclass
class GatewayResult:
    """Result of processing data through the MCP gateway."""

    tagged_data: str
    server_name: str
    is_trusted: bool
    instructions_stripped: int = 0
    warnings: list[str] = field(default_factory=list)


class MCPSecurityGateway:
    """Security gateway for MCP (Model Context Protocol) data.

    Processes incoming MCP data through three stages:
    1. Provenance Tagging — wrap data in metadata tags
    2. Instruction Stripping — heuristic scan for imperative patterns
    3. Trust Validation — check against whitelist
    """

    def __init__(self, whitelist: Optional[MCPWhitelist] = None) -> None:
        self._whitelist = whitelist or MCPWhitelist()

    @property
    def whitelist(self) -> MCPWhitelist:
        return self._whitelist

    def process(
        self,
        data: str,
        server_name: str,
        endpoint: str = "",
    ) -> GatewayResult:
        """Process incoming MCP data through the security pipeline."""
        warnings: list[str] = []

        # Stage 1: Trust validation
        is_trusted = self._whitelist.is_trusted(server_name)
        if not is_trusted:
            warnings.append(f"MCP server '{server_name}' is not in the trusted whitelist")

        # Stage 2: Instruction stripping (especially for untrusted sources)
        cleaned_data, strip_count = self._strip_instructions(data)
        if strip_count > 0:
            warnings.append(
                f"Stripped {strip_count} suspected instruction(s) from MCP data"
            )
            logger.warning(
                "Stripped %d instruction patterns from MCP server '%s'",
                strip_count, server_name,
            )

        # Stage 3: Provenance tagging
        tagged = tag_mcp_data(cleaned_data, server_name, endpoint)

        return GatewayResult(
            tagged_data=tagged,
            server_name=server_name,
            is_trusted=is_trusted,
            instructions_stripped=strip_count,
            warnings=warnings,
        )

    def _strip_instructions(self, text: str) -> tuple[str, int]:
        """Strip suspected instruction patterns from MCP data.

        Returns (cleaned_text, count_of_stripped_patterns).
        """
        count = 0
        result = text

        for pattern in INSTRUCTION_PATTERNS:
            matches = pattern.findall(result)
            if matches:
                count += len(matches)
                result = pattern.sub("[MCP_INSTRUCTION_STRIPPED]", result)

        return result, count
