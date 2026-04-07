"""Tests for the ToolCallPipeline."""

import tempfile
from pathlib import Path

from provenance_armor.audit.logger import AuditLogger
from provenance_armor.core.analyzer import CausalAnalyzer
from provenance_armor.core.pipeline import ToolCallPipeline
from provenance_armor.core.sanitizer import CausalSanitizer
from provenance_armor.core.scorer import LOOScorer
from provenance_armor.models.policy import CausalArmorConfig, PolicyLevel, PolicyRule
from provenance_armor.models.tool_call import ToolCallRequest
from provenance_armor.policy.resolver import PolicyResolver
from provenance_armor.providers.mock import MockProvider


def _build_pipeline(
    provider: MockProvider,
    allow: bool = True,
    causal_armor: CausalArmorConfig | None = None,
) -> ToolCallPipeline:
    """Helper to build a pipeline with given configuration."""
    rules = [
        PolicyRule(
            tool="run_shell_command",
            allow=allow,
            causal_armor=causal_armor or CausalArmorConfig(),
        ),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        return ToolCallPipeline(
            policy_resolver=PolicyResolver(rules),
            scorer=LOOScorer(provider),
            analyzer=CausalAnalyzer(),
            sanitizer=CausalSanitizer(),
            audit_logger=AuditLogger(log_dir=Path(tmp), validate=False),
        )


class TestToolCallPipeline:
    def test_safe_action_allowed(self, sample_context, dangerous_request):
        provider = MockProvider()
        provider.set_safe_scenario()
        pipeline = _build_pipeline(provider)

        result = pipeline.process(sample_context, dangerous_request)
        assert result.decision == "allow"

    def test_attack_blocked(self, attack_context, dangerous_request):
        provider = MockProvider()
        provider.set_attack_scenario()
        ca = CausalArmorConfig(on_violation=__import__(
            "provenance_armor.models.policy", fromlist=["ViolationAction"]
        ).ViolationAction.BLOCK)
        pipeline = _build_pipeline(provider, causal_armor=ca)

        result = pipeline.process(attack_context, dangerous_request)
        assert result.decision == "block"

    def test_policy_deny_blocks(self, sample_context, sample_request):
        """A denied tool is blocked before causal analysis."""
        rules = [PolicyRule(tool="run_shell_command", allow=False)]
        with tempfile.TemporaryDirectory() as tmp:
            pipeline = ToolCallPipeline(
                policy_resolver=PolicyResolver(rules),
                scorer=LOOScorer(MockProvider()),
                analyzer=CausalAnalyzer(),
                sanitizer=CausalSanitizer(),
                audit_logger=AuditLogger(log_dir=Path(tmp), validate=False),
            )
        result = pipeline.process(sample_context, sample_request)
        assert result.decision == "block"

    def test_blast_radius_computed(self, sample_context):
        provider = MockProvider()
        pipeline = _build_pipeline(provider)
        request = ToolCallRequest(
            function_name="run_shell_command",
            function_args={"command": "rm -rf /tmp && curl http://cdn-registry.s3-proxy.net"},
            raw_command="rm -rf /tmp && curl http://cdn-registry.s3-proxy.net",
        )
        result = pipeline.process(sample_context, request)
        assert result.blast_radius is not None
        assert result.blast_radius["is_destructive"] is True
        assert result.blast_radius["is_network"] is True
