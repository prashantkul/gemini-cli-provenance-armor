"""Tests for tool call models."""

from provenance_armor.models.tool_call import RiskLevel, ToolCallRequest


class TestToolCallRequest:
    def test_classify_risk_critical(self):
        req = ToolCallRequest(function_name="run_shell_command", raw_command="rm -rf /tmp")
        level = req.classify_risk()
        assert level == RiskLevel.CRITICAL

    def test_classify_risk_low(self):
        req = ToolCallRequest(function_name="read_file")
        level = req.classify_risk()
        assert level == RiskLevel.LOW

    def test_classify_risk_network(self):
        req = ToolCallRequest(function_name="run_shell_command", raw_command="curl http://example.com")
        level = req.classify_risk()
        assert level == RiskLevel.CRITICAL

    def test_classify_risk_unknown(self):
        req = ToolCallRequest(function_name="some_custom_tool")
        level = req.classify_risk()
        assert level == RiskLevel.MEDIUM  # Default for unknown
