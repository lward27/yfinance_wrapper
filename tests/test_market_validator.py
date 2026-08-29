"""Standard-library unit tests for yfinance_wrapper.market_validator."""

import unittest

from yfinance_wrapper.market_validator import (
    validate_market,
    MarketValidationError,
    SUPPORTED_MARKETS,
)


class TestValidateMarket(unittest.TestCase):
    def test_all_canonical_keys_accepted(self):
        for market in SUPPORTED_MARKETS:
            with self.subTest(market=market):
                self.assertEqual(validate_market(market), market)

    def test_lowercase_accepted(self):
        self.assertEqual(validate_market("us"), "US")
        self.assertEqual(validate_market("gb"), "GB")
        self.assertEqual(validate_market("asia"), "ASIA")
        self.assertEqual(validate_market("europe"), "EUROPE")
        self.assertEqual(validate_market("rates"), "RATES")
        self.assertEqual(validate_market("commodities"), "COMMODITIES")
        self.assertEqual(validate_market("currencies"), "CURRENCIES")
        self.assertEqual(validate_market("cryptocurrencies"), "CRYPTOCURRENCIES")

    def test_mixed_case_accepted(self):
        self.assertEqual(validate_market("Us"), "US")
        self.assertEqual(validate_market("gB"), "GB")
        self.assertEqual(validate_market("AsIa"), "ASIA")
        self.assertEqual(validate_market("EuRoPe"), "EUROPE")

    def test_strips_whitespace(self):
        self.assertEqual(validate_market("  US  "), "US")
        self.assertEqual(validate_market("\tgb\n"), "GB")

    def test_rejects_none(self):
        with self.assertRaises(MarketValidationError) as ctx:
            validate_market(None)
        self.assertIn("required", str(ctx.exception).lower())

    def test_rejects_empty(self):
        with self.assertRaises(MarketValidationError) as ctx:
            validate_market("")
        self.assertIn("empty", str(ctx.exception).lower())

    def test_rejects_whitespace_only(self):
        with self.assertRaises(MarketValidationError) as ctx:
            validate_market("   ")
        self.assertIn("empty", str(ctx.exception).lower())

    def test_rejects_invalid_market(self):
        with self.assertRaises(MarketValidationError) as ctx:
            validate_market("INVALID")
        self.assertIn("unsupported", str(ctx.exception).lower())

    def test_rejects_partial_match(self):
        with self.assertRaises(MarketValidationError) as ctx:
            validate_market("US_MARKET")
        self.assertIn("unsupported", str(ctx.exception).lower())

    def test_error_includes_supported_list(self):
        with self.assertRaises(MarketValidationError) as ctx:
            validate_market("FOO")
        msg = str(ctx.exception)
        self.assertIn("FOO", msg)
        for market in SUPPORTED_MARKETS:
            self.assertIn(market, msg)


if __name__ == "__main__":
    unittest.main()
