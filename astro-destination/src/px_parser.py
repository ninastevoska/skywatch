
"""Parse PC-Axis datasets into structured tabular data."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
from pyaxis import pyaxis


PX_ENCODING = "windows-1250"


class PXParseError(Exception):
    """Raised when a PC-Axis dataset cannot be parsed."""


def parse_px(content: bytes) -> tuple[pd.DataFrame, dict]:
    """Parse downloaded PC-Axis content.

    Args:
        content: Raw PC-Axis content returned by the fetcher.

    Returns:
        A tuple containing the parsed DataFrame and metadata.

    Raises:
        PXParseError: If the input is empty, invalid, or cannot
            be parsed as a PC-Axis dataset.
    """
    if not content:
        raise PXParseError("Cannot parse an empty PC-Axis dataset.")

    try:
        with TemporaryDirectory() as temporary_directory:
            file_path = Path(temporary_directory) / "dataset.px"
            file_path.write_bytes(content)

            result = pyaxis.parse(
                str(file_path),
                encoding=PX_ENCODING,
                lang="sl",
            )

        data = result["DATA"]
        metadata = result["METADATA"]

        if not isinstance(data, pd.DataFrame):
            raise PXParseError(
                "The parser did not return a valid DataFrame."
            )

        if not isinstance(metadata, dict):
            raise PXParseError(
                "The parser did not return valid metadata."
            )

        return data, metadata

    except PXParseError:
        raise

    except Exception as exc:
        raise PXParseError(
            f"Failed to parse the PC-Axis dataset: {exc}"
        ) from exc
