"""Policy configuration models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PolicyLevel(Enum):
    """Hierarchy of policy sources. Admin > User > Workspace."""

    ADMIN = "admin"
    USER = "user"
    WORKSPACE = "workspace"


class ViolationAction(Enum):
    """What to do when causal dominance is detected."""

    BLOCK = "block"
    ASK_USER = "ask_user"
    SANITIZE_AND_RETRY = "sanitize_and_retry"


@dataclass
class CausalArmorConfig:
    """Causal Armor configuration for a specific tool policy."""

    enabled: bool = True
    margin_tau: float = 0.5
    untrusted_inputs: list[str] = field(
        default_factory=lambda: ["read_file", "web_fetch", "mcp_call"]
    )
    privileged_patterns: list[str] = field(
        default_factory=lambda: ["rm", "curl", "chmod", "env", "ssh"]
    )
    on_violation: ViolationAction = ViolationAction.SANITIZE_AND_RETRY
    max_retries: int = 2


@dataclass
class PolicyRule:
    """A single policy rule for a tool."""

    tool: str
    allow: bool = True
    causal_armor: Optional[CausalArmorConfig] = None
    source_level: PolicyLevel = PolicyLevel.WORKSPACE


@dataclass
class EffectivePolicy:
    """The resolved policy for a tool after merging all hierarchy levels.

    Merge rules:
    - Admin DENY always wins (cannot be overridden).
    - If no explicit rule, fail-safe: deny.
    - causal_armor config from the highest-priority source wins.
    """

    tool: str
    allowed: bool
    causal_armor: Optional[CausalArmorConfig]
    resolved_from: list[str] = field(default_factory=list)  # Policy file paths
