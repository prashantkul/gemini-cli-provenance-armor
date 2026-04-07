"""TOML policy schema validation."""

from __future__ import annotations

from typing import Any


class PolicyValidationError(Exception):
    """Raised when a policy file fails schema validation."""


VALID_ON_VIOLATION = {"block", "ask_user", "sanitize_and_retry"}


def validate_policy_dict(data: dict[str, Any], source: str = "") -> list[str]:
    """Validate a parsed TOML policy dict. Returns list of error messages."""
    errors: list[str] = []
    prefix = f"[{source}] " if source else ""

    policies = data.get("policy", [])
    if not isinstance(policies, list):
        errors.append(f"{prefix}'policy' must be an array of tables ([[policy]])")
        return errors

    for i, rule in enumerate(policies):
        rule_prefix = f"{prefix}policy[{i}]"

        if "tool" not in rule:
            errors.append(f"{rule_prefix}: missing required field 'tool'")

        if "allow" in rule and not isinstance(rule["allow"], bool):
            errors.append(f"{rule_prefix}: 'allow' must be a boolean")

        ca = rule.get("causal_armor")
        if ca is not None:
            if not isinstance(ca, dict):
                errors.append(f"{rule_prefix}.causal_armor: must be a table")
                continue

            if "enabled" in ca and not isinstance(ca["enabled"], bool):
                errors.append(f"{rule_prefix}.causal_armor.enabled: must be a boolean")

            if "margin_tau" in ca:
                tau = ca["margin_tau"]
                if not isinstance(tau, (int, float)):
                    errors.append(f"{rule_prefix}.causal_armor.margin_tau: must be a number")
                elif not (0.0 <= tau <= 2.0):
                    errors.append(f"{rule_prefix}.causal_armor.margin_tau: must be between 0.0 and 2.0")

            if "on_violation" in ca:
                if ca["on_violation"] not in VALID_ON_VIOLATION:
                    errors.append(
                        f"{rule_prefix}.causal_armor.on_violation: "
                        f"must be one of {VALID_ON_VIOLATION}"
                    )

            if "max_retries" in ca:
                mr = ca["max_retries"]
                if not isinstance(mr, int) or mr < 0:
                    errors.append(f"{rule_prefix}.causal_armor.max_retries: must be a non-negative integer")

            for list_field in ("untrusted_inputs", "privileged_patterns"):
                if list_field in ca:
                    if not isinstance(ca[list_field], list):
                        errors.append(f"{rule_prefix}.causal_armor.{list_field}: must be an array")
                    elif not all(isinstance(v, str) for v in ca[list_field]):
                        errors.append(f"{rule_prefix}.causal_armor.{list_field}: all items must be strings")

    return errors
