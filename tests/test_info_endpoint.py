"""Async endpoint tests for /info upstream handling.

These tests patch yfinance_wrapper.api.yf.Ticker so no network access
occurs. They verify that upstream failures surface as HTTP 502, that
missing or unidentifying info surfaces as HTTP 404, that invalid
tickers return HTTP 422 without any upstream call, and that a
successful fetch returns the info dict unchanged.
"""

import unittest
from unittest.mock import PropertyMock, patch

from fastapi import HTTPException

from yfinance_wrapper.api import get_info


class TestInfoEndpoint(unittest.IsolatedAsyncioTestCase):
    """Cover success, 502, 404, and 422 paths of GET /info."""

    @patch("yfinance_wrapper.api.yf.Ticker")
    async def test_successful_info_passthrough(self, mock_ticker):
        payload = {"symbol": "AAPL", "regularMarketPrice": 150.0}
        mock_ticker.return_value.info = payload

        result = await get_info(ticker_name="aapl")

        self.assertEqual(result, payload)
        mock_ticker.assert_called_once_with("AAPL")

    @patch("yfinance_wrapper.api.yf.Ticker")
    async def test_upstream_exception_returns_502(self, mock_ticker):
        type(mock_ticker.return_value).info = PropertyMock(
            side_effect=Exception("boom")
        )

        with self.assertRaises(HTTPException) as ctx:
            await get_info(ticker_name="AAPL")

        self.assertEqual(ctx.exception.status_code, 502)
        self.assertEqual(ctx.exception.detail, "Upstream error")

    @patch("yfinance_wrapper.api.yf.Ticker")
    async def test_ticker_construction_exception_returns_502(self, mock_ticker):
        mock_ticker.side_effect = Exception("boom")

        with self.assertRaises(HTTPException) as ctx:
            await get_info(ticker_name="AAPL")

        self.assertEqual(ctx.exception.status_code, 502)
        self.assertEqual(ctx.exception.detail, "Upstream error")

    @patch("yfinance_wrapper.api.yf.Ticker")
    async def test_none_info_returns_404(self, mock_ticker):
        mock_ticker.return_value.info = None

        with self.assertRaises(HTTPException) as ctx:
            await get_info(ticker_name="AAPL")

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "Ticker Not Found")

    @patch("yfinance_wrapper.api.yf.Ticker")
    async def test_empty_info_returns_404(self, mock_ticker):
        mock_ticker.return_value.info = {}

        with self.assertRaises(HTTPException) as ctx:
            await get_info(ticker_name="AAPL")

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "Ticker Not Found")

    @patch("yfinance_wrapper.api.yf.Ticker")
    async def test_unidentifying_info_returns_404(self, mock_ticker):
        mock_ticker.return_value.info = {"foo": "bar"}

        with self.assertRaises(HTTPException) as ctx:
            await get_info(ticker_name="AAPL")

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "Ticker Not Found")

    @patch("yfinance_wrapper.api.yf.Ticker")
    async def test_invalid_ticker_returns_422_and_no_ticker_call(
        self, mock_ticker
    ):
        with self.assertRaises(HTTPException) as ctx:
            await get_info(ticker_name="BAD!")

        self.assertEqual(ctx.exception.status_code, 422)
        mock_ticker.assert_not_called()


if __name__ == "__main__":
    unittest.main()
