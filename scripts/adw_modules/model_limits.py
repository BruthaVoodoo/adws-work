"""
Model token limits registry for supported LLM models.

This module maintains token limit mappings for all models available through
GitHub Copilot and OpenCode. Used for pre-flight validation to prevent
token limit errors during API calls.

Sources:
- Claude Sonnet 4: https://docs.anthropic.com/en/docs/about-claude/models#model-comparison
- Claude Haiku 4.5: https://docs.anthropic.com/en/docs/about-claude/models#model-comparison
- Claude Opus 4: https://docs.anthropic.com/en/docs/about-claude/models#model-comparison

Last Updated: 2026-02-13
"""

from typing import Optional

# Token limits for supported models (in tokens)
# These are context window limits - the maximum total tokens (input + output)
MODEL_TOKEN_LIMITS = {
    # GitHub Copilot model IDs (via OpenCode)
    "github-copilot/claude-sonnet-4.5": 128_000,
    "github-copilot/claude-sonnet-4": 128_000,
    "github-copilot/claude-haiku-4.5": 128_000,
    "github-copilot/claude-opus-4": 200_000,
    # Anthropic direct model IDs (for future compatibility)
    "claude-sonnet-4": 128_000,
    "claude-sonnet-4-20250514": 128_000,
    "claude-haiku-4.5": 128_000,
    "claude-haiku-4.5-20250514": 128_000,
    "claude-opus-4": 200_000,
    "claude-opus-4-20250514": 200_000,
    # Legacy model IDs (older versions)
    "claude-3-5-sonnet-20241022": 200_000,
    "claude-3-5-haiku-20241022": 200_000,
    "claude-3-opus-20240229": 200_000,
    "claude-3-sonnet-20240229": 200_000,
    "claude-3-haiku-20240307": 200_000,
}

# Default fallback limit if model not found (conservative estimate)
DEFAULT_TOKEN_LIMIT = 100_000


def get_model_limit(model_id: str) -> int:
    """
    Get the token limit for a given model ID.

    Args:
        model_id: The model identifier (e.g., "github-copilot/claude-sonnet-4")

    Returns:
        Token limit in tokens. Returns DEFAULT_TOKEN_LIMIT if model not found.

    Examples:
        >>> get_model_limit("github-copilot/claude-sonnet-4")
        128000
        >>> get_model_limit("github-copilot/claude-opus-4")
        200000
        >>> get_model_limit("unknown-model")
        100000
    """
    limit = MODEL_TOKEN_LIMITS.get(model_id)

    if limit is None:
        # Try partial match for flexibility (e.g., "sonnet-4" matches "claude-sonnet-4")
        # Only if model_id is non-empty and has meaningful content
        model_id_stripped = model_id.strip()
        if model_id_stripped:
            model_id_lower = model_id_stripped.lower()
            for known_model, known_limit in MODEL_TOKEN_LIMITS.items():
                if (
                    model_id_lower in known_model.lower()
                    or known_model.lower() in model_id_lower
                ):
                    return known_limit

        # No match found, return default
        return DEFAULT_TOKEN_LIMIT

    return limit


def get_all_models() -> dict[str, int]:
    """
    Get all registered models and their token limits.

    Returns:
        Dictionary mapping model IDs to token limits.

    Example:
        >>> limits = get_all_models()
        >>> limits["github-copilot/claude-sonnet-4"]
        128000
    """
    return MODEL_TOKEN_LIMITS.copy()


def is_model_supported(model_id: str) -> bool:
    """
    Check if a model ID is explicitly registered.

    Args:
        model_id: The model identifier to check

    Returns:
        True if model is in registry, False otherwise.

    Example:
        >>> is_model_supported("github-copilot/claude-sonnet-4")
        True
        >>> is_model_supported("unknown-model")
        False
    """
    return model_id in MODEL_TOKEN_LIMITS
