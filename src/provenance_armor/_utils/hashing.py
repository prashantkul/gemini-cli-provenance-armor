"""SHA-256 hashing utilities for integrity verification."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    """Return hex SHA-256 digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Return hex SHA-256 digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_str(text: str) -> str:
    """Return hex SHA-256 digest of a string (UTF-8 encoded)."""
    return sha256_bytes(text.encode())
