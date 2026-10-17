import unittest
from unittest.mock import patch

import pandas as pd
from fastapi import HTTPException
from yfinance.exceptions import YFRateLimitError

from yfinance_wrapper.full_history import get_full_history, reserve_request, serialize_history


def frame():
    return pd.DataFrame({
        "Open": [100.0, 101.0], "High": [110.0, 111.0],
        "Low": [90.0, 91.0], "Close": [105.0, 106.0],
        "Adj Close": [104.0, 105.0], "Volume": [1000, 2000],
        "Dividends": [0.2, 0.0], "Stock Splits": [0.0, 4.0],
    }, index=pd.date_range("2020-08-28", periods=2, tz="America/New_York"))


class TestFullHistory(unittest.TestCase):
    def test_serializes_all_actions_and_declares_actual_source_basis(self):
        result = serialize_history("AAPL", frame())
        self.assertEqual(result["price_basis"], "yahoo_split_adjusted")
        self.assertEqual(result["rows"][0]["dividend"], "0.2")
        self.assertEqual(result["rows"][1]["split_ratio"], "4.0")
        self.assertEqual(result["rows"][0]["volume"], 1000)
        self.assertEqual(result["rows"][0]["capital_gain"], "0")
        self.assertEqual(result["exchange_timezone"], "America/New_York")

    @patch("yfinance_wrapper.full_history.yf.Ticker")
    @patch("yfinance_wrapper.full_history.reserve_request")
    def test_fetches_once_with_explicit_unadjusted_flags(self, reserve, ticker):
        ticker.return_value.history.return_value = frame()
        get_full_history(" aapl ")
        ticker.assert_called_once_with("AAPL")
        ticker.return_value.history.assert_called_once_with(
            period="max", interval="1d", auto_adjust=False, back_adjust=False,
            actions=True, repair=False, keepna=True, rounding=False,
            raise_errors=True, timeout=60,
        )

    @patch("yfinance_wrapper.full_history.reserve_request")
    @patch("yfinance_wrapper.full_history.yf.Ticker")
    def test_invalid_input_does_not_reserve_or_fetch(self, ticker, reserve):
        with self.assertRaises(HTTPException) as ctx:
            get_full_history("BAD!")
        self.assertEqual(ctx.exception.status_code, 422)
        ticker.assert_not_called()
        reserve.assert_not_called()

    @patch("yfinance_wrapper.full_history.rate_limit_cooldown")
    @patch("yfinance_wrapper.full_history.reserve_request")
    @patch("yfinance_wrapper.full_history.yf.Ticker")
    def test_upstream_rate_limit_is_not_hidden_as_502(self, ticker, reserve, cooldown):
        ticker.return_value.history.side_effect = YFRateLimitError()
        with self.assertRaises(HTTPException) as ctx:
            get_full_history("AAPL")
        self.assertEqual(ctx.exception.status_code, 429)
        self.assertEqual(ctx.exception.headers["Retry-After"], "900")
        cooldown.assert_called_once()

    @patch("yfinance_wrapper.full_history._next_request", 100.0)
    @patch("yfinance_wrapper.full_history.time.monotonic", return_value=99.1)
    def test_gate_returns_retry_after_without_network_work(self, clock):
        with self.assertRaises(HTTPException) as ctx:
            reserve_request()
        self.assertEqual(ctx.exception.status_code, 429)
        self.assertEqual(ctx.exception.headers["Retry-After"], "1")

    def test_missing_action_columns_are_not_silently_zeroed(self):
        with self.assertRaises(ValueError):
            serialize_history("AAPL", frame().drop(columns=["Stock Splits"]))
