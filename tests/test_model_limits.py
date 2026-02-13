"""
Unit tests for model_limits.py
Tests model token limit registry functionality.
"""

import pytest
from scripts.adw_modules.model_limits import (
    get_model_limit,
    get_all_models,
    is_model_supported,
    MODEL_TOKEN_LIMITS,
    DEFAULT_TOKEN_LIMIT,
)


class TestGetModelLimit:
    """Test get_model_limit() function."""

    def test_github_copilot_sonnet_4(self):
        """Should return 128K for Sonnet 4."""
        assert get_model_limit("github-copilot/claude-sonnet-4") == 128_000

    def test_github_copilot_haiku_4_5(self):
        """Should return 128K for Haiku 4.5."""
        assert get_model_limit("github-copilot/claude-haiku-4.5") == 128_000

    def test_github_copilot_opus_4(self):
        """Should return 200K for Opus 4."""
        assert get_model_limit("github-copilot/claude-opus-4") == 200_000

    def test_anthropic_direct_sonnet_4(self):
        """Should return 128K for direct Anthropic Sonnet 4 ID."""
        assert get_model_limit("claude-sonnet-4") == 128_000

    def test_anthropic_direct_opus_4(self):
        """Should return 200K for direct Anthropic Opus 4 ID."""
        assert get_model_limit("claude-opus-4") == 200_000

    def test_versioned_model_id(self):
        """Should return correct limit for versioned model IDs."""
        assert get_model_limit("claude-sonnet-4-20250514") == 128_000
        assert get_model_limit("claude-opus-4-20250514") == 200_000

    def test_legacy_model_3_5_sonnet(self):
        """Should return 200K for legacy Claude 3.5 Sonnet."""
        assert get_model_limit("claude-3-5-sonnet-20241022") == 200_000

    def test_legacy_model_3_5_haiku(self):
        """Should return 200K for legacy Claude 3.5 Haiku."""
        assert get_model_limit("claude-3-5-haiku-20241022") == 200_000

    def test_unknown_model_returns_default(self):
        """Should return default limit for unknown model."""
        assert get_model_limit("unknown-model-xyz") == DEFAULT_TOKEN_LIMIT

    def test_empty_string_returns_default(self):
        """Should return default limit for empty string."""
        assert get_model_limit("") == DEFAULT_TOKEN_LIMIT

    def test_partial_match_sonnet(self):
        """Should match partial model ID containing 'sonnet-4'."""
        # Partial match should find github-copilot/claude-sonnet-4
        result = get_model_limit("sonnet-4")
        assert result == 128_000

    def test_partial_match_opus(self):
        """Should match partial model ID containing 'opus-4'."""
        # Partial match should find github-copilot/claude-opus-4
        result = get_model_limit("opus-4")
        assert result == 200_000

    def test_case_insensitive_match(self):
        """Should match model IDs case-insensitively."""
        assert get_model_limit("GITHUB-COPILOT/CLAUDE-SONNET-4") == 128_000
        assert get_model_limit("Claude-Opus-4") == 200_000


class TestGetAllModels:
    """Test get_all_models() function."""

    def test_returns_dict(self):
        """Should return dictionary."""
        result = get_all_models()
        assert isinstance(result, dict)

    def test_contains_expected_models(self):
        """Should contain all expected model IDs."""
        result = get_all_models()
        assert "github-copilot/claude-sonnet-4" in result
        assert "github-copilot/claude-haiku-4.5" in result
        assert "github-copilot/claude-opus-4" in result
        assert "claude-sonnet-4" in result
        assert "claude-opus-4" in result

    def test_returns_copy(self):
        """Should return copy, not reference to original."""
        result = get_all_models()
        result["test-model"] = 999_999
        # Original dict should not be modified
        assert "test-model" not in MODEL_TOKEN_LIMITS

    def test_values_are_positive_integers(self):
        """Should have positive integer values for all models."""
        result = get_all_models()
        for model_id, limit in result.items():
            assert isinstance(limit, int), f"{model_id} limit should be int"
            assert limit > 0, f"{model_id} limit should be positive"

    def test_expected_count(self):
        """Should return expected number of models."""
        result = get_all_models()
        # At least 10 models should be registered
        assert len(result) >= 10


class TestIsModelSupported:
    """Test is_model_supported() function."""

    def test_supported_github_copilot_models(self):
        """Should return True for GitHub Copilot models."""
        assert is_model_supported("github-copilot/claude-sonnet-4") is True
        assert is_model_supported("github-copilot/claude-haiku-4.5") is True
        assert is_model_supported("github-copilot/claude-opus-4") is True

    def test_supported_anthropic_direct_models(self):
        """Should return True for direct Anthropic model IDs."""
        assert is_model_supported("claude-sonnet-4") is True
        assert is_model_supported("claude-opus-4") is True

    def test_unsupported_model(self):
        """Should return False for unknown model."""
        assert is_model_supported("unknown-model") is False
        assert is_model_supported("gpt-4") is False

    def test_empty_string(self):
        """Should return False for empty string."""
        assert is_model_supported("") is False

    def test_partial_match_not_supported(self):
        """Should not return True for partial matches."""
        # is_model_supported checks exact match only
        assert is_model_supported("sonnet-4") is False
        assert is_model_supported("opus") is False

    def test_case_sensitive(self):
        """Should be case-sensitive for exact match check."""
        # Exact match is case-sensitive
        assert is_model_supported("GITHUB-COPILOT/CLAUDE-SONNET-4") is False


class TestModelLimitsRegistry:
    """Test MODEL_TOKEN_LIMITS constant."""

    def test_registry_is_dict(self):
        """Should be a dictionary."""
        assert isinstance(MODEL_TOKEN_LIMITS, dict)

    def test_registry_not_empty(self):
        """Should not be empty."""
        assert len(MODEL_TOKEN_LIMITS) > 0

    def test_all_limits_reasonable(self):
        """Should have reasonable token limits (50K - 1M range)."""
        for model_id, limit in MODEL_TOKEN_LIMITS.items():
            assert 50_000 <= limit <= 1_000_000, (
                f"{model_id} has unreasonable limit: {limit}"
            )

    def test_primary_models_correct_limits(self):
        """Should have correct limits for primary models."""
        assert MODEL_TOKEN_LIMITS["github-copilot/claude-sonnet-4"] == 128_000
        assert MODEL_TOKEN_LIMITS["github-copilot/claude-haiku-4.5"] == 128_000
        assert MODEL_TOKEN_LIMITS["github-copilot/claude-opus-4"] == 200_000


class TestDefaultTokenLimit:
    """Test DEFAULT_TOKEN_LIMIT constant."""

    def test_default_is_integer(self):
        """Should be an integer."""
        assert isinstance(DEFAULT_TOKEN_LIMIT, int)

    def test_default_is_positive(self):
        """Should be positive."""
        assert DEFAULT_TOKEN_LIMIT > 0

    def test_default_is_conservative(self):
        """Should be conservative (less than smallest known limit)."""
        min_known_limit = min(MODEL_TOKEN_LIMITS.values())
        assert DEFAULT_TOKEN_LIMIT <= min_known_limit


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_none_input(self):
        """Should handle None gracefully (though type hints say str)."""
        # If called with None, should not crash
        # Implementation will treat None as unknown model
        try:
            result = get_model_limit(None)  # type: ignore
            assert result == DEFAULT_TOKEN_LIMIT
        except (TypeError, AttributeError):
            # Acceptable to raise error for None
            pass

    def test_numeric_input(self):
        """Should handle non-string input gracefully."""
        try:
            result = get_model_limit(12345)  # type: ignore
            assert result == DEFAULT_TOKEN_LIMIT
        except (TypeError, AttributeError):
            # Acceptable to raise error for non-string
            pass

    def test_whitespace_model_id(self):
        """Should handle whitespace-only model ID."""
        assert get_model_limit("   ") == DEFAULT_TOKEN_LIMIT

    def test_model_id_with_extra_whitespace(self):
        """Should strip whitespace and match model IDs correctly."""
        # Implementation strips whitespace for better UX
        assert get_model_limit(" github-copilot/claude-sonnet-4 ") == 128_000
        assert get_model_limit("\tgithub-copilot/claude-opus-4\n") == 200_000
