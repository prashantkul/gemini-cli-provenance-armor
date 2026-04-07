"""Stage 3: Delta masking — only scan newly-read content of known files."""

from __future__ import annotations

from provenance_armor._utils.hashing import sha256_str


class DeltaMask:
    """Tracks file content hashes to avoid re-scanning unchanged data.

    When a file is scanned, its hash is recorded. On subsequent scans,
    only the new/changed portion is returned for scanning.
    """

    def __init__(self) -> None:
        self._seen: dict[str, str] = {}  # source_uri -> hash of last scanned content
        self._content_cache: dict[str, str] = {}  # source_uri -> last scanned content

    def get_delta(self, source_uri: str, content: str) -> str:
        """Return only the new content that hasn't been scanned before.

        If the content hasn't changed, returns empty string.
        If the content is entirely new, returns the full content.
        If the content has been extended, returns only the new portion.
        """
        content_hash = sha256_str(content)
        prev_hash = self._seen.get(source_uri)

        if prev_hash == content_hash:
            # Content unchanged
            return ""

        prev_content = self._content_cache.get(source_uri, "")

        # Update cache
        self._seen[source_uri] = content_hash
        self._content_cache[source_uri] = content

        if not prev_content:
            # First time seeing this source
            return content

        # If the new content starts with the old content, return the delta
        if content.startswith(prev_content):
            return content[len(prev_content):]

        # Content was modified, not just appended — rescan everything
        return content

    def reset(self, source_uri: str | None = None) -> None:
        """Clear cached state for a source, or all sources if None."""
        if source_uri is None:
            self._seen.clear()
            self._content_cache.clear()
        else:
            self._seen.pop(source_uri, None)
            self._content_cache.pop(source_uri, None)
