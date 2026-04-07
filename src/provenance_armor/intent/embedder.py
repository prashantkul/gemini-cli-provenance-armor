"""Vector embeddings for user instructions and tool calls.

Uses sentence-transformers when available, falls back to a simple
bag-of-words TF approach for zero-dependency operation.
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from typing import Any, Optional

logger = logging.getLogger(__name__)


class IntentEmbedder:
    """Generates vector embeddings for text (instructions and tool calls).

    Tries to use sentence-transformers for high-quality embeddings.
    Falls back to a simple TF-based bag-of-words approach.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        self._model: Optional[Any] = None
        self._use_transformer: Optional[bool] = None

    def _init_model(self) -> bool:
        """Attempt to load sentence-transformers model."""
        if self._use_transformer is not None:
            return self._use_transformer

        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            self._use_transformer = True
            logger.info("Using sentence-transformers model: %s", self._model_name)
        except ImportError:
            logger.info("sentence-transformers not available — using fallback embedder")
            self._use_transformer = False

        return self._use_transformer

    def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text."""
        if self._init_model() and self._model is not None:
            return self._model.encode(text).tolist()
        return self._fallback_embed(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if self._init_model() and self._model is not None:
            return [v.tolist() for v in self._model.encode(texts)]
        return [self._fallback_embed(t) for t in texts]

    def _fallback_embed(self, text: str) -> list[float]:
        """Simple TF-based bag-of-words embedding (no dependencies).

        Uses a fixed vocabulary of security-relevant terms to create
        a sparse-then-normalized embedding.
        """
        tokens = _tokenize(text)
        tf = Counter(tokens)
        total = sum(tf.values()) or 1

        # Fixed vocabulary of security/tool-relevant terms
        vector = [tf.get(word, 0) / total for word in _VOCAB]

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


def _tokenize(text: str) -> list[str]:
    """Simple word tokenizer."""
    return re.findall(r"[a-z]+", text.lower())


# Fixed vocabulary for the fallback embedder — covers common
# terms in security-relevant instructions and tool calls
_VOCAB = [
    "read", "write", "delete", "remove", "create", "modify", "update",
    "file", "directory", "folder", "path", "config", "configuration",
    "run", "execute", "command", "shell", "script", "bash",
    "install", "package", "dependency", "module", "import",
    "git", "push", "pull", "commit", "branch", "merge",
    "curl", "wget", "fetch", "download", "upload", "send", "post",
    "ssh", "key", "token", "secret", "password", "credential",
    "api", "endpoint", "server", "request", "response",
    "test", "debug", "log", "error", "fix", "bug",
    "database", "query", "table", "schema", "migration",
    "docker", "container", "deploy", "build", "compile",
    "permission", "access", "allow", "deny", "block",
    "network", "port", "connection", "socket",
    "env", "environment", "variable", "export",
    "search", "find", "list", "show", "display", "print",
    "refactor", "rename", "move", "copy", "replace",
]
