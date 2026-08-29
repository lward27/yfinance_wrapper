"""Async endpoint tests for GET /markets/{market_name}.

These tests use unittest.mock to verify that yf.Market is never
instantiated when validation fails, and that upstream exceptions
are sanitized as HTTP 502 without leaking internal details.
"""

import unittest
from unittest.mock import patch, MagicMock

from fastapi import HTTPException

from yfinance_wrapper.api import get_market


class TestMarketEndpoint(unittest.IsolatedAsyncioTestCase):
    """Assert 422/502 responses and correct JSON envelope for /markets."""

    @patch("yfinance_wrapper.api.yf.Market")
    async def test_valid_canonical_market_returns_envelope(self, mock_market_cls):
        mock_market = MagicMock()
        mock_market.summary = {"key": "value"}
        mock_market.status = {"open": True}
        mock_market_cls.return_value = mock_market

        result = await get_market(market_name="US")

        self.assertEqual(result["market"], "US")
        self.assertEqual(result["summary"], {"key": "value"})
        self.assertEqual(result["status"], {"open": True})
        mock_market_cls.assert_called_once_with("US")

    @patch("yfinance_wrapper.api.yf.Market")
    async def test_valid_lowercase_market_returns_envelope(self, mock_market_cls):
        mock_market = MagicMock()
        mock_market.summary = {"key": "value"}
        mock_market.status = None
        mock_market_cls.return_value = mock_market

        result = await get_market(market_name="gb")

        self.assertEqual(result["market"], "GB")
        self.assertEqual(result["summary"], {"key": "value"})
        self.assertIsNone(result["status"])
        mock_market_cls.assert_called_once_with("GB")

    @patch("yfinance_wrapper.api.yf.Market")
    async def test_valid_mixed_case_market_returns_envelope(self, mock_market_cls):
        mock_market = MagicMock()
        mock_market.summary = {"key": "value"}
        mock_market.status = None
        mock_market_cls.return_value = mock_market

        result = await get_market(market_name="AsIa")

        self.assertEqual(result["market"], "ASIA")
        self.assertEqual(result["summary"], {"key": "value"})
        self.assertIsNone(result["status"])
        mock_market_cls.assert_called_once_with("ASIA")

    @patch("yfinance_wrapper.api.yf.Market")
    async def test_invalid_market_returns_422_and_no_market_call(self, mock_market_cls):
        with self.assertRaises(HTTPException) as ctx:
            await get_market(market_name="INVALID")
        self.assertEqual(ctx.exception.status_code, 422)
        mock_market_cls.assert_not_called()

    @patch("yfinance_wrapper.api.yf.Market")
    async def test_empty_market_returns_422_and_no_market_call(self, mock_market_cls):
        with self.assertRaises(HTTPException) as ctx:
            await get_market(market_name="")
        self.assertEqual(ctx.exception.status_code, 422)
        mock_market_cls.assert_not_called()

    @patch("yfinance_wrapper.api.yf.Market")
    async def test_upstream_exception_returns_502(self, mock_market_cls):
        mock_market_cls.side_effect = RuntimeError("network failure")

        with self.assertRaises(HTTPException) as ctx:
            await get_market(market_name="US")
        self.assertEqual(ctx.exception.status_code, 502)
        self.assertEqual(ctx.exception.detail, "Upstream error")

    @patch("yfinance_wrapper.api.yf.Market")
    async def test_all_supported_markets_accepted(self, mock_market_cls):
        from yfinance_wrapper.market_validator import SUPPORTED_MARKETS

        for market in SUPPORTED_MARKETS:
            with self.subTest(market=market):
                mock_market = MagicMock()
                mock_market.summary = {}
                mock_market.status = None
                mock_market_cls.return_value = mock_market
                mock_market_cls.reset_mock()

                result = await get_market(market_name=market)

                self.assertEqual(result["market"], market)
                mock_market_cls.assert_called_once_with(market)


if __name__ == "__main__":
    unittest.main()
