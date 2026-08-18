"""Pure validation utilities for ticker normalization and date ranges.

These functions have no side effects and require no network access,
making them easy to test with the standard library.
"""

from datetime import date, timedelta
from typing import Optional, Tuple


def normalize_ticker(ticker: Optional[str]) -> str:
    """Normalize a ticker string.

    Rules:
    - Strip leading/trailing whitespace.
    - Convert to uppercase.
    - Reject empty or None values.
    - Reject strings longer than 20 characters.
    - Allow alphanumeric, dots, hyphens, and equals (common in Yahoo Finance).

    Raises:
        ValueError: If the ticker is invalid.
    """
    if ticker is None:
        raise ValueError("Ticker is required")
    cleaned = ticker.strip().upper()
    if not cleaned:
        raise ValueError("Ticker cannot be empty")
    if len(cleaned) > 20:
        raise ValueError("Ticker too long (max 20 characters)")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-=")
    if not all(ch in allowed for ch in cleaned):
        raise ValueError("Ticker contains invalid characters")
    return cleaned


def validate_date_range(
    start: Optional[date],
    end: Optional[date],
    *,
    allow_future: bool = False,
) -> Tuple[date, date]:
    """Validate and return a normalized date range.

    Rules:
    - Both start and end must be provided together (or both omitted).
    - start must not be after end.
    - By default, neither date may be in the future.

    Returns:
        A (start, end) tuple.

    Raises:
        ValueError: If the date range is invalid.
    """
    if (start is None) != (end is None):
        raise ValueError("Both start and end dates are required together")

    if start is None and end is None:
        # Return a sensible default when both are omitted.
        today = date.today()
        default_start = today - timedelta(days=365)
        return (default_start, today)

    assert start is not None and end is not None

    if start > end:
        raise ValueError("Start date cannot be after end date")

    if not allow_future:
        today = date.today()
        if start > today:
            raise ValueError("Start date cannot be in the future")
        if end > today:
            raise ValueError("End date cannot be in the future")

    return (start, end)
