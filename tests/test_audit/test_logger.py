"""Tests for the audit logger."""

import json
import tempfile
from pathlib import Path

from provenance_armor.audit.logger import AuditLogger
from provenance_armor.models.audit import AuditEvent, EventKind


class TestAuditLogger:
    def test_log_tool_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger = AuditLogger(log_dir=Path(tmp), validate=False)
            event = logger.log_tool_call(
                function_name="run_shell_command",
                function_args={"command": "ls"},
                decision="allow",
            )

            assert event.kind == EventKind.TOOL_CALL
            assert logger.log_path.exists()

            line = logger.log_path.read_text().strip()
            record = json.loads(line)
            assert record["Body"] == "gemini_cli.tool_call"
            assert record["Attributes"]["function_name"] == "run_shell_command"

    def test_log_causal_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger = AuditLogger(log_dir=Path(tmp), validate=False)
            event = logger.log_causal_analysis(
                verdict="dominated",
                scores={"p_full": -1.0, "p_without_user": -1.2},
                dominant_spans=["span1"],
            )
            assert event.kind == EventKind.CAUSAL_ANALYSIS

    def test_events_in_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger = AuditLogger(log_dir=Path(tmp), validate=False)
            logger.log_tool_call("test", {}, "allow")
            logger.log_tool_call("test2", {}, "block")
            events = logger.get_events()
            assert len(events) == 2

    def test_otel_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger = AuditLogger(log_dir=Path(tmp), validate=False)
            logger.log_tool_call("test", {}, "allow")

            line = logger.log_path.read_text().strip()
            record = json.loads(line)

            # Check OTel-compatible fields
            assert "Timestamp" in record
            assert "SeverityText" in record
            assert "Body" in record
            assert "Attributes" in record
            assert "Resource" in record
            assert record["Resource"]["service.name"] == "provenance-armor"
