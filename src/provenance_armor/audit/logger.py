"""Audit logger: writes OTel-compatible JSON events to log files."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from provenance_armor.audit.schema import event_to_otel, validate_event
from provenance_armor.models.audit import AuditEvent, EventKind

logger = logging.getLogger(__name__)

DEFAULT_LOG_DIR = Path.home() / ".provenance-armor" / "logs"


class AuditLogger:
    """Writes audit events as newline-delimited JSON to a log file.

    Each line in the log file is a self-contained OTel-compatible JSON record.
    """

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        log_file: str = "audit.jsonl",
        validate: bool = True,
    ) -> None:
        self._log_dir = log_dir or DEFAULT_LOG_DIR
        self._log_file = log_file
        self._validate = validate
        self._events: list[AuditEvent] = []  # In-memory buffer

    @property
    def log_path(self) -> Path:
        return self._log_dir / self._log_file

    def log(self, event: AuditEvent) -> None:
        """Log an audit event."""
        if self._validate:
            errors = validate_event(event)
            if errors:
                logger.warning("Audit event validation: %s", "; ".join(errors))

        self._events.append(event)
        self._write_event(event)

    def log_tool_call(
        self,
        function_name: str,
        function_args: dict,
        decision: str,
        success: bool = True,
        prompt_id: Optional[str] = None,
    ) -> AuditEvent:
        """Convenience: create and log a tool_call event."""
        event = AuditEvent(kind=EventKind.TOOL_CALL, prompt_id=prompt_id)
        event.set_tool_call(function_name, function_args, decision, success)
        self.log(event)
        return event

    def log_causal_analysis(
        self,
        verdict: str,
        scores: dict[str, float],
        dominant_spans: list[str],
        prompt_id: Optional[str] = None,
    ) -> AuditEvent:
        """Convenience: create and log a causal_analysis event."""
        event = AuditEvent(kind=EventKind.CAUSAL_ANALYSIS, prompt_id=prompt_id)
        event.set_causal_analysis(verdict, scores, dominant_spans)
        self.log(event)
        return event

    def get_events(self) -> list[AuditEvent]:
        """Return all in-memory events (for testing/inspection)."""
        return list(self._events)

    def _write_event(self, event: AuditEvent) -> None:
        """Append an event as JSON to the log file."""
        try:
            self._log_dir.mkdir(parents=True, exist_ok=True)
            otel_record = event_to_otel(event)
            with open(self.log_path, "a") as f:
                f.write(json.dumps(otel_record, default=str) + "\n")
        except OSError as e:
            logger.error("Failed to write audit log: %s", e)
