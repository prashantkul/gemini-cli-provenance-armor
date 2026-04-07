"""Intent classification: maps user instructions to permission profiles."""

from __future__ import annotations

import re
from enum import Enum, auto
from dataclasses import dataclass


class IntentCategory(Enum):
    """High-level intent categories that map to permission sets."""

    READ_ONLY = auto()       # Browsing, reading, searching
    REFACTOR = auto()        # Code changes, renames, restructuring
    SYSTEM_CONFIG = auto()   # Installing packages, changing configs
    NETWORK_ACCESS = auto()  # Fetching URLs, API calls
    DESTRUCTIVE = auto()     # Deleting files, dropping tables
    UNKNOWN = auto()


@dataclass(frozen=True)
class ClassificationResult:
    """Result of classifying a user instruction."""

    category: IntentCategory
    confidence: float          # 0.0 to 1.0
    matched_keywords: list[str]


# Keyword-to-category mapping
_CATEGORY_KEYWORDS: dict[IntentCategory, list[str]] = {
    IntentCategory.READ_ONLY: [
        "read", "show", "display", "list", "find", "search", "look",
        "check", "view", "examine", "inspect", "what is", "explain",
        "understand", "describe", "analyze",
    ],
    IntentCategory.REFACTOR: [
        "refactor", "rename", "restructure", "rewrite", "improve",
        "clean up", "organize", "simplify", "extract", "inline",
        "move", "split", "merge", "update", "change", "modify",
        "fix", "add", "implement", "create", "write",
    ],
    IntentCategory.SYSTEM_CONFIG: [
        "install", "configure", "setup", "set up", "initialize",
        "upgrade", "update package", "pip install", "npm install",
        "apt install", "brew install", "docker",
    ],
    IntentCategory.NETWORK_ACCESS: [
        "fetch", "download", "upload", "curl", "wget", "api call",
        "http", "request", "endpoint", "url", "deploy", "push",
        "publish", "send",
    ],
    IntentCategory.DESTRUCTIVE: [
        "delete", "remove", "destroy", "drop", "truncate", "wipe",
        "clear", "reset", "purge", "rm -rf", "uninstall",
    ],
}


class IntentClassifier:
    """Classifies user instructions into intent categories.

    Uses keyword matching for fast, deterministic classification.
    The resulting category maps to a permission profile that restricts
    which tools are available during the session.
    """

    def classify(self, instruction: str) -> ClassificationResult:
        """Classify a user instruction into an IntentCategory."""
        text = instruction.lower()
        scores: dict[IntentCategory, list[str]] = {}

        for category, keywords in _CATEGORY_KEYWORDS.items():
            matched = [kw for kw in keywords if kw in text]
            if matched:
                scores[category] = matched

        if not scores:
            return ClassificationResult(
                category=IntentCategory.UNKNOWN,
                confidence=0.0,
                matched_keywords=[],
            )

        # Pick the category with the most keyword matches
        best_category = max(scores, key=lambda c: len(scores[c]))
        best_keywords = scores[best_category]

        # Confidence is based on number of matches relative to total keywords
        total_keywords = len(_CATEGORY_KEYWORDS[best_category])
        confidence = min(1.0, len(best_keywords) / max(3, total_keywords / 2))

        return ClassificationResult(
            category=best_category,
            confidence=confidence,
            matched_keywords=best_keywords,
        )
