"""Tests for the regex scanner."""

from provenance_armor.redaction.regex_scanner import RegexScanner
from provenance_armor.models.redaction import RedactionCategory


class TestRegexScanner:
    def test_aws_key_detection(self):
        scanner = RegexScanner()
        text = "My key is AKIAIOSFODNN7EXAMPLE"
        result = scanner.scan(text)
        aws_hits = [h for h in result.hits if h.category == RedactionCategory.AWS_KEY]
        assert len(aws_hits) >= 1
        assert "AKIAIOSFODNN7EXAMPLE" in aws_hits[0].matched_text

    def test_github_token(self):
        scanner = RegexScanner()
        text = "Token: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef1234"
        result = scanner.scan(text)
        api_hits = [h for h in result.hits if h.category == RedactionCategory.API_KEY]
        assert len(api_hits) >= 1

    def test_email_detection(self):
        scanner = RegexScanner()
        text = "Contact: user@example.com for details"
        result = scanner.scan(text)
        email_hits = [h for h in result.hits if h.category == RedactionCategory.EMAIL]
        assert len(email_hits) == 1
        assert email_hits[0].matched_text == "user@example.com"

    def test_credit_card(self):
        scanner = RegexScanner()
        text = "Card: 4111-1111-1111-1111"
        result = scanner.scan(text)
        cc_hits = [h for h in result.hits if h.category == RedactionCategory.CREDIT_CARD]
        assert len(cc_hits) == 1

    def test_ssh_key_header(self):
        scanner = RegexScanner()
        text = "-----BEGIN RSA PRIVATE KEY-----\nMIIE..."
        result = scanner.scan(text)
        ssh_hits = [h for h in result.hits if h.category == RedactionCategory.SSH_KEY]
        assert len(ssh_hits) == 1

    def test_password_in_config(self):
        scanner = RegexScanner()
        text = 'password=my_secret_pass123'
        result = scanner.scan(text)
        pw_hits = [h for h in result.hits if h.category == RedactionCategory.PASSWORD]
        assert len(pw_hits) == 1

    def test_no_false_positives_on_clean_text(self):
        scanner = RegexScanner()
        text = "This is a normal sentence about writing code."
        result = scanner.scan(text)
        assert len(result.hits) == 0

    def test_bearer_token(self):
        scanner = RegexScanner()
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"
        result = scanner.scan(text)
        secret_hits = [h for h in result.hits if h.category == RedactionCategory.GENERIC_SECRET]
        assert len(secret_hits) >= 1
