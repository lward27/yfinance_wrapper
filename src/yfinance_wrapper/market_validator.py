"""Pure, case-insensitive validator for yfinance Market keys.

Uses only the Python standard library.
"""

SUPPORTED_MARKETS = frozenset(
    {
        "US",
        "GB",
        "ASIA",
        "EUROPE",
        "RATES",
        "COMMODITIES",
        "CURRENCIES",
        "CRYPTOCURRENCIES",
    }
)


class MarketValidationError(ValueError):
    """Raised when a market name is invalid, empty, or missing."""

    pass


def validate_market(name: str) -> str:
    """Return the canonical upper-case market key if *name* is supported.

    The comparison is case-insensitive and surrounding whitespace is
    stripped.  On any failure a :class:`MarketValidationError` is raised
    so that the caller can translate it into an HTTP 422 response.

    Parameters
    ----------
    name:
        The raw market identifier (e.g. ``"us"``, ``"EUROPE"``).

    Returns
    -------
    str
        The canonical upper-case key (e.g. ``"US"``).

    Raises
    ------
    MarketValidationError
        If *name* is ``None``, empty, whitespace-only, or not one of the
        supported market keys.
    """
    if name is None:
        raise MarketValidationError("Market name is required.")

    if not isinstance(name, str):
        # Coerce to string for basic compatibility, then strip.
        name = str(name)

    cleaned = name.strip()
    if cleaned == "":
        raise MarketValidationError("Market name cannot be empty.")

    upper = cleaned.upper()
    if upper not in SUPPORTED_MARKETS:
        supported = ", ".join(sorted(SUPPORTED_MARKETS))
        raise MarketValidationError(
            f"Unsupported market '{cleaned}'. Supported markets: {supported}."
        )

    return upper
