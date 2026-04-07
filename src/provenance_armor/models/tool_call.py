"""Tool call request and result models."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from provenance_armor.models.scoring import DominanceResult


class RiskLevel(Enum):
    """Risk classification for tool calls."""

    CRITICAL = "critical"   # rm, curl, chmod, env, ssh
    HIGH = "high"           # git push, npm publish
    MEDIUM = "medium"       # write_file, replace
    LOW = "low"             # read_file, list_directory


# Maps command base names to risk levels
RISK_PATTERNS: dict[str, RiskLevel] = {
    "rm": RiskLevel.CRITICAL,
    "curl": RiskLevel.CRITICAL,
    "wget": RiskLevel.CRITICAL,
    "chmod": RiskLevel.CRITICAL,
    "chown": RiskLevel.CRITICAL,
    "ssh": RiskLevel.CRITICAL,
    "env": RiskLevel.CRITICAL,
    "export": RiskLevel.CRITICAL,
    "nc": RiskLevel.CRITICAL,
    "dd": RiskLevel.CRITICAL,
    "mkfs": RiskLevel.CRITICAL,
    "git push": RiskLevel.HIGH,
    "npm publish": RiskLevel.HIGH,
    "docker": RiskLevel.HIGH,
    "pip install": RiskLevel.HIGH,
    "write_file": RiskLevel.MEDIUM,
    "replace": RiskLevel.MEDIUM,
    "mv": RiskLevel.MEDIUM,
    "cp": RiskLevel.MEDIUM,
    "read_file": RiskLevel.LOW,
    "list_directory": RiskLevel.LOW,
    "ls": RiskLevel.LOW,
    "cat": RiskLevel.LOW,
    "grep": RiskLevel.LOW,
}


@dataclass
class ToolCallRequest:
    """A proposed tool invocation intercepted before execution."""

    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    function_name: str = ""
    function_args: dict[str, Any] = field(default_factory=dict)
    raw_command: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.LOW
    timestamp: float = field(default_factory=time.time)

    def classify_risk(self) -> RiskLevel:
        """Classify risk level based on function name and args."""
        # Check raw command first (for shell commands)
        if self.raw_command:
            cmd = self.raw_command.strip().split()[0].split("/")[-1] if self.raw_command.strip() else ""
            if cmd in RISK_PATTERNS:
                self.risk_level = RISK_PATTERNS[cmd]
                return self.risk_level

        # Check function name
        if self.function_name in RISK_PATTERNS:
            self.risk_level = RISK_PATTERNS[self.function_name]
            return self.risk_level

        # Default: MEDIUM for unknown tools
        self.risk_level = RiskLevel.MEDIUM
        return self.risk_level


@dataclass
class ToolCallResult:
    """Outcome after the pipeline processes a ToolCallRequest."""

    request: ToolCallRequest
    decision: str  # "allow", "block", "sanitize_and_retry", "ask_user"
    dominance_result: Optional[DominanceResult] = None
    redacted_output: Optional[str] = None
    blast_radius: Optional[dict[str, Any]] = None
    audit_event_id: Optional[str] = None
