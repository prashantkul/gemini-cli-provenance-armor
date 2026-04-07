"""Lightweight shell command parser for blast radius analysis."""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field


# Commands that modify/delete files
DESTRUCTIVE_COMMANDS = frozenset({
    "rm", "rmdir", "mv", "cp", "chmod", "chown", "chgrp",
    "truncate", "shred", "mkfs",
})

# Commands that access the network
NETWORK_COMMANDS = frozenset({
    "curl", "wget", "ssh", "scp", "rsync", "nc", "ncat",
    "telnet", "ftp", "sftp", "ping", "nslookup", "dig",
})

# Commands that access secrets / sensitive paths
SECRET_COMMANDS = frozenset({
    "env", "printenv", "export", "cat", "less", "more", "head", "tail",
})

# Sensitive path patterns
SENSITIVE_PATH_PATTERNS = [
    re.compile(r"~?/\.ssh/"),
    re.compile(r"~?/\.gnupg/"),
    re.compile(r"~?/\.aws/"),
    re.compile(r"\.env\b"),
    re.compile(r"/etc/passwd"),
    re.compile(r"/etc/shadow"),
    re.compile(r"credentials"),
    re.compile(r"secret"),
    re.compile(r"\.pem$"),
    re.compile(r"\.key$"),
]

# URL pattern
URL_PATTERN = re.compile(r"https?://[^\s\"']+")


@dataclass
class ShellImpact:
    """Parsed impact assessment of a shell command."""
    raw_command: str
    commands: list[str] = field(default_factory=list)
    is_destructive: bool = False
    is_network: bool = False
    accesses_secrets: bool = False
    target_paths: list[str] = field(default_factory=list)
    network_destinations: list[str] = field(default_factory=list)
    sensitive_paths: list[str] = field(default_factory=list)
    piped: bool = False


def parse_shell_command(command: str) -> ShellImpact:
    """Parse a shell command string and assess its impact.

    This is a best-effort static analysis. It handles pipes, semicolons,
    and && chains but does not evaluate variables or subshells.
    """
    impact = ShellImpact(raw_command=command)

    # Split on pipes, semicolons, &&, ||
    segments = re.split(r"\s*(?:\|{1,2}|&&|;)\s*", command)
    impact.piped = "|" in command

    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue

        try:
            tokens = shlex.split(segment)
        except ValueError:
            tokens = segment.split()

        if not tokens:
            continue

        cmd = tokens[0].split("/")[-1]  # Handle full paths like /bin/rm
        impact.commands.append(cmd)

        if cmd in DESTRUCTIVE_COMMANDS:
            impact.is_destructive = True

        if cmd in NETWORK_COMMANDS:
            impact.is_network = True

        # Check all tokens for paths, URLs, and sensitive locations
        for token in tokens[1:]:
            # Check for URLs
            url_match = URL_PATTERN.search(token)
            if url_match:
                impact.network_destinations.append(url_match.group())
                impact.is_network = True

            # Check for sensitive paths
            for pattern in SENSITIVE_PATH_PATTERNS:
                if pattern.search(token):
                    impact.sensitive_paths.append(token)
                    impact.accesses_secrets = True
                    break

            # Collect target paths (non-flag tokens that look like paths)
            if not token.startswith("-") and ("/" in token or "." in token):
                impact.target_paths.append(token)

        # Special case: cat/head/tail reading sensitive files
        if cmd in SECRET_COMMANDS:
            for token in tokens[1:]:
                for pattern in SENSITIVE_PATH_PATTERNS:
                    if pattern.search(token):
                        impact.accesses_secrets = True
                        break

    return impact
