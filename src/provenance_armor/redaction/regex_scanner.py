"""Stage 1: Deterministic regex-based secret and PII detection."""

from __future__ import annotations

import re

from provenance_armor.models.redaction import RedactionCategory, RedactionHit, ScanResult

# Pattern definitions: (compiled regex, category, placeholder)
PATTERNS: list[tuple[re.Pattern, RedactionCategory, str]] = [
    # AWS Access Key ID (starts with AKIA)
    (
        re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        RedactionCategory.AWS_KEY,
        "[REDACTED_AWS_KEY]",
    ),
    # AWS Secret Access Key (40-char base64)
    (
        re.compile(r"\b([0-9a-zA-Z/+=]{40})\b"),
        RedactionCategory.AWS_KEY,
        "[REDACTED_AWS_SECRET]",
    ),
    # Generic API keys (long hex or alphanumeric strings with key-like prefixes)
    (
        re.compile(r"\b((?:sk|pk|api|key|token|secret|password)[-_]?[a-zA-Z0-9]{20,})\b", re.IGNORECASE),
        RedactionCategory.API_KEY,
        "[REDACTED_API_KEY]",
    ),
    # GitHub Personal Access Token
    (
        re.compile(r"\b(ghp_[a-zA-Z0-9]{36})\b"),
        RedactionCategory.API_KEY,
        "[REDACTED_GITHUB_TOKEN]",
    ),
    # SSH Private Key header
    (
        re.compile(r"(-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----)", re.IGNORECASE),
        RedactionCategory.SSH_KEY,
        "[REDACTED_SSH_KEY]",
    ),
    # Credit card numbers (basic Luhn-compatible patterns)
    (
        re.compile(r"\b(\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4})\b"),
        RedactionCategory.CREDIT_CARD,
        "[REDACTED_CREDIT_CARD]",
    ),
    # Email addresses
    (
        re.compile(r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b"),
        RedactionCategory.EMAIL,
        "[REDACTED_EMAIL]",
    ),
    # US phone numbers
    (
        re.compile(r"\b(\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})\b"),
        RedactionCategory.PHONE,
        "[REDACTED_PHONE]",
    ),
    # IPv4 addresses (non-local)
    (
        re.compile(r"\b((?!127\.0\.0\.1|0\.0\.0\.0)(?:\d{1,3}\.){3}\d{1,3})\b"),
        RedactionCategory.IP_ADDRESS,
        "[REDACTED_IP]",
    ),
    # Password in key=value or JSON contexts
    (
        re.compile(r'(?:password|passwd|pwd)\s*[:=]\s*["\']?([^\s"\']+)', re.IGNORECASE),
        RedactionCategory.PASSWORD,
        "[REDACTED_PASSWORD]",
    ),
    # Generic secret patterns (bearer tokens, authorization headers)
    (
        re.compile(r"\b(Bearer\s+[a-zA-Z0-9._~+/=-]+)\b", re.IGNORECASE),
        RedactionCategory.GENERIC_SECRET,
        "[REDACTED_BEARER_TOKEN]",
    ),
]


class RegexScanner:
    """Stage 1 scanner using deterministic regex patterns."""

    def scan(self, text: str) -> ScanResult:
        """Scan text for secrets and PII using regex patterns."""
        hits: list[RedactionHit] = []

        for pattern, category, placeholder in PATTERNS:
            for match in pattern.finditer(text):
                hits.append(
                    RedactionHit(
                        category=category,
                        matched_text=match.group(0),
                        start=match.start(),
                        end=match.end(),
                        placeholder=placeholder,
                        confidence=1.0,
                    )
                )

        return ScanResult(hits=hits, stage="regex")
