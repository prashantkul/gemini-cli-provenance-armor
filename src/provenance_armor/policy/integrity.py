"""Policy file integrity verification using SHA-256 checksums."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from provenance_armor._utils.hashing import sha256_file

logger = logging.getLogger(__name__)

CHECKSUM_FILE_NAME = ".policy-checksums.json"


class IntegrityVerifier:
    """Verifies that policy files have not been tampered with.

    Stores SHA-256 checksums in a sidecar JSON file alongside the
    policy directory. On verification, compares current file hashes
    against stored checksums.
    """

    def __init__(self, checksum_dir: Optional[Path] = None) -> None:
        self._checksum_dir = checksum_dir or Path.home() / ".config" / "provenance-armor"

    @property
    def checksum_path(self) -> Path:
        return self._checksum_dir / CHECKSUM_FILE_NAME

    def compute_checksums(self, *policy_paths: Path) -> dict[str, str]:
        """Compute SHA-256 checksums for the given policy files."""
        checksums: dict[str, str] = {}
        for path in policy_paths:
            if path.exists():
                checksums[str(path)] = sha256_file(path)
        return checksums

    def store_checksums(self, checksums: dict[str, str]) -> None:
        """Write checksums to the sidecar file."""
        self._checksum_dir.mkdir(parents=True, exist_ok=True)
        with open(self.checksum_path, "w") as f:
            json.dump(checksums, f, indent=2)
        logger.info("Stored policy checksums at %s", self.checksum_path)

    def load_checksums(self) -> dict[str, str]:
        """Load previously stored checksums."""
        if not self.checksum_path.exists():
            return {}
        with open(self.checksum_path) as f:
            return json.load(f)

    def verify(self, *policy_paths: Path) -> tuple[bool, list[str]]:
        """Verify policy files against stored checksums.

        Returns (all_ok, list_of_violations). If no stored checksums
        exist, returns (False, ["no stored checksums"]).
        """
        stored = self.load_checksums()
        if not stored:
            return False, ["No stored checksums found. Run 'store' first."]

        violations: list[str] = []
        current = self.compute_checksums(*policy_paths)

        for path_str, expected_hash in stored.items():
            actual_hash = current.get(path_str)
            if actual_hash is None:
                violations.append(f"Policy file missing: {path_str}")
            elif actual_hash != expected_hash:
                violations.append(
                    f"Policy file modified: {path_str} "
                    f"(expected {expected_hash[:16]}..., "
                    f"got {actual_hash[:16]}...)"
                )

        return len(violations) == 0, violations
