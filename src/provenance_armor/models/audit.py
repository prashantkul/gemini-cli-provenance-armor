"""Audit logging data models (OpenTelemetry-compatible)."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EventKind(Enum):
    """Type of audit event, matching OTel log record naming."""

    USER_PROMPT = "gemini_cli.user_prompt"
    TOOL_CALL = "gemini_cli.tool_call"
    FILE_OPERATION = "gemini_cli.file_operation"
    CAUSAL_ANALYSIS = "gemini_cli.causal_analysis"
    REDACTION = "gemini_cli.redaction"
    POLICY_DECISION = "gemini_cli.policy_decision"


@dataclass
class AuditEvent:
    """A single audit log record, OTel-compatible."""

    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    kind: EventKind = EventKind.TOOL_CALL
    timestamp: float = field(default_factory=time.time)
    prompt_id: Optional[str] = None       # Links back to originating user prompt
    attributes: dict[str, Any] = field(default_factory=dict)

    def set_tool_call(
        self,
        function_name: str,
        function_args: dict[str, Any],
        decision: str,
        success: bool = True,
    ) -> None:
        """Populate attributes for a tool_call event."""
        self.kind = EventKind.TOOL_CALL
        self.attributes.update({
            "function_name": function_name,
            "function_args": function_args,
            "decision": decision,
            "success": success,
        })

    def set_user_prompt(
        self,
        prompt_text: Optional[str] = None,
        prompt_length: int = 0,
    ) -> None:
        """Populate attributes for a user_prompt event."""
        self.kind = EventKind.USER_PROMPT
        self.prompt_id = self.event_id
        self.attributes.update({
            "prompt_length": prompt_length,
        })
        if prompt_text is not None:
            self.attributes["prompt"] = prompt_text

    def set_causal_analysis(
        self,
        verdict: str,
        scores: dict[str, float],
        dominant_spans: list[str],
    ) -> None:
        """Populate attributes for a causal_analysis event."""
        self.kind = EventKind.CAUSAL_ANALYSIS
        self.attributes.update({
            "verdict": verdict,
            "scores": scores,
            "dominant_spans": dominant_spans,
        })

    def to_dict(self) -> dict[str, Any]:
        """Serialize to OTel-compatible dict."""
        return {
            "event_id": self.event_id,
            "kind": self.kind.value,
            "timestamp": self.timestamp,
            "prompt_id": self.prompt_id,
            "attributes": self.attributes,
        }
