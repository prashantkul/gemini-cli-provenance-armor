"""Stage 2: NER-based contextual PII detection (optional dependency: spaCy)."""

from __future__ import annotations

import logging
from typing import Any, Optional

from provenance_armor.models.redaction import RedactionCategory, RedactionHit, ScanResult

logger = logging.getLogger(__name__)

# Map spaCy entity labels to our categories
NER_LABEL_MAP: dict[str, RedactionCategory] = {
    "PERSON": RedactionCategory.PII_NAME,
    "GPE": RedactionCategory.PII_ADDRESS,
    "LOC": RedactionCategory.PII_ADDRESS,
    "ORG": RedactionCategory.PII_NAME,
    "FAC": RedactionCategory.PII_ADDRESS,
}

NER_PLACEHOLDER_MAP: dict[RedactionCategory, str] = {
    RedactionCategory.PII_NAME: "[REDACTED_NAME]",
    RedactionCategory.PII_ADDRESS: "[REDACTED_LOCATION]",
}


class NERScanner:
    """Stage 2 scanner using spaCy NER for context-aware PII detection.

    Requires the ``spacy`` optional dependency. Falls back gracefully
    if spaCy is not installed.
    """

    def __init__(self, model_name: str = "en_core_web_sm") -> None:
        self._model_name = model_name
        self._nlp: Optional[Any] = None
        self._available: Optional[bool] = None

    def _load_model(self) -> bool:
        """Attempt to load the spaCy model. Returns True if successful."""
        if self._available is not None:
            return self._available

        try:
            import spacy
            self._nlp = spacy.load(self._model_name)
            self._available = True
            logger.info("spaCy model '%s' loaded for NER scanning", self._model_name)
        except ImportError:
            logger.info("spaCy not installed — NER scanning disabled")
            self._available = False
        except OSError:
            logger.warning(
                "spaCy model '%s' not found — run: python -m spacy download %s",
                self._model_name,
                self._model_name,
            )
            self._available = False

        return self._available

    @property
    def available(self) -> bool:
        return self._load_model()

    def scan(self, text: str) -> ScanResult:
        """Scan text for PII entities using NER."""
        if not self._load_model() or self._nlp is None:
            return ScanResult(hits=[], stage="ner")

        doc = self._nlp(text)
        hits: list[RedactionHit] = []

        for ent in doc.ents:
            category = NER_LABEL_MAP.get(ent.label_)
            if category is None:
                continue

            placeholder = NER_PLACEHOLDER_MAP.get(category, "[REDACTED_PII]")
            hits.append(
                RedactionHit(
                    category=category,
                    matched_text=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    placeholder=placeholder,
                    confidence=0.85,  # NER confidence is lower than regex
                )
            )

        return ScanResult(hits=hits, stage="ner")
