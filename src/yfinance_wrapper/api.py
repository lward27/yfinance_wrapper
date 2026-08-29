from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import date

import yfinance as yf

from yfinance_wrapper.validation import normalize_ticker, validate_date_range
from yfinance_wrapper.history_period_validator import (
    validate_history_period,
    HistoryPeriodError,
)
from yfinance_wrapper.market_validator import (
    validate_market,
    MarketValidationError,
)

app = FastAPI()

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _validation_error_response(detail: str) -> HTTPException:
    return HTTPException(status_code=422, detail=detail)


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/info")
async def get_info(ticker_name: str):
    try:
        normalized = normalize_ticker(ticker_name)
    except ValueError as exc:
        raise _validation_error_response(str(exc))
    tick = yf.Ticker(normalized)
    return tick.info


@app.get("/history")
async def get_history(
    ticker_name: str,
    period: Optional[str] = None,
    start: Optional[date] = None,
    end: Optional[date] = None,
):
    # 1. Validate ticker first
    try:
        normalized = normalize_ticker(ticker_name)
    except ValueError as exc:
        raise _validation_error_response(str(exc))

    # 2. Validate period/date mutual exclusion and period value
    has_period = period is not None
    has_dates = start is not None or end is not None

    if has_period and has_dates:
        raise _validation_error_response(
            "Period and explicit start/end dates are mutually exclusive. Provide one or the other."
        )

    if has_period:
        try:
            validated_period = validate_history_period(period)
        except HistoryPeriodError as exc:
            raise _validation_error_response(str(exc))
    else:
        validated_period = None

    # 3. Validate date range when dates are provided
    if has_dates:
        try:
            validated_start, validated_end = validate_date_range(start, end)
        except ValueError as exc:
            raise _validation_error_response(str(exc))
    else:
        validated_start = None
        validated_end = None

    # 4. Only after all validation passes, construct the upstream ticker
    tick = yf.Ticker(normalized)
    try:
        if validated_start is not None and validated_end is not None:
            hist = tick.history(start=str(validated_start), end=str(validated_end))
        else:
            hist = tick.history(period=validated_period or "max")
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream error")
    if hist is None or hist.empty:
        raise HTTPException(status_code=404, detail="Ticker Not Found")
    return hist.to_dict()


@app.get("/markets/{market_name}")
async def get_market(market_name: str):
    # 1. Validate market name before any upstream call
    try:
        canonical = validate_market(market_name)
    except MarketValidationError as exc:
        raise _validation_error_response(str(exc))

    # 2. Only after validation passes, construct the upstream Market
    try:
        market = yf.Market(canonical)
        summary = market.summary
        status = market.status
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream error")

    return {
        "market": canonical,
        "summary": summary,
        "status": status,
    }
