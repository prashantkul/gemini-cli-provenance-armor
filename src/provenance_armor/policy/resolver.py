"""Resolve effective policy for a tool by merging hierarchical rules."""

from __future__ import annotations

import logging
from typing import Optional

from provenance_armor.models.policy import (
    EffectivePolicy,
    PolicyLevel,
    PolicyRule,
)

logger = logging.getLogger(__name__)

# Priority ordering: lower index = higher priority
LEVEL_PRIORITY = {
    PolicyLevel.ADMIN: 0,
    PolicyLevel.USER: 1,
    PolicyLevel.WORKSPACE: 2,
}


class PolicyResolver:
    """Resolves the effective policy for a given tool name.

    Merge rules (from docs/03_policy_engine_logic.md):
    - Admin DENY always wins and cannot be overridden.
    - Higher-priority levels override lower ones.
    - If no rule matches, fail-safe: DENY.
    - causal_armor config from the highest-priority source wins.
    """

    def __init__(self, rules: list[PolicyRule]) -> None:
        self._rules = sorted(
            rules,
            key=lambda r: LEVEL_PRIORITY.get(r.source_level, 99),
        )

    def resolve(self, tool_name: str) -> EffectivePolicy:
        """Resolve the effective policy for a tool.

        Returns a deny-all policy if no rules match (fail-safe).
        """
        matching = [r for r in self._rules if self._matches(r.tool, tool_name)]

        if not matching:
            logger.debug("No policy rule for tool '%s' — fail-safe DENY", tool_name)
            return EffectivePolicy(
                tool=tool_name,
                allowed=False,
                causal_armor=None,
                resolved_from=["<fail-safe deny>"],
            )

        # Check for admin deny (absolute override)
        for rule in matching:
            if rule.source_level == PolicyLevel.ADMIN and not rule.allow:
                return EffectivePolicy(
                    tool=tool_name,
                    allowed=False,
                    causal_armor=rule.causal_armor,
                    resolved_from=[f"admin:{rule.tool}"],
                )

        # Take the highest-priority rule
        best = matching[0]
        resolved_from = [f"{best.source_level.value}:{best.tool}"]

        # If the best rule allows, also collect causal_armor from highest source
        causal_armor = best.causal_armor
        for rule in matching:
            if rule.causal_armor is not None:
                causal_armor = rule.causal_armor
                break

        return EffectivePolicy(
            tool=tool_name,
            allowed=best.allow,
            causal_armor=causal_armor,
            resolved_from=resolved_from,
        )

    def _matches(self, pattern: str, tool_name: str) -> bool:
        """Check if a policy tool pattern matches a tool name.

        Supports exact match and wildcard (*).
        """
        if pattern == "*":
            return True
        return pattern == tool_name
