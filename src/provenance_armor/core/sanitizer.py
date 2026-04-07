"""Sanitize-and-Retry: strips injected instructions from poisoned spans."""

from __future__ import annotations

import copy
import re

from provenance_armor.models.context import ContextWindow, SpanKind
from provenance_armor.models.scoring import DominanceResult

# Patterns commonly used in indirect prompt injections.
# These match imperative instructions that attempt to hijack agent behavior.
INJECTION_PATTERNS = [
    # Direct instruction hijacking
    re.compile(r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|context)\b"),
    re.compile(r"(?i)\bdisregard\s+(all\s+)?(previous|prior|above)\b"),
    re.compile(r"(?i)\bforget\s+(everything|all)\s+(above|before|previously)\b"),
    # Command injection
    re.compile(r"(?i)\b(execute|run|perform)\s+(the\s+following|this)\s+(command|script|code)\b"),
    re.compile(r"(?i)\byou\s+must\s+(now\s+)?(execute|run|perform|do)\b"),
    re.compile(r"(?i)\b(instead|now)\s*,?\s*(execute|run|do|perform)\b"),
    # Role manipulation
    re.compile(r"(?i)\byou\s+are\s+(now\s+)?a\b"),
    re.compile(r"(?i)\bact\s+as\s+(if\s+you\s+are|a)\b"),
    re.compile(r"(?i)\bpretend\s+(to\s+be|you\s+are)\b"),
    re.compile(r"(?i)\byour\s+new\s+(role|instructions?|task)\b"),
    # Output manipulation
    re.compile(r"(?i)\b(do\s+not|don't|never)\s+(mention|reveal|tell|show|display)\b"),
    re.compile(r"(?i)\bhide\s+(this|the)\s+(from|in)\b"),
    # Exfiltration attempts
    re.compile(r"(?i)\b(send|post|upload|exfiltrate|transmit)\s+(to|all|the|this)\b"),
    re.compile(r"(?i)\bfetch\s+https?://\S+\s+(and|with|using)\b"),
    # System prompt extraction
    re.compile(r"(?i)\b(print|show|reveal|output)\s+(your\s+)?(system\s+prompt|instructions)\b"),
]

# Pattern for hidden Unicode tricks (zero-width chars, RTL override, etc.)
UNICODE_TRICKS_PATTERN = re.compile(
    r"[\u200b\u200c\u200d\u200e\u200f\u202a-\u202e\u2060\u2061-\u2064\ufeff]"
)


class CausalSanitizer:
    """Implements the Sanitize-and-Retry loop.

    When causal dominance is detected:
    1. Identify the poisoned spans (untrusted spans with highest influence)
    2. Strip imperative instructions from those spans
    3. Remove hidden Unicode tricks
    4. Return a cleaned ContextWindow for regeneration
    """

    def sanitize(
        self,
        context: ContextWindow,
        dominance: DominanceResult,
    ) -> ContextWindow:
        """Return a sanitized copy of the context.

        Only spans identified as dominant in the DominanceResult are cleaned.
        Factual content is preserved; only injected instructions are stripped.
        """
        cleaned = copy.deepcopy(context)
        dominant_ids = set(dominance.dominant_spans)

        for span in cleaned.spans:
            if span.span_id in dominant_ids:
                span.content = self.strip_instructions(span.content)
                span.content = self.strip_unicode_tricks(span.content)

        return cleaned

    def strip_instructions(self, text: str) -> str:
        """Remove injected instruction patterns from text.

        Replaces matched injection patterns with a sanitization marker,
        preserving the surrounding factual content.
        """
        result = text
        for pattern in INJECTION_PATTERNS:
            result = pattern.sub("[SANITIZED_INSTRUCTION]", result)
        return result

    def strip_unicode_tricks(self, text: str) -> str:
        """Remove hidden Unicode characters used for obfuscation."""
        return UNICODE_TRICKS_PATTERN.sub("", text)

    def redact_cot(self, cot_text: str, poisoned_content: list[str]) -> str:
        """Redact Chain-of-Thought segments that reference poisoned content.

        Replaces any substring from the poisoned content that appears
        in the agent's CoT with a redaction marker.
        """
        result = cot_text
        for content in poisoned_content:
            # Extract significant phrases (4+ words) from poisoned content
            sentences = re.split(r"[.!?\n]", content)
            for sentence in sentences:
                phrase = sentence.strip()
                if len(phrase.split()) >= 4 and phrase in result:
                    result = result.replace(phrase, "[REDACTED_COT]")
        return result
