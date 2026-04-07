"""Tests for intent classification."""

from provenance_armor.intent.classifier import IntentCategory, IntentClassifier


class TestIntentClassifier:
    def test_read_only(self):
        clf = IntentClassifier()
        result = clf.classify("Show me the contents of the config file")
        assert result.category == IntentCategory.READ_ONLY

    def test_refactor(self):
        clf = IntentClassifier()
        result = clf.classify("Refactor the authentication module and rename the class")
        assert result.category == IntentCategory.REFACTOR

    def test_destructive(self):
        clf = IntentClassifier()
        result = clf.classify("Delete all the temporary files and remove the cache")
        assert result.category == IntentCategory.DESTRUCTIVE

    def test_network(self):
        clf = IntentClassifier()
        result = clf.classify("Download the package from the API endpoint")
        assert result.category == IntentCategory.NETWORK_ACCESS

    def test_system_config(self):
        clf = IntentClassifier()
        result = clf.classify("Install the new dependency and configure the environment")
        assert result.category == IntentCategory.SYSTEM_CONFIG

    def test_unknown(self):
        clf = IntentClassifier()
        result = clf.classify("xyzzy plugh")
        assert result.category == IntentCategory.UNKNOWN
        assert result.confidence == 0.0
