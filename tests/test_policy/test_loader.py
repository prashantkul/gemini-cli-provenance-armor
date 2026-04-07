"""Tests for the policy loader."""

from provenance_armor.models.policy import PolicyLevel, ViolationAction
from provenance_armor.policy.loader import PolicyLoader


SAMPLE_TOML = '''
[[policy]]
tool = "run_shell_command"
allow = true

[policy.causal_armor]
enabled = true
margin_tau = 0.5
untrusted_inputs = ["read_file", "web_fetch"]
privileged_patterns = ["rm", "curl"]
on_violation = "sanitize_and_retry"
max_retries = 3

[[policy]]
tool = "read_file"
allow = true
'''


class TestPolicyLoader:
    def test_load_from_string(self):
        loader = PolicyLoader()
        rules = loader.load_from_string(SAMPLE_TOML, PolicyLevel.WORKSPACE)

        assert len(rules) == 2
        assert rules[0].tool == "run_shell_command"
        assert rules[0].allow is True
        assert rules[0].causal_armor is not None
        assert rules[0].causal_armor.margin_tau == 0.5
        assert rules[0].causal_armor.on_violation == ViolationAction.SANITIZE_AND_RETRY
        assert rules[0].causal_armor.max_retries == 3

        assert rules[1].tool == "read_file"
        assert rules[1].causal_armor is None

    def test_load_invalid_toml(self):
        loader = PolicyLoader()
        import pytest
        from provenance_armor.policy.schema import PolicyValidationError

        with pytest.raises(PolicyValidationError):
            loader.load_from_string('[[policy]]\nallow = "not_a_bool"', PolicyLevel.USER)
