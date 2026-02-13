"""
Token counting and validation utilities for ADWS.

Provides token counting using tiktoken (Claude-compatible encoding)
and safety margin calculations to prevent API token limit errors.
"""

import tiktoken
from typing import Optional


# Default encoding for Claude models (cl100k_base is compatible)
DEFAULT_ENCODING = "cl100k_base"

# Safety margin: Use 95% of actual limit to account for system messages
SAFETY_MARGIN = 0.95


def count_tokens(text: str, encoding_name: str = DEFAULT_ENCODING) -> int:
    """
    Count tokens in text using tiktoken.

    Args:
        text: The text to count tokens for
        encoding_name: The tiktoken encoding to use (default: cl100k_base)

    Returns:
        Number of tokens in the text

    Examples:
        >>> count_tokens("Hello world")
        2
        >>> count_tokens("This is a longer message with more tokens")
        8
    """
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception as e:
        # Fallback: rough estimate if tiktoken fails
        # Average ~4 characters per token for English text
        return len(text) // 4


def get_safe_token_limit(model_limit: int) -> int:
    """
    Calculate safe token limit with margin.

    Args:
        model_limit: The model's actual token limit

    Returns:
        Safe limit (95% of actual limit)

    Examples:
        >>> get_safe_token_limit(128000)
        121600
        >>> get_safe_token_limit(200000)
        190000
    """
    return int(model_limit * SAFETY_MARGIN)


def check_token_limit(
    text: str, model_limit: int, encoding_name: str = DEFAULT_ENCODING
) -> tuple[bool, int, int]:
    """
    Check if text exceeds safe token limit for model.

    Args:
        text: The text to check
        model_limit: The model's token limit
        encoding_name: The tiktoken encoding to use

    Returns:
        Tuple of (within_limit, token_count, safe_limit)
        - within_limit: True if tokens <= safe limit
        - token_count: Actual token count
        - safe_limit: Safe token limit (with margin)

    Examples:
        >>> text = "Hello world"
        >>> within, count, limit = check_token_limit(text, 128000)
        >>> within
        True
        >>> count < limit
        True
    """
    token_count = count_tokens(text, encoding_name)
    safe_limit = get_safe_token_limit(model_limit)
    within_limit = token_count <= safe_limit

    return within_limit, token_count, safe_limit


def calculate_overage_percentage(token_count: int, model_limit: int) -> float:
    """
    Calculate percentage over limit.

    Args:
        token_count: Actual token count
        model_limit: Model's token limit

    Returns:
        Percentage over limit (e.g., 43.75 means 43.75% over)

    Examples:
        >>> calculate_overage_percentage(184000, 128000)
        43.75
        >>> calculate_overage_percentage(100000, 128000)
        -21.875
    """
    return ((token_count - model_limit) / model_limit) * 100


def estimate_tokens_for_text(text: str) -> int:
    """
    Quick token estimate without loading encoding.

    Uses simple heuristic: ~4 chars per token for English.
    Less accurate but faster than count_tokens().

    Args:
        text: The text to estimate

    Returns:
        Estimated token count
    """
    return len(text) // 4


def format_token_summary(
    token_count: int, model_limit: int, safe_limit: Optional[int] = None
) -> str:
    """
    Format human-readable token usage summary.

    Args:
        token_count: Current token count
        model_limit: Model's maximum limit
        safe_limit: Safe limit (optional, will calculate if not provided)

    Returns:
        Formatted summary string

    Examples:
        >>> format_token_summary(100000, 128000)
        '100,000 tokens (78.1% of 128,000 limit, within safe margin)'
    """
    if safe_limit is None:
        safe_limit = get_safe_token_limit(model_limit)

    percentage = (token_count / model_limit) * 100

    if token_count <= safe_limit:
        status = "within safe margin"
    elif token_count <= model_limit:
        status = "exceeds safe margin"
    else:
        overage = calculate_overage_percentage(token_count, model_limit)
        status = f"EXCEEDS LIMIT by {overage:.1f}%"

    return (
        f"{token_count:,} tokens ({percentage:.1f}% of {model_limit:,} limit, {status})"
    )
