"""Async endpoint tests for /history input validation.

These tests use unittest.mock to verify that yf.Ticker is never
instantiated when any validation step fails, and that each failure
returns HTTP 422.
"""

import unittest
from datetime import date
from unittest.mock import patch

from fastapi import HTTPException

from yfinance_wrapper.api import get_history


class TestHistoryEndpointValidation(unittest.IsolatedAsyncioTestCase):
    """Assert 422 responses and no yf.Ticker calls for invalid inputs."""

    @patch("yfinance_wrapper.api.yf.Ticker")
    async def test_invalid_ticker_returns_422_and_no_ticker_call(self, mock_ticker):
        with self.assertRaises(HTTPException) as ctx:
            await get_history(ticker_name="AAPL!")
        self.assertEqual(ctx.exception.status_code, 422)
        mock_ticker.assert_not_called()

    @patch("yfinance_wrapper.api.yf.Ticker")
    async def test_invalid_period_returns_422_and_no_ticker_call(self, mock_ticker):
        with self.assertRaises(HTTPException) as ctx:
            await get_history(ticker_name="AAPL", period="invalid")
        self.assertEqual(ctx.exception.status_code, 422)
        mock_ticker.assert_not_called()

    @patch("yfinance_wrapper.api.yf.Ticker")
    async def test_period_and_dates_conflict_returns_422_and_no_ticker_call(
        self, mock_ticker
    ):
        with self.assertRaises(HTTPException) as ctx:
            await get_history(
                ticker_name="AAPL",
                period="1y",
                start=date(2023, 1, 1),
                end=date(2023, 12, 31),
            )
        self.assertEqual(ctx.exception.status_code, 422)
        mock_ticker.assert_not_called()

    @patch("yfinance_wrapper.api.yf.Ticker")
    async def test_invalid_date_range_returns_422_and_no_ticker_call(
        self, mock_ticker
    ):
        # start after end
        with self.assertRaises(HTTPException) as ctx:
            await get_history(
                ticker_name="AAPL",
                start=date(2023, 12, 31),
                end=date(2023, 1, 1),
            )
        self.assertEqual(ctx.exception.status_code, 422)
        mock_ticker.assert_not_called()


if __name__ == "__main__":
    unittest.main()
