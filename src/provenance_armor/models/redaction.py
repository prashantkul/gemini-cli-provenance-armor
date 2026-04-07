"""Redaction engine data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class RedactionCategory(Enum):
    """Type of sensitive data detected."""

    AWS_KEY = auto()
    API_KEY = auto()
    SSH_KEY = auto()
    CREDIT_CARD = auto()
    EMAIL = auto()
    PHONE = auto()
    IP_ADDRESS = auto()
    PASSWORD = auto()
    PII_NAME = auto()
    PII_ADDRESS = auto()
    ENV_VARIABLE = auto()
    GENERIC_SECRET = auto()


@dataclass(frozen=True)
class RedactionHit:
    """A single detected sensitive data occurrence."""

    category: RedactionCategory
    matched_text: str
    start: int         # Character offset in source text
    end: int           # Character offset end
    placeholder: str   # e.g., "[REDACTED_AWS_KEY]"
    confidence: float = 1.0  # 1.0 for regex, lower for NER


@dataclass
class ScanResult:
    """Result from a single scanning stage."""

    hits: list[RedactionHit] = field(default_factory=list)
    stage: str = ""  # "regex", "ner", "delta"


@dataclass
class RedactedContent:
    """Final output of the redaction pipeline."""

    original_length: int = 0
    redacted_text: str = ""
    hits: list[RedactionHit] = field(default_factory=list)
    stages_applied: list[str] = field(default_factory=list)

    @property
    def redaction_count(self) -> int:
        return len(self.hits)

    @property
    def has_redactions(self) -> bool:
        return len(self.hits) > 0
