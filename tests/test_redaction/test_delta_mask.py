"""Tests for delta masking."""

from provenance_armor.redaction.delta_mask import DeltaMask


class TestDeltaMask:
    def test_first_scan_returns_full(self):
        dm = DeltaMask()
        content = "Hello World"
        assert dm.get_delta("/file.txt", content) == content

    def test_unchanged_returns_empty(self):
        dm = DeltaMask()
        content = "Hello World"
        dm.get_delta("/file.txt", content)
        assert dm.get_delta("/file.txt", content) == ""

    def test_appended_returns_delta(self):
        dm = DeltaMask()
        dm.get_delta("/file.txt", "Hello")
        delta = dm.get_delta("/file.txt", "Hello World")
        assert delta == " World"

    def test_modified_returns_full(self):
        dm = DeltaMask()
        dm.get_delta("/file.txt", "Hello")
        delta = dm.get_delta("/file.txt", "Goodbye")
        assert delta == "Goodbye"

    def test_different_sources_independent(self):
        dm = DeltaMask()
        dm.get_delta("/a.txt", "content a")
        dm.get_delta("/b.txt", "content b")
        assert dm.get_delta("/a.txt", "content a") == ""
        assert dm.get_delta("/b.txt", "content b new") == " new"

    def test_reset_single(self):
        dm = DeltaMask()
        dm.get_delta("/file.txt", "Hello")
        dm.reset("/file.txt")
        assert dm.get_delta("/file.txt", "Hello") == "Hello"

    def test_reset_all(self):
        dm = DeltaMask()
        dm.get_delta("/a.txt", "a")
        dm.get_delta("/b.txt", "b")
        dm.reset()
        assert dm.get_delta("/a.txt", "a") == "a"
        assert dm.get_delta("/b.txt", "b") == "b"
