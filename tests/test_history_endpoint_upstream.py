"""Async endpoint tests for /history upstream error handling.

These tests patch yfinance_wrapper.api.yf.Ticker so no network access
occurs, and verify that upstream failures surface as HTTP 502 while
missing data surfaces as HTTP 404.
"""

import unittest
from datetime import date
from unittest.mock import patch

import pandas as pd
from fastapi import HTTPException

from yfinance_wrapper.api import get_history


def frame() -> pd.DataFrame:
    return pd.DataFrame(
        {"Close": [100.0, 101.5]},
        index=pd.to_datetime(["2023-01-02", "2023-01-03"]),
    )


class TestHistoryEndpointUpstream(unittest.IsolatedAsyncioTestCase):
    """Assert 502/404 responses and history() call passthrough."""

    @patch("yfinance_wrapper.api.yf.Ticker")
    async def test_period_passthrough(self, mock_ticker):
        data = frame()
        mock_ticker.return_value.history.return_value = data

        response = await get_history(ticker_name="AAPL", period="1y")

        mock_ticker.return_value.history.assert_called_once_with(period="1y")
        self.assertEqual(response, data.to_dict())

    @patch("yfinance_wrapper.api.yf.Ticker")
    async def test_start_end_passthrough(self, mock_ticker):
        data = frame()
        mock_ticker.return_value.history.return_value = data

        response = await get_history(
            ticker_name="AAPL",
            start=date(2023, 1, 1),
            end=date(2023, 12, 31),
        )

        mock_ticker.return_value.history.assert_called_once_with(
            start="2023-01-01", end="2023-12-31"
        )
        self.assertEqual(response, data.to_dict())

    @patch("yfinance_wrapper.api.yf.Ticker")
    async def test_history_exception_returns_502(self, mock_ticker):
        mock_ticker.return_value.history.side_effect = Exception("boom")

        with self.assertRaises(HTTPException) as ctx:
            await get_history(ticker_name="AAPL", period="1y")

        self.assertEqual(ctx.exception.status_code, 502)
        self.assertEqual(ctx.exception.detail, "Upstream error")

    @patch("yfinance_wrapper.api.yf.Ticker")
    async def test_ticker_construction_exception_returns_502(self, mock_ticker):
        mock_ticker.side_effect = Exception("boom")

        with self.assertRaises(HTTPException) as ctx:
            await get_history(ticker_name="AAPL", period="1y")

        self.assertEqual(ctx.exception.status_code, 502)
        self.assertEqual(ctx.exception.detail, "Upstream error")

    @patch("yfinance_wrapper.api.yf.Ticker")
    async def test_none_history_returns_404(self, mock_ticker):
        mock_ticker.return_value.history.return_value = None

        with self.assertRaises(HTTPException) as ctx:
            await get_history(ticker_name="AAPL", period="1y")

        self.assertEqual(ctx.exception.status_code, 404)

    @patch("yfinance_wrapper.api.yf.Ticker")
    async def test_empty_history_returns_404(self, mock_ticker):
        mock_ticker.return_value.history.return_value = pd.DataFrame()

        with self.assertRaises(HTTPException) as ctx:
            await get_history(ticker_name="AAPL", period="1y")

        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
