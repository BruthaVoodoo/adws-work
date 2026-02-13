"""
Unit tests for token_utils.py
"""

import pytest
from scripts.adw_modules.token_utils import (
    count_tokens,
    get_safe_token_limit,
    check_token_limit,
    calculate_overage_percentage,
    estimate_tokens_for_text,
    format_token_summary,
    SAFETY_MARGIN,
)


class TestCountTokens:
    """Test token counting functionality."""

    def test_count_tokens_simple(self):
        """Test basic token counting."""
        text = "Hello world"
        count = count_tokens(text)
        assert count > 0
        assert isinstance(count, int)

    def test_count_tokens_empty(self):
        """Test counting empty string."""
        assert count_tokens("") == 0

    def test_count_tokens_long(self):
        """Test counting longer text."""
        text = "This is a longer message with more tokens to count"
        count = count_tokens(text)
        assert count > 5  # Should have multiple tokens

    def test_count_tokens_accuracy_small(self):
        """Test token counting accuracy with known small text."""
        # "Hello world" typically encodes to 2 tokens in cl100k_base
        text = "Hello world"
        count = count_tokens(text)
        assert count == 2

    def test_count_tokens_accuracy_medium(self):
        """Test token counting accuracy with medium text."""
        # Test with known token count patterns
        text = "The quick brown fox jumps over the lazy dog"
        count = count_tokens(text)
        # Should be approximately 9-10 tokens
        assert 8 <= count <= 11

    def test_count_tokens_with_special_chars(self):
        """Test token counting with special characters."""
        text = "Error: {status: 500, message: 'Internal Server Error'}"
        count = count_tokens(text)
        assert count > 10  # Special chars increase token count

    def test_count_tokens_with_code(self):
        """Test token counting with code snippets."""
        code = """
        def test_function():
            assert 1 + 1 == 2
            return True
        """
        count = count_tokens(code)
        assert count > 15  # Code with indentation uses more tokens

    def test_count_tokens_unicode(self):
        """Test token counting with unicode characters."""
        text = "Hello 世界 🌍"
        count = count_tokens(text)
        assert count > 0
        assert isinstance(count, int)

    def test_count_tokens_large_text(self):
        """Test token counting with large text (simulating test output)."""
        # Simulate 128K token limit scenario
        large_text = "token " * 25000  # ~25K words
        count = count_tokens(large_text)
        assert count > 20000  # Should be substantial
        assert count < 150000  # But not unreasonably high


class TestSafeTokenLimit:
    """Test safe token limit calculations."""

    def test_get_safe_token_limit_128k(self):
        """Test safe limit for 128K model."""
        result = get_safe_token_limit(128000)
        assert result == 121600  # 95% of 128000

    def test_get_safe_token_limit_200k(self):
        """Test safe limit for 200K model."""
        result = get_safe_token_limit(200000)
        assert result == 190000  # 95% of 200000

    def test_safety_margin_value(self):
        """Verify safety margin constant."""
        assert SAFETY_MARGIN == 0.95


class TestCheckTokenLimit:
    """Test token limit checking."""

    def test_check_within_limit(self):
        """Test text within safe limit."""
        text = "Short text"
        within, count, safe_limit = check_token_limit(text, 128000)
        assert within is True
        assert count > 0
        assert safe_limit == 121600

    def test_check_exceeds_limit(self):
        """Test text exceeding limit."""
        # Create very long text
        text = "token " * 50000  # ~50K tokens
        within, count, safe_limit = check_token_limit(text, 10000)
        assert within is False
        assert count > safe_limit


class TestOveragePercentage:
    """Test overage percentage calculations."""

    def test_overage_positive(self):
        """Test positive overage (over limit)."""
        result = calculate_overage_percentage(184000, 128000)
        assert result == pytest.approx(43.75, rel=0.01)

    def test_overage_negative(self):
        """Test negative overage (under limit)."""
        result = calculate_overage_percentage(100000, 128000)
        assert result < 0

    def test_overage_exact(self):
        """Test exact limit (0% overage)."""
        result = calculate_overage_percentage(128000, 128000)
        assert result == 0.0


class TestEstimateTokens:
    """Test token estimation."""

    def test_estimate_basic(self):
        """Test basic estimation."""
        text = "test"  # 4 chars = ~1 token
        estimate = estimate_tokens_for_text(text)
        assert estimate == 1

    def test_estimate_longer(self):
        """Test longer text estimation."""
        text = "a" * 400  # 400 chars = ~100 tokens
        estimate = estimate_tokens_for_text(text)
        assert estimate == 100


class TestFormatTokenSummary:
    """Test token summary formatting."""

    def test_format_within_safe(self):
        """Test formatting when within safe margin."""
        summary = format_token_summary(100000, 128000)
        assert "100,000 tokens" in summary
        assert "within safe margin" in summary

    def test_format_exceeds_safe(self):
        """Test formatting when exceeds safe but under limit."""
        summary = format_token_summary(125000, 128000)
        assert "125,000 tokens" in summary
        assert "exceeds safe margin" in summary

    def test_format_exceeds_limit(self):
        """Test formatting when exceeds limit."""
        summary = format_token_summary(184000, 128000)
        assert "184,000 tokens" in summary
        assert "EXCEEDS LIMIT" in summary
        assert "43.8%" in summary or "43.7%" in summary  # Allow rounding variance

    def test_format_with_custom_safe_limit(self):
        """Test formatting with custom safe limit."""
        summary = format_token_summary(100000, 128000, safe_limit=90000)
        assert "100,000 tokens" in summary
