"""Environment variable whitelist and masking."""

from __future__ import annotations

import os
import re

# Only these environment variables are safe to propagate
ENV_WHITELIST = frozenset({
    "PATH",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PWD",
    "HOME",
    "USER",
    "SHELL",
    "TERM",
    "TMPDIR",
    "TZ",
    "EDITOR",
})

# Patterns that reference env vars in shell commands
ENV_REF_PATTERN = re.compile(r"\$\{?([A-Z_][A-Z0-9_]*)\}?")


class EnvMasker:
    """Masks sensitive environment variables in text and commands.

    Only whitelisted variables are allowed through. All others are
    replaced with ``[MASKED_ENV:VAR_NAME]``.
    """

    def __init__(self, extra_whitelist: set[str] | None = None) -> None:
        self._whitelist = ENV_WHITELIST | (extra_whitelist or set())

    def get_safe_env(self) -> dict[str, str]:
        """Return a filtered copy of the current environment."""
        return {k: v for k, v in os.environ.items() if k in self._whitelist}

    def mask_command(self, command: str) -> str:
        """Replace references to non-whitelisted env vars in a command string."""
        def _replace(match: re.Match) -> str:
            var_name = match.group(1)
            if var_name in self._whitelist:
                return match.group(0)
            return f"[MASKED_ENV:{var_name}]"

        return ENV_REF_PATTERN.sub(_replace, command)

    def mask_text(self, text: str) -> str:
        """Mask any leaked env variable values found in text."""
        result = text
        for key, value in os.environ.items():
            if key in self._whitelist:
                continue
            if value and len(value) >= 8 and value in result:
                result = result.replace(value, f"[MASKED_ENV:{key}]")
        return result
