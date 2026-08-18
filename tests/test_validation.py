"""Standard-library unit tests for yfinance_wrapper.validation."""

import unittest
from datetime import date, timedelta

from yfinance_wrapper.validation import normalize_ticker, validate_date_range


class TestNormalizeTicker(unittest.TestCase):
    def test_uppercases(self):
        self.assertEqual(normalize_ticker("aapl"), "AAPL")

    def test_strips_whitespace(self):
        self.assertEqual(normalize_ticker("  MSFT  "), "MSFT")

    def test_rejects_none(self):
        with self.assertRaises(ValueError) as ctx:
            normalize_ticker(None)
        self.assertIn("required", str(ctx.exception).lower())

    def test_rejects_empty(self):
        with self.assertRaises(ValueError) as ctx:
            normalize_ticker("")
        self.assertIn("empty", str(ctx.exception).lower())

    def test_rejects_whitespace_only(self):
        with self.assertRaises(ValueError) as ctx:
            normalize_ticker("   ")
        self.assertIn("empty", str(ctx.exception).lower())

    def test_rejects_too_long(self):
        with self.assertRaises(ValueError) as ctx:
            normalize_ticker("A" * 21)
        self.assertIn("too long", str(ctx.exception).lower())

    def test_allows_dots_and_hyphens(self):
        self.assertEqual(normalize_ticker("BRK-B"), "BRK-B")
        self.assertEqual(normalize_ticker("VTSAX"), "VTSAX")

    def test_rejects_invalid_characters(self):
        with self.assertRaises(ValueError) as ctx:
            normalize_ticker("AAPL!")
        self.assertIn("invalid", str(ctx.exception).lower())


class TestValidateDateRange(unittest.TestCase):
    def test_both_none_returns_default(self):
        start, end = validate_date_range(None, None)
        self.assertIsInstance(start, date)
        self.assertIsInstance(end, date)
        self.assertLessEqual(start, end)
        # Default range is roughly one year
        self.assertEqual((end - start).days, 365)

    def test_valid_range(self):
        start = date(2023, 1, 1)
        end = date(2023, 12, 31)
        result = validate_date_range(start, end)
        self.assertEqual(result, (start, end))

    def test_start_after_end_raises(self):
        with self.assertRaises(ValueError) as ctx:
            validate_date_range(date(2023, 12, 31), date(2023, 1, 1))
        self.assertIn("after", str(ctx.exception).lower())

    def test_only_start_raises(self):
        with self.assertRaises(ValueError) as ctx:
            validate_date_range(date(2023, 1, 1), None)
        self.assertIn("both", str(ctx.exception).lower())

    def test_only_end_raises(self):
        with self.assertRaises(ValueError) as ctx:
            validate_date_range(None, date(2023, 1, 1))
        self.assertIn("both", str(ctx.exception).lower())

    def test_future_start_raises_by_default(self):
        future = date.today() + timedelta(days=1)
        with self.assertRaises(ValueError) as ctx:
            validate_date_range(future, future)
        self.assertIn("future", str(ctx.exception).lower())

    def test_future_end_raises_by_default(self):
        today = date.today()
        future = today + timedelta(days=1)
        with self.assertRaises(ValueError) as ctx:
            validate_date_range(today, future)
        self.assertIn("future", str(ctx.exception).lower())

    def test_future_allowed_when_flag_set(self):
        future = date.today() + timedelta(days=1)
        result = validate_date_range(future, future, allow_future=True)
        self.assertEqual(result, (future, future))


if __name__ == "__main__":
    unittest.main()
