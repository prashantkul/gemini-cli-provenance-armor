"""RedactionEngine: orchestrates the 3-stage redaction pipeline.

Pipeline:
  Stage 1: RegexScanner  — deterministic pattern matching
  Stage 2: NERScanner    — context-aware PII detection (optional)
  Stage 3: DeltaMask     — skip already-scanned content
"""

from __future__ import annotations

from provenance_armor.models.redaction import RedactedContent, RedactionHit, ScanResult
from provenance_armor.redaction.delta_mask import DeltaMask
from provenance_armor.redaction.env_masker import EnvMasker
from provenance_armor.redaction.ner_scanner import NERScanner
from provenance_armor.redaction.regex_scanner import RegexScanner


class RedactionEngine:
    """Orchestrates multi-stage redaction of sensitive data.

    Runs all enabled stages in order, merges hits, resolves overlaps,
    and produces the final redacted text with semantic placeholders.
    """

    def __init__(
        self,
        enable_ner: bool = True,
        enable_delta: bool = True,
        enable_env: bool = True,
    ) -> None:
        self._regex = RegexScanner()
        self._ner = NERScanner() if enable_ner else None
        self._delta = DeltaMask() if enable_delta else None
        self._env = EnvMasker() if enable_env else None

    def scan(
        self,
        text: str,
        source_uri: str | None = None,
    ) -> RedactedContent:
        """Run the full redaction pipeline on text.

        Args:
            text: The text to scan and redact.
            source_uri: Optional source identifier for delta masking.
        """
        scan_text = text
        stages: list[str] = []

        # Stage 3 (pre-filter): Delta masking to reduce scan volume
        if self._delta and source_uri:
            scan_text = self._delta.get_delta(source_uri, text)
            stages.append("delta")
            if not scan_text:
                return RedactedContent(
                    original_length=len(text),
                    redacted_text=text,
                    stages_applied=stages,
                )

        all_hits: list[RedactionHit] = []

        # Stage 1: Regex scanning
        regex_result = self._regex.scan(scan_text)
        all_hits.extend(regex_result.hits)
        stages.append("regex")

        # Stage 2: NER scanning (if available)
        if self._ner and self._ner.available:
            ner_result = self._ner.scan(scan_text)
            all_hits.extend(ner_result.hits)
            stages.append("ner")

        # Env masking (applied to the full text)
        if self._env:
            text = self._env.mask_text(text)
            stages.append("env")

        # Merge, deduplicate, and apply redactions
        merged = self._merge_hits(all_hits)
        redacted = self._apply_redactions(text, merged)

        return RedactedContent(
            original_length=len(text),
            redacted_text=redacted,
            hits=merged,
            stages_applied=stages,
        )

    def _merge_hits(self, hits: list[RedactionHit]) -> list[RedactionHit]:
        """Merge overlapping hits, preferring higher confidence."""
        if not hits:
            return []

        # Sort by start position, then by confidence (descending)
        sorted_hits = sorted(hits, key=lambda h: (h.start, -h.confidence))

        merged: list[RedactionHit] = [sorted_hits[0]]
        for hit in sorted_hits[1:]:
            last = merged[-1]
            if hit.start < last.end:
                # Overlapping — keep the one with higher confidence
                if hit.confidence > last.confidence:
                    merged[-1] = hit
            else:
                merged.append(hit)

        return merged

    def _apply_redactions(
        self, text: str, hits: list[RedactionHit]
    ) -> str:
        """Apply redactions to text, replacing matched content with placeholders."""
        if not hits:
            return text

        # Sort by position (reverse) to avoid offset shifting
        sorted_hits = sorted(hits, key=lambda h: h.start, reverse=True)
        result = text
        for hit in sorted_hits:
            result = result[:hit.start] + hit.placeholder + result[hit.end:]

        return result
