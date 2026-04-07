"""Tests for the policy resolver."""

from provenance_armor.models.policy import (
    CausalArmorConfig,
    PolicyLevel,
    PolicyRule,
)
from provenance_armor.policy.resolver import PolicyResolver


class TestPolicyResolver:
    def test_fail_safe_deny(self):
        """No rules → deny by default."""
        resolver = PolicyResolver([])
        policy = resolver.resolve("run_shell_command")
        assert policy.allowed is False

    def test_simple_allow(self):
        rules = [PolicyRule(tool="run_shell_command", allow=True)]
        resolver = PolicyResolver(rules)
        policy = resolver.resolve("run_shell_command")
        assert policy.allowed is True

    def test_admin_deny_overrides_workspace_allow(self):
        rules = [
            PolicyRule(
                tool="run_shell_command",
                allow=False,
                source_level=PolicyLevel.ADMIN,
            ),
            PolicyRule(
                tool="run_shell_command",
                allow=True,
                source_level=PolicyLevel.WORKSPACE,
            ),
        ]
        resolver = PolicyResolver(rules)
        policy = resolver.resolve("run_shell_command")
        assert policy.allowed is False

    def test_wildcard_match(self):
        rules = [PolicyRule(tool="*", allow=True)]
        resolver = PolicyResolver(rules)
        policy = resolver.resolve("anything")
        assert policy.allowed is True

    def test_specific_over_wildcard(self):
        rules = [
            PolicyRule(tool="*", allow=True, source_level=PolicyLevel.WORKSPACE),
            PolicyRule(tool="rm", allow=False, source_level=PolicyLevel.ADMIN),
        ]
        resolver = PolicyResolver(rules)
        assert resolver.resolve("rm").allowed is False
        assert resolver.resolve("ls").allowed is True

    def test_causal_armor_inherited(self):
        ca = CausalArmorConfig(margin_tau=0.7)
        rules = [PolicyRule(tool="run_shell_command", allow=True, causal_armor=ca)]
        resolver = PolicyResolver(rules)
        policy = resolver.resolve("run_shell_command")
        assert policy.causal_armor is not None
        assert policy.causal_armor.margin_tau == 0.7
