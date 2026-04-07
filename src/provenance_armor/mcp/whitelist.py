"""Trusted MCP endpoint registry."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MCPEndpoint:
    """A registered MCP server endpoint."""

    name: str
    url: str
    trusted: bool = False
    description: str = ""


class MCPWhitelist:
    """Registry of trusted MCP server endpoints.

    Only whitelisted servers are allowed to provide data to the
    context window. Unknown servers trigger warnings and their
    data is treated with higher suspicion.
    """

    def __init__(self) -> None:
        self._endpoints: dict[str, MCPEndpoint] = {}

    def register(
        self,
        name: str,
        url: str,
        trusted: bool = True,
        description: str = "",
    ) -> None:
        """Register an MCP endpoint."""
        self._endpoints[name] = MCPEndpoint(
            name=name, url=url, trusted=trusted, description=description,
        )

    def is_trusted(self, name: str) -> bool:
        """Check if an MCP server is in the trusted whitelist."""
        endpoint = self._endpoints.get(name)
        if endpoint is None:
            logger.warning("Unknown MCP server: '%s'", name)
            return False
        return endpoint.trusted

    def get_endpoint(self, name: str) -> MCPEndpoint | None:
        """Look up an endpoint by name."""
        return self._endpoints.get(name)

    def list_trusted(self) -> list[MCPEndpoint]:
        """Return all trusted endpoints."""
        return [e for e in self._endpoints.values() if e.trusted]

    def list_all(self) -> list[MCPEndpoint]:
        """Return all registered endpoints."""
        return list(self._endpoints.values())
