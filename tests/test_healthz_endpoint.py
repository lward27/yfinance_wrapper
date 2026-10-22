"""Async endpoint tests for GET /healthz.

These tests call the handler directly and patch
yfinance_wrapper.api.version plus os.environ, so no network access
occurs. They verify that the pre-existing "status" field is preserved,
that "version" reflects importlib.metadata.version (with an "unknown"
fallback when package metadata is missing), and that the "build"
object reflects the YFINANCE_WRAPPER_BUILD_REVISION and
YFINANCE_WRAPPER_IMAGE_DIGEST environment variables (each falling back
to "unknown" when unset).
"""

import os
import unittest
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

from yfinance_wrapper.api import healthz


class TestHealthzEndpoint(unittest.IsolatedAsyncioTestCase):
    """Cover the /healthz response shape and fallback behavior."""

    async def test_preserves_existing_status_field(self):
        result = await healthz()

        self.assertEqual(result["status"], "ok")

    async def test_version_from_package_metadata(self):
        with patch("yfinance_wrapper.api.version", return_value="1.2.3"):
            result = await healthz()

        self.assertEqual(result["version"], "1.2.3")

    async def test_version_unknown_when_package_not_found(self):
        with patch(
            "yfinance_wrapper.api.version",
            side_effect=PackageNotFoundError("yfinance_wrapper"),
        ):
            result = await healthz()

        self.assertEqual(result["version"], "unknown")

    async def test_build_fields_from_environment(self):
        env = {
            "YFINANCE_WRAPPER_BUILD_REVISION": "abc123",
            "YFINANCE_WRAPPER_IMAGE_DIGEST": "sha256:deadbeef",
        }
        with patch.dict(os.environ, env):
            result = await healthz()

        self.assertEqual(result["build"]["revision"], "abc123")
        self.assertEqual(result["build"]["image_digest"], "sha256:deadbeef")

    async def test_build_fields_unknown_when_unset(self):
        env = os.environ.copy()
        env.pop("YFINANCE_WRAPPER_BUILD_REVISION", None)
        env.pop("YFINANCE_WRAPPER_IMAGE_DIGEST", None)
        with patch.dict(os.environ, env, clear=True):
            result = await healthz()

        self.assertEqual(result["build"]["revision"], "unknown")
        self.assertEqual(result["build"]["image_digest"], "unknown")

    async def test_build_fields_unknown_when_empty(self):
        env = {
            "YFINANCE_WRAPPER_BUILD_REVISION": "",
            "YFINANCE_WRAPPER_IMAGE_DIGEST": "",
        }
        with patch.dict(os.environ, env):
            result = await healthz()

        self.assertEqual(result["build"]["revision"], "unknown")
        self.assertEqual(result["build"]["image_digest"], "unknown")


if __name__ == "__main__":
    unittest.main()
