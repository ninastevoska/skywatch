"""Unit tests for downloading PC-Axis datasets."""

import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from src.px_fetcher import (
    DATASET_URL,
    PXFetchError,
    fetch_px,
)


class TestPXFetcher(unittest.TestCase):
    """Verify successful downloads and HTTP error handling."""

    @patch("src.px_fetcher.urlopen")
    def test_successful_download(self, mock_urlopen):
        """Return raw bytes when the HTTP request succeeds."""
        content = b'CHARSET="ANSI";\nDATA=1 2 3;'

        response = MagicMock()
        response.status = 200
        response.read.return_value = content

        mock_urlopen.return_value.__enter__.return_value = response

        result = fetch_px()

        self.assertEqual(result, content)
        self.assertIsInstance(result, bytes)
        mock_urlopen.assert_called_once()

    @patch("src.px_fetcher.urlopen")
    def test_request_configuration(self, mock_urlopen):
        """Send the configured URL, user agent, and timeout."""
        response = MagicMock()
        response.status = 200
        response.read.return_value = b"PC-Axis content"

        mock_urlopen.return_value.__enter__.return_value = response

        fetch_px(timeout=15)

        args, kwargs = mock_urlopen.call_args
        request = args[0]

        self.assertEqual(request.full_url, DATASET_URL)
        self.assertEqual(kwargs["timeout"], 15)
        self.assertEqual(
            request.get_header("User-agent"),
            "SkyWatch-AstroDestination/1.0",
        )

    @patch("src.px_fetcher.urlopen")
    def test_empty_response(self, mock_urlopen):
        """Reject responses containing no dataset content."""
        response = MagicMock()
        response.status = 200
        response.read.return_value = b""

        mock_urlopen.return_value.__enter__.return_value = response

        with self.assertRaisesRegex(PXFetchError, "empty"):
            fetch_px()

    @patch("src.px_fetcher.urlopen")
    def test_unexpected_http_status(self, mock_urlopen):
        """Reject an unexpected HTTP response status."""
        response = MagicMock()
        response.status = 302
        response.read.return_value = b"Unexpected response"

        mock_urlopen.return_value.__enter__.return_value = response

        with self.assertRaisesRegex(PXFetchError, "302"):
            fetch_px()

    @patch("src.px_fetcher.urlopen")
    def test_http_error(self, mock_urlopen):
        """Convert HTTP errors into PXFetchError."""
        mock_urlopen.side_effect = HTTPError(
            url=DATASET_URL,
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )

        with self.assertRaisesRegex(PXFetchError, "404"):
            fetch_px()

    @patch("src.px_fetcher.urlopen")
    def test_network_error(self, mock_urlopen):
        """Convert connection errors into PXFetchError."""
        mock_urlopen.side_effect = URLError(
            "Connection refused"
        )

        with self.assertRaisesRegex(
            PXFetchError, "Failed to download"
        ):
            fetch_px()

    @patch("src.px_fetcher.urlopen")
    def test_timeout(self, mock_urlopen):
        """Handle network timeouts gracefully."""
        mock_urlopen.side_effect = TimeoutError(
            "Connection timed out"
        )

        with self.assertRaises(PXFetchError):
            fetch_px()


if __name__ == "__main__":
    unittest.main()
