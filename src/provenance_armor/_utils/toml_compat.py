"""TOML loading wrapper using stdlib tomllib (Python 3.11+)."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


def load_toml(path: Path) -> dict[str, Any]:
    """Load and parse a TOML file, returning a dict."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def loads_toml(text: str) -> dict[str, Any]:
    """Parse a TOML string, returning a dict."""
    return tomllib.loads(text)
