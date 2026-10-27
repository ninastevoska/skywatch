"""Unit tests for parsing PC-Axis tourism datasets."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.px_parser import PXParseError, parse_px


class TestPXParser(unittest.TestCase):
    """Verify PC-Axis parsing, encoding, and error handling."""

    def setUp(self):
        """Prepare sample data returned by the mocked parser."""
        self.content = (
            b'CHARSET="ANSI";\n'
            b'CODEPAGE="windows-1250";\n'
            b'DATA=100 200;'
        )

        self.data = pd.DataFrame({
            "MESEC": ["2026M01", "2026M02"],
            "OBČINE": ["Bohinj", "Bohinj"],
            "DRŽAVA": ["0 Država - SKUPAJ"] * 2,
            "MERITVE": ["Prenočitve turistov"] * 2,
            "DATA": ["100", "200"],
        })

        self.metadata = {
            "TITLE": "Tourist overnight stays",
        }

    @patch("src.px_parser.pyaxis.parse")
    def test_successful_parsing(self, mock_parse):
        """Return the parsed DataFrame and metadata."""
        mock_parse.return_value = {
            "DATA": self.data,
            "METADATA": self.metadata,
        }

        data, metadata = parse_px(self.content)

        pd.testing.assert_frame_equal(data, self.data)
        self.assertEqual(metadata, self.metadata)
        mock_parse.assert_called_once()

    @patch("src.px_parser.pyaxis.parse")
    def test_windows_1250_encoding(self, mock_parse):
        """Use the encoding required by the SURS dataset."""
        mock_parse.return_value = {
            "DATA": self.data,
            "METADATA": self.metadata,
        }

        parse_px(self.content)

        args, kwargs = mock_parse.call_args

        self.assertEqual(kwargs["encoding"], "windows-1250")
        self.assertEqual(kwargs["lang"], "sl")
        self.assertTrue(args[0].endswith(".px"))

    @patch("src.px_parser.pyaxis.parse")
    def test_temporary_file_contains_original_bytes(self, mock_parse):
        """Pass the original dataset bytes to the parser."""
        observed_content = []

        def inspect_file(path, **kwargs):
            observed_content.append(Path(path).read_bytes())

            return {
                "DATA": self.data,
                "METADATA": self.metadata,
            }

        mock_parse.side_effect = inspect_file

        parse_px(self.content)

        self.assertEqual(observed_content, [self.content])

    @patch("src.px_parser.pyaxis.parse")
    def test_temporary_file_is_removed(self, mock_parse):
        """Remove the temporary dataset file after parsing."""
        paths = []

        def record_path(path, **kwargs):
            paths.append(Path(path))

            return {
                "DATA": self.data,
                "METADATA": self.metadata,
            }

        mock_parse.side_effect = record_path

        parse_px(self.content)

        self.assertEqual(len(paths), 1)
        self.assertFalse(paths[0].exists())

    @patch("src.px_parser.pyaxis.parse")
    def test_parser_failure(self, mock_parse):
        """Convert third-party parser errors into PXParseError."""
        mock_parse.side_effect = ValueError(
            "Invalid PC-Axis content"
        )

        with self.assertRaises(PXParseError):
            parse_px(self.content)

    @patch("src.px_parser.pyaxis.parse")
    def test_temporary_file_removed_after_failure(self, mock_parse):
        """Clean up temporary files even when parsing fails."""
        paths = []

        def fail_parsing(path, **kwargs):
            paths.append(Path(path))
            raise ValueError("Invalid PC-Axis content")

        mock_parse.side_effect = fail_parsing

        with self.assertRaises(PXParseError):
            parse_px(self.content)

        self.assertEqual(len(paths), 1)
        self.assertFalse(paths[0].exists())


if __name__ == "__main__":
    unittest.main()
