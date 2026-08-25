"""Pure validation for yfinance history periods.

This module has no side effects and requires no network access.
"""

VALID_PERIODS = frozenset(
    {
        "1d",
        "5d",
        "1mo",
        "3mo",
        "6mo",
        "1y",
        "2y",
        "5y",
        "10y",
        "ytd",
        "max",
    }
)


class HistoryPeriodError(ValueError):
    """Raised when an invalid or malformed history period is supplied."""

    pass


def validate_history_period(period: str) -> str:
    """Normalize and validate a yfinance history period string.

    Rules:
    - Strip leading/trailing whitespace.
    - Convert to lowercase.
    - Reject empty strings.
    - Must be one of the supported yfinance period values.

    Raises:
        HistoryPeriodError: If the period is invalid or unsupported.

    Returns:
        The normalized (lowercased) period string.
    """
    if period is None:
        raise HistoryPeriodError("Period is required")
    cleaned = period.strip().lower()
    if not cleaned:
        raise HistoryPeriodError("Period cannot be empty")
    if cleaned not in VALID_PERIODS:
        raise HistoryPeriodError(
            f"Invalid period '{period}'. Supported periods: {', '.join(sorted(VALID_PERIODS))}"
        )
    return cleaned
