"""OpenTelemetry-compatible audit event schema definitions."""

from __future__ import annotations

from typing import Any

from provenance_armor.models.audit import AuditEvent, EventKind

# Required attributes per event kind
REQUIRED_ATTRIBUTES: dict[EventKind, set[str]] = {
    EventKind.USER_PROMPT: {"prompt_length"},
    EventKind.TOOL_CALL: {"function_name", "function_args", "decision"},
    EventKind.FILE_OPERATION: {"operation", "path"},
    EventKind.CAUSAL_ANALYSIS: {"verdict", "scores"},
    EventKind.REDACTION: {"redaction_count", "categories"},
    EventKind.POLICY_DECISION: {"tool", "allowed", "resolved_from"},
}


def validate_event(event: AuditEvent) -> list[str]:
    """Validate that an audit event has all required attributes."""
    errors: list[str] = []
    required = REQUIRED_ATTRIBUTES.get(event.kind, set())

    for attr in required:
        if attr not in event.attributes:
            errors.append(f"Missing required attribute '{attr}' for {event.kind.value}")

    if event.timestamp <= 0:
        errors.append("Timestamp must be positive")

    return errors


def event_to_otel(event: AuditEvent) -> dict[str, Any]:
    """Convert an AuditEvent to an OpenTelemetry LogRecord-compatible dict."""
    return {
        "Timestamp": int(event.timestamp * 1_000_000_000),  # nanoseconds
        "SeverityText": _severity_for_kind(event.kind),
        "Body": event.kind.value,
        "Attributes": {
            "event_id": event.event_id,
            "prompt_id": event.prompt_id,
            **event.attributes,
        },
        "Resource": {
            "service.name": "provenance-armor",
        },
    }


def _severity_for_kind(kind: EventKind) -> str:
    """Map event kinds to OTel severity levels."""
    if kind in (EventKind.CAUSAL_ANALYSIS, EventKind.REDACTION):
        return "WARN"
    if kind == EventKind.POLICY_DECISION:
        return "INFO"
    return "INFO"
