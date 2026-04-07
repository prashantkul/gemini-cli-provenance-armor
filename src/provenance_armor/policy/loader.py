"""Load and merge TOML policy files from the Admin > User > Workspace hierarchy."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from provenance_armor._utils.toml_compat import load_toml
from provenance_armor.models.policy import (
    CausalArmorConfig,
    PolicyLevel,
    PolicyRule,
    ViolationAction,
)
from provenance_armor.policy.schema import PolicyValidationError, validate_policy_dict

logger = logging.getLogger(__name__)

# Default search paths
DEFAULT_ADMIN_PATH = Path("/etc/provenance-armor/policy.toml")
DEFAULT_USER_PATH = Path.home() / ".config" / "provenance-armor" / "policy.toml"
DEFAULT_WORKSPACE_PATH = Path(".provenance-armor") / "policy.toml"


class PolicyLoader:
    """Loads policy rules from TOML files at three hierarchy levels.

    Search order (highest to lowest priority):
    1. Admin: /etc/provenance-armor/policy.toml (or custom)
    2. User: ~/.config/provenance-armor/policy.toml (or custom)
    3. Workspace: .provenance-armor/policy.toml (or custom)
    """

    def __init__(
        self,
        admin_path: Optional[Path] = None,
        user_path: Optional[Path] = None,
        workspace_path: Optional[Path] = None,
    ) -> None:
        self._admin_path = admin_path or DEFAULT_ADMIN_PATH
        self._user_path = user_path or DEFAULT_USER_PATH
        self._workspace_path = workspace_path or DEFAULT_WORKSPACE_PATH

    def load_all(self) -> list[PolicyRule]:
        """Load and return all policy rules from all available levels.

        Rules are returned with their source_level set so the resolver
        can enforce precedence.
        """
        rules: list[PolicyRule] = []

        for level, path in [
            (PolicyLevel.ADMIN, self._admin_path),
            (PolicyLevel.USER, self._user_path),
            (PolicyLevel.WORKSPACE, self._workspace_path),
        ]:
            loaded = self._load_level(level, path)
            rules.extend(loaded)

        return rules

    def _load_level(self, level: PolicyLevel, path: Path) -> list[PolicyRule]:
        """Load policy rules from a single file."""
        if not path.exists():
            logger.debug("Policy file not found: %s", path)
            return []

        try:
            data = load_toml(path)
        except Exception as e:
            logger.warning("Failed to parse policy file %s: %s", path, e)
            return []

        errors = validate_policy_dict(data, source=str(path))
        if errors:
            logger.warning(
                "Policy validation errors in %s: %s",
                path,
                "; ".join(errors),
            )
            raise PolicyValidationError(
                f"Invalid policy at {path}: {'; '.join(errors)}"
            )

        return self._parse_rules(data, level, str(path))

    def _parse_rules(
        self,
        data: dict[str, Any],
        level: PolicyLevel,
        source_path: str,
    ) -> list[PolicyRule]:
        """Parse TOML data into PolicyRule objects."""
        rules: list[PolicyRule] = []

        for entry in data.get("policy", []):
            ca_data = entry.get("causal_armor")
            ca_config = None
            if ca_data is not None:
                ca_config = CausalArmorConfig(
                    enabled=ca_data.get("enabled", True),
                    margin_tau=ca_data.get("margin_tau", 0.5),
                    untrusted_inputs=ca_data.get(
                        "untrusted_inputs",
                        ["read_file", "web_fetch", "mcp_call"],
                    ),
                    privileged_patterns=ca_data.get(
                        "privileged_patterns",
                        ["rm", "curl", "chmod", "env", "ssh"],
                    ),
                    on_violation=ViolationAction(
                        ca_data.get("on_violation", "sanitize_and_retry")
                    ),
                    max_retries=ca_data.get("max_retries", 2),
                )

            rules.append(
                PolicyRule(
                    tool=entry["tool"],
                    allow=entry.get("allow", True),
                    causal_armor=ca_config,
                    source_level=level,
                )
            )

        return rules

    def load_from_string(self, toml_str: str, level: PolicyLevel) -> list[PolicyRule]:
        """Parse policy rules from a TOML string (useful for testing)."""
        from provenance_armor._utils.toml_compat import loads_toml

        data = loads_toml(toml_str)
        errors = validate_policy_dict(data, source="<string>")
        if errors:
            raise PolicyValidationError(
                f"Invalid policy: {'; '.join(errors)}"
            )
        return self._parse_rules(data, level, "<string>")
