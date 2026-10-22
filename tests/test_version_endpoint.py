"""Async endpoint tests for GET /version.

These tests call the handler directly and patch
yfinance_wrapper.api.version plus os.environ, so no network access
occurs. They verify that the response has exactly the keys "version"
and "build", that the values match those returned by /healthz under
the same patched environment, and that the "unknown" fallbacks apply
when package metadata is missing or the build environment variables
are unset or empty.
"""

import os
import unittest
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

from yfinance_wrapper.api import healthz, version_info


class TestVersionEndpoint(unittest.IsolatedAsyncioTestCase):
    """Cover the /version response shape and fallback behavior."""

    async def test_response_has_exactly_version_and_build_keys(self):
        result = await version_info()

        self.assertEqual(set(result.keys()), {"version", "build"})

    async def test_values_match_healthz_under_same_environment(self):
        env = {
            "YFINANCE_WRAPPER_BUILD_REVISION": "abc123",
            "YFINANCE_WRAPPER_IMAGE_DIGEST": "sha256:deadbeef",
        }
        with patch("yfinance_wrapper.api.version", return_value="1.2.3"):
            with patch.dict(os.environ, env):
                version_result = await version_info()
                healthz_result = await healthz()

        self.assertEqual(version_result["version"], healthz_result["version"])
        self.assertEqual(version_result["build"], healthz_result["build"])

    async def test_version_from_package_metadata(self):
        with patch("yfinance_wrapper.api.version", return_value="1.2.3"):
            result = await version_info()

        self.assertEqual(result["version"], "1.2.3")

    async def test_version_unknown_when_package_not_found(self):
        with patch(
            "yfinance_wrapper.api.version",
            side_effect=PackageNotFoundError("yfinance_wrapper"),
        ):
            result = await version_info()

        self.assertEqual(result["version"], "unknown")

    async def test_build_fields_from_environment(self):
        env = {
            "YFINANCE_WRAPPER_BUILD_REVISION": "abc123",
            "YFINANCE_WRAPPER_IMAGE_DIGEST": "sha256:deadbeef",
        }
        with patch.dict(os.environ, env):
            result = await version_info()

        self.assertEqual(result["build"]["revision"], "abc123")
        self.assertEqual(result["build"]["image_digest"], "sha256:deadbeef")

    async def test_build_fields_unknown_when_unset(self):
        env = os.environ.copy()
        env.pop("YFINANCE_WRAPPER_BUILD_REVISION", None)
        env.pop("YFINANCE_WRAPPER_IMAGE_DIGEST", None)
        with patch.dict(os.environ, env, clear=True):
            result = await version_info()

        self.assertEqual(result["build"]["revision"], "unknown")
        self.assertEqual(result["build"]["image_digest"], "unknown")

    async def test_build_fields_unknown_when_empty(self):
        env = {
            "YFINANCE_WRAPPER_BUILD_REVISION": "",
            "YFINANCE_WRAPPER_IMAGE_DIGEST": "",
        }
        with patch.dict(os.environ, env):
            result = await version_info()

        self.assertEqual(result["build"]["revision"], "unknown")
        self.assertEqual(result["build"]["image_digest"], "unknown")


if __name__ == "__main__":
    unittest.main()
