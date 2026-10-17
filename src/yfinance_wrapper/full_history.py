"""Explicit, lossless history export for the slow corporate-action backfill."""

import math
import threading
import time
from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd
import yfinance as yf
from fastapi import APIRouter, HTTPException
from yfinance.exceptions import YFPricesMissingError, YFRateLimitError, YFTzMissingError

from yfinance_wrapper.validation import normalize_ticker

router = APIRouter()
_lock = threading.Lock()
_next_request = 0.0


def reserve_request():
    """Bound this expensive endpoint without delaying ordinary history reads."""
    global _next_request
    with _lock:
        now = time.monotonic()
        if now < _next_request:
            raise HTTPException(
                429, "Full-history export is cooling down",
                headers={"Retry-After": str(math.ceil(_next_request - now))},
            )
        _next_request = now + 60


def rate_limit_cooldown():
    global _next_request
    with _lock:
        _next_request = max(_next_request, time.monotonic() + 900)


def number(value):
    if value is None or pd.isna(value):
        return None
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("Non-finite history value")
    return str(result)


def serialize_history(ticker, frame):
    required = {"Open", "High", "Low", "Close", "Adj Close", "Volume",
                "Dividends", "Stock Splits"}
    if not required.issubset(frame.columns) or frame.index.tz is None:
        raise ValueError("Incomplete upstream history schema")
    rows = []
    for ts, row in frame.sort_index().iterrows():
        volume = number(row["Volume"])
        if volume is not None and (
            Decimal(volume) < 0 or Decimal(volume) != int(Decimal(volume))
        ):
            raise ValueError("Invalid volume")
        rows.append({
            "date": ts.date().isoformat(),
            "open": number(row["Open"]), "high": number(row["High"]),
            "low": number(row["Low"]), "close": number(row["Close"]),
            "adjusted_close": number(row["Adj Close"]),
            "volume": None if volume is None else int(Decimal(volume)),
            "dividend": number(row["Dividends"]),
            "split_ratio": number(row["Stock Splits"]),
            "capital_gain": number(row.get("Capital Gains", 0)),
        })
    return {
        "schema_version": 1, "ticker": ticker, "source": "yahoo_finance",
        "source_version": yf.__version__,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "price_basis": "yahoo_split_adjusted",
        "dividend_basis": "yahoo_split_adjusted",
        "exchange_timezone": str(frame.index.tz),
        "rows": rows,
    }


@router.get("/history/full")
def get_full_history(ticker_name: str):
    try:
        ticker = normalize_ticker(ticker_name)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    reserve_request()
    try:
        frame = yf.Ticker(ticker).history(
            period="max", interval="1d", auto_adjust=False, back_adjust=False,
            actions=True, repair=False, keepna=True, rounding=False,
            raise_errors=True, timeout=60,
        )
        if frame is None or frame.empty:
            raise HTTPException(404, "No history found")
        return serialize_history(ticker, frame)
    except YFRateLimitError:
        rate_limit_cooldown()
        raise HTTPException(
            429, "Yahoo Finance rate limit", headers={"Retry-After": "900"}
        )
    except (YFPricesMissingError, YFTzMissingError):
        raise HTTPException(404, "No history found")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(502, "Upstream history export failed")
